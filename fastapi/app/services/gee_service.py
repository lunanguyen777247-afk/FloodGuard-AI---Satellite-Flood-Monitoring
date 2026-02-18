import ee
import json
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import logging
from app.core.config import get_settings
import hashlib
import time
import os
import json

logger = logging.getLogger(__name__)


class GEEService:
    """Service for interacting with Google Earth Engine"""
    
    def __init__(self):
        self.settings = get_settings()
        self._initialize_gee()
    
    def _initialize_gee(self):
        """Initialize Google Earth Engine with service account"""
        try:
            credentials = ee.ServiceAccountCredentials(
                self.settings.GEE_SERVICE_ACCOUNT,
                self.settings.GEE_PRIVATE_KEY_PATH
            )
            ee.Initialize(credentials)
            logger.info("Google Earth Engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GEE: {e}")
            raise
    
    def get_region_geometry(self, region_name: str) -> ee.Geometry:
        """
        Get geometry for a Vietnamese province/region
        
        Args:
            region_name: Name of the province (e.g., "Quảng Trị")
            
        Returns:
            ee.Geometry: Region geometry
        """
        try:
            # Load Vietnam administrative boundaries
            vietnam = ee.FeatureCollection("FAO/GAUL/2015/level1").filter(
                ee.Filter.eq('ADM0_NAME', 'Viet Nam')
            )
            
            # Filter by province name
            region = vietnam.filter(ee.Filter.eq('ADM1_NAME', region_name)).first()
            
            if region:
                return region.geometry()
            else:
                logger.warning(f"Region {region_name} not found, using default bbox")
                # Return default bbox for central Vietnam if not found
                return ee.Geometry.Rectangle([106.0, 16.0, 108.0, 17.5])
                
        except Exception as e:
            logger.error(f"Error getting region geometry: {e}")
            raise
    
    def get_sentinel1_flood_mask(
        self,
        region: ee.Geometry,
        start_date: str,
        end_date: str,
        threshold: float = -15.0
    ) -> ee.Image:
        """
        Generate flood mask from Sentinel-1 SAR data
        
        Args:
            region: Region geometry
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            threshold: VV threshold for water detection (dB)
            
        Returns:
            ee.Image: Binary flood mask
        """
        try:
            # Get Sentinel-1 GRD collection
            s1 = ee.ImageCollection('COPERNICUS/S1_GRD') \
                .filterBounds(region) \
                .filterDate(start_date, end_date) \
                .filter(ee.Filter.eq('instrumentMode', 'IW')) \
                .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
                .select('VV')
            
            # Create median composite
            s1_composite = s1.median().clip(region)
            
            # Apply water detection threshold
            water_mask = s1_composite.lt(threshold).rename('water')
            
            # Apply morphological operations to reduce noise
            water_mask = water_mask.focal_median(30, 'circle', 'meters')
            
            return water_mask
            
        except Exception as e:
            logger.error(f"Error generating flood mask: {e}")
            raise
    
    def get_rainfall_data(
        self,
        region: ee.Geometry,
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Get rainfall data from GPM/TRMM
        
        Args:
            region: Region geometry
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Dict: Rainfall statistics
        """
        try:
            # Use GPM IMERG dataset
            gpm = ee.ImageCollection('NASA/GPM_L3/IMERG_V06') \
                .filterBounds(region) \
                .filterDate(start_date, end_date) \
                .select('precipitation')
            
            # Calculate total rainfall
            total_rainfall = gpm.sum().clip(region)
            
            # Get statistics
            stats = total_rainfall.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.max(), '', True
                ).combine(
                    ee.Reducer.sum(), '', True
                ),
                geometry=region,
                scale=10000,
                maxPixels=1e9
            )
            
            return stats.getInfo()
            
        except Exception as e:
            logger.error(f"Error getting rainfall data: {e}")
            raise
    
    def get_dem_data(self, region: ee.Geometry) -> ee.Image:
        """
        Get Digital Elevation Model data
        
        Args:
            region: Region geometry
            
        Returns:
            ee.Image: DEM image
        """
        try:
            # Use SRTM DEM
            dem = ee.Image('USGS/SRTMGL1_003').clip(region)
            
            # Calculate slope
            slope = ee.Terrain.slope(dem)
            
            return dem.addBands(slope.rename('slope'))
            
        except Exception as e:
            logger.error(f"Error getting DEM data: {e}")
            raise
    
    def calculate_flood_statistics(
        self,
        region: ee.Geometry,
        flood_mask: ee.Image
    ) -> Dict:
        """
        Calculate flood statistics for a region
        
        Args:
            region: Region geometry
            flood_mask: Binary flood mask
            
        Returns:
            Dict: Flood statistics
        """
        try:
            # Calculate flood area
            pixel_area = ee.Image.pixelArea()
            flood_area = flood_mask.multiply(pixel_area).divide(1e6)  # Convert to km²
            
            # Get statistics
            stats = flood_area.reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=region,
                scale=30,
                maxPixels=1e9
            )
            
            # Get region area for percentage calculation
            region_area = region.area().divide(1e6).getInfo()  # km²
            flood_area_km2 = stats.getInfo().get('water', 0)
            
            return {
                'flood_area_km2': flood_area_km2,
                'region_area_km2': region_area,
                'flood_percentage': (flood_area_km2 / region_area * 100) if region_area > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating flood statistics: {e}")
            raise
    
    def generate_flood_map(
        self,
        region_name: str,
        start_date: str,
        end_date: str,
        export_format: str = "png"
    ) -> Dict:
        """
        Generate complete flood analysis map
        
        Args:
            region_name: Name of the region
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            export_format: Output format (png, geojson, tiff)
            
        Returns:
            Dict: Map data and statistics
        """
        try:
            # Get region geometry
            region = self.get_region_geometry(region_name)

            # Build cache key from region + dates + vis params
            key_raw = f"{region_name}|{start_date}|{end_date}|png|0|1|white,blue"
            key = hashlib.sha1(key_raw.encode('utf-8')).hexdigest()
            cache_dir = getattr(self.settings, 'TILES_CACHE_DIR', './cache/tiles')
            os.makedirs(cache_dir, exist_ok=True)
            cache_file = os.path.join(cache_dir, f"{key}.json")

            # Check cache TTL
            ttl = getattr(self.settings, 'CACHE_TTL', 3600)
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r') as fh:
                        cached = json.load(fh)
                    if time.time() - cached.get('ts', 0) < ttl:
                        return cached.get('result')
                except Exception:
                    pass

            # Generate flood mask
            flood_mask = self.get_sentinel1_flood_mask(region, start_date, end_date)

            # Get DEM
            dem = self.get_dem_data(region)

            # Get rainfall data
            rainfall_stats = self.get_rainfall_data(region, start_date, end_date)

            # Calculate flood statistics
            flood_stats = self.calculate_flood_statistics(region, flood_mask)

            # Generate map URL
            map_id = flood_mask.getMapId({
                'min': 0,
                'max': 1,
                'palette': ['white', 'blue']
            })

            result = {
                'region': region_name,
                'date_range': {'start': start_date, 'end': end_date},
                'flood_statistics': flood_stats,
                'rainfall_statistics': rainfall_stats,
                'map_url': map_id.get('tile_fetcher').url_format,
                'map_id': map_id.get('mapid')
            }

            try:
                with open(cache_file, 'w') as fh:
                    json.dump({'ts': time.time(), 'result': result}, fh)
            except Exception:
                pass

            return result
            
        except Exception as e:
            logger.error(f"Error generating flood map: {e}")
            raise
    
    def export_to_geojson(
        self,
        region: ee.Geometry,
        flood_mask: ee.Image
    ) -> Dict:
        """
        Export flood mask as GeoJSON
        
        Args:
            region: Region geometry
            flood_mask: Binary flood mask
            
        Returns:
            Dict: GeoJSON FeatureCollection
        """
        try:
            # Vectorize flood mask but limit and simplify to avoid huge payloads
            vectors = flood_mask.selfMask().reduceToVectors(
                geometry=region,
                scale=30,
                geometryType='polygon',
                eightConnected=False,
                maxPixels=1e9
            )

            fc = ee.FeatureCollection(vectors)
            # simplify geometries to reduce size
            fc_simpl = fc.map(lambda f: f.simplify(30))

            # Export to Google Drive asynchronously and return task info
            file_prefix = f"flood_geo_{int(time.time())}"
            drive_folder = getattr(self.settings, 'TILES_CACHE_DIR', 'GEE_Exports')

            try:
                task = ee.batch.Export.table.toDrive(
                    collection=fc_simpl,
                    description=f"export_{file_prefix}",
                    folder=drive_folder,
                    fileNamePrefix=file_prefix,
                    fileFormat='GeoJSON'
                )
                task.start()
                return {
                    'export_task_id': task.id,
                    'drive_folder': drive_folder,
                    'fileNamePrefix': file_prefix,
                    'message': 'Export started; check Tasks in GEE or Drive for completion.'
                }
            except Exception:
                # fallback: try small getInfo() but with try/except
                try:
                    geojson = fc_simpl.getInfo()
                    return geojson
                except Exception as e:
                    raise
            
        except Exception as e:
            logger.error(f"Error exporting to GeoJSON: {e}")
            raise

    def aggregate_admin_summary(
        self,
        country_name: str,
        start_date: str,
        end_date: str,
        scale: int = 100
    ) -> List[Dict]:
        """
        Aggregate flood statistics per ADM1 for a country.

        Returns a list of summaries with fields similar to RegionData.
        """
        try:
            adm1 = ee.FeatureCollection("FAO/GAUL/2015/level1").filter(
                ee.Filter.eq('ADM0_NAME', country_name)
            )

            # Build flood composite for full country period
            s1 = ee.ImageCollection('COPERNICUS/S1_GRD') \
                .filterDate(start_date, end_date) \
                .filter(ee.Filter.eq('instrumentMode', 'IW')) \
                .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
                .select('VV')

            s1_composite = s1.median()

            # water mask
            water_mask = s1_composite.lt(-15).rename('water')

            pixel_area = ee.Image.pixelArea()
            flooded = water_mask.multiply(pixel_area)

            reduced = flooded.reduceRegions(collection=adm1, reducer=ee.Reducer.sum(), scale=scale, maxPixels=1e9)

            features = reduced.getInfo().get('features', [])

            dem = ee.Image('USGS/SRTMGL1_003')

            summary = []
            for f in features:
                props = f.get('properties', {})
                name = props.get('ADM1_NAME') or props.get('NAME_1') or 'Unknown'
                flooded_m2 = props.get('sum') or 0
                flooded_ha = flooded_m2 / 10000.0

                geom = f.get('geometry')
                try:
                    feat = ee.Feature(ee.Geometry(geom))
                    total_m2 = feat.geometry().area().getInfo()
                except Exception:
                    total_m2 = 1

                total_ha = total_m2 / 10000.0 if total_m2 else 1
                pct = (flooded_ha / total_ha * 100) if total_ha > 0 else 0

                if pct > 20:
                    severity = 'Critical'
                elif pct > 10:
                    severity = 'High'
                elif pct > 2:
                    severity = 'Medium'
                else:
                    severity = 'Low'

                # population estimate inside flooded area
                try:
                    pop = ee.ImageCollection('WorldPop/GP/100m/pop').first().multiply(water_mask)
                    pop_stats = pop.reduceRegion(reducer=ee.Reducer.sum(), geometry=ee.Geometry(geom), scale=100, maxPixels=1e9)
                    affected_pop = int(pop_stats.getInfo().get('population', 0))
                except Exception:
                    affected_pop = int(flooded_ha * 10)

                est_loss = flooded_ha * 0.005  # default billion per ha

                # depth proxy using DEM
                avg_depth = 0.0
                try:
                    flooded_mask_img = water_mask.updateMask(water_mask).clip(ee.Geometry(geom))
                    flooded_dem_mean = dem.updateMask(flooded_mask_img).reduceRegion(ee.Reducer.mean(), geometry=ee.Geometry(geom), scale=scale, maxPixels=1e9).get('elevation')
                    surrounding_median = dem.updateMask(flooded_mask_img.Not()).reduceRegion(ee.Reducer.median(), geometry=ee.Geometry(geom), scale=scale, maxPixels=1e9).get('elevation')
                    fm = flooded_dem_mean.getInfo() if flooded_dem_mean is not None else None
                    sm = surrounding_median.getInfo() if surrounding_median is not None else None
                    if fm is not None and sm is not None:
                        d = sm - fm
                        avg_depth = round(d if d > 0 else 0.0, 2)
                except Exception:
                    avg_depth = 0.0

                summary.append({
                    'name': name,
                    'flooded_area_ha': round(flooded_ha, 2),
                    'flooded_pct': round(pct, 2),
                    'severity': severity,
                    'avgDepth_m': avg_depth,
                    'estimated_loss_billion_vnd': round(est_loss, 3),
                    'affected_population': affected_pop,
                })

            return summary

        except Exception as e:
            logger.error(f'Error aggregating admin summary: {e}')
            raise
    
    def get_population_data(self, region: ee.Geometry) -> Dict:
        """
        Get population data for affected areas
        
        Args:
            region: Region geometry
            
        Returns:
            Dict: Population statistics
        """
        try:
            # Use WorldPop dataset
            population = ee.ImageCollection('WorldPop/GP/100m/pop') \
                .filterBounds(region) \
                .sort('system:time_start', False) \
                .first() \
                .clip(region)
            
            # Get statistics
            stats = population.reduceRegion(
                reducer=ee.Reducer.sum().combine(
                    ee.Reducer.mean(), '', True
                ),
                geometry=region,
                scale=100,
                maxPixels=1e9
            )
            
            return stats.getInfo()
            
        except Exception as e:
            logger.error(f"Error getting population data: {e}")
            raise
    
    def estimate_affected_population(
        self,
        region: ee.Geometry,
        flood_mask: ee.Image
    ) -> int:
        """
        Estimate population affected by flooding
        
        Args:
            region: Region geometry
            flood_mask: Binary flood mask
            
        Returns:
            int: Estimated affected population
        """
        try:
            # Get population data
            population = ee.ImageCollection('WorldPop/GP/100m/pop') \
                .filterBounds(region) \
                .sort('system:time_start', False) \
                .first() \
                .clip(region)
            
            # Calculate affected population
            affected_pop = population.multiply(flood_mask)
            
            stats = affected_pop.reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=region,
                scale=100,
                maxPixels=1e9
            )
            
            return int(stats.getInfo().get('population', 0))
            
        except Exception as e:
            logger.error(f"Error estimating affected population: {e}")
            return 0


# Create singleton instance
gee_service = GEEService()
