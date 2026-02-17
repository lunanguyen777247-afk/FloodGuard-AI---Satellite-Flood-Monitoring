import ee
import json
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import logging
from app.core.config import get_settings

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
            
            return {
                'region': region_name,
                'date_range': {'start': start_date, 'end': end_date},
                'flood_statistics': flood_stats,
                'rainfall_statistics': rainfall_stats,
                'map_url': map_id.get('tile_fetcher').url_format,
                'map_id': map_id.get('mapid')
            }
            
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
            # Vectorize flood mask
            vectors = flood_mask.reduceToVectors(
                geometry=region,
                scale=30,
                geometryType='polygon',
                eightConnected=False,
                maxPixels=1e9
            )
            
            # Convert to GeoJSON
            geojson = vectors.getInfo()
            
            return geojson
            
        except Exception as e:
            logger.error(f"Error exporting to GeoJSON: {e}")
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
