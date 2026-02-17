from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import date, datetime, timedelta
import logging

from app.models.region import (
    Region, RegionDetail, RegionListResponse, 
    FloodStatistics, SeverityLevel
)
from app.services.gee_service import gee_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/regions", tags=["regions"])


@router.get("/", response_model=RegionListResponse)
async def get_regions(
    date_filter: Optional[date] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    severity: Optional[SeverityLevel] = Query(None, description="Filter by severity level"),
    min_area: Optional[float] = Query(None, ge=0, description="Minimum submerged area (km²)")
):
    """
    Get list of all monitored regions with flood data
    
    - **date_filter**: Optional date to get historical data
    - **severity**: Filter by severity level (Low/Moderate/High/Critical)
    - **min_area**: Minimum submerged area to include
    """
    try:
        # In production, this would query from database
        # For now, we'll generate data using GEE service
        
        vietnam_provinces = [
            "Quảng Trị", "Thừa Thiên Huế", "Quảng Bình",
            "Hà Tĩnh", "Nghệ An", "Thanh Hóa"
        ]
        
        regions = []
        target_date = date_filter or date.today()
        
        for i, province in enumerate(vietnam_provinces, 1):
            try:
                # Get flood data from GEE
                region_geom = gee_service.get_region_geometry(province)
                
                # Calculate date range (7 days before target date)
                end_date = target_date.isoformat()
                start_date = (target_date - timedelta(days=7)).isoformat()
                
                # Get flood mask
                flood_mask = gee_service.get_sentinel1_flood_mask(
                    region_geom, start_date, end_date
                )
                
                # Calculate statistics
                flood_stats = gee_service.calculate_flood_statistics(region_geom, flood_mask)
                
                # Get rainfall data
                rainfall_stats = gee_service.get_rainfall_data(
                    region_geom, start_date, end_date
                )
                
                # Estimate affected population
                affected_pop = gee_service.estimate_affected_population(
                    region_geom, flood_mask
                )
                
                # Determine severity based on flood area
                flood_area = flood_stats.get('flood_area_km2', 0)
                if flood_area > 500:
                    severity_level = SeverityLevel.CRITICAL
                elif flood_area > 300:
                    severity_level = SeverityLevel.HIGH
                elif flood_area > 100:
                    severity_level = SeverityLevel.MODERATE
                else:
                    severity_level = SeverityLevel.LOW
                
                # Estimate loss (simplified calculation)
                estimated_loss = flood_area * 0.5 + affected_pop * 0.01
                
                region = Region(
                    id=str(i),
                    name=province,
                    submerged_area=flood_area,
                    rainfall=rainfall_stats.get('precipitation_mean', 0) * 100,  # Convert to mm
                    avg_depth=1.5 if flood_area > 100 else 0.8,
                    severity=severity_level,
                    affected_population=affected_pop,
                    estimated_loss=estimated_loss,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                # Apply filters
                if severity and region.severity != severity:
                    continue
                if min_area and region.submerged_area < min_area:
                    continue
                
                regions.append(region)
                
            except Exception as e:
                logger.error(f"Error processing region {province}: {e}")
                continue
        
        return RegionListResponse(
            total=len(regions),
            regions=regions,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting regions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get regions: {str(e)}")


@router.get("/{region_id}", response_model=RegionDetail)
async def get_region_detail(region_id: str):
    """
    Get detailed information for a specific region
    
    - **region_id**: Unique region identifier
    """
    try:
        # Get all regions and find the requested one
        response = await get_regions()
        
        region = next((r for r in response.regions if r.id == region_id), None)
        if not region:
            raise HTTPException(status_code=404, detail=f"Region {region_id} not found")
        
        # Get geometry data
        region_geom = gee_service.get_region_geometry(region.name)
        bounds = region_geom.bounds().getInfo()['coordinates'][0]
        
        # Calculate bbox
        lons = [p[0] for p in bounds]
        lats = [p[1] for p in bounds]
        bbox = [min(lons), min(lats), max(lons), max(lats)]
        
        # Calculate center
        center_lon = sum(lons) / len(lons)
        center_lat = sum(lats) / len(lats)
        
        # Create detailed response
        detail = RegionDetail(
            **region.dict(),
            latitude=center_lat,
            longitude=center_lon,
            bbox=bbox,
            geometry={
                "type": "Polygon",
                "coordinates": [bounds]
            }
        )
        
        return detail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting region detail: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get region detail: {str(e)}")


@router.get("/statistics/summary", response_model=FloodStatistics)
async def get_flood_statistics():
    """
    Get overall flood statistics across all regions
    """
    try:
        response = await get_regions()
        
        total_submerged = sum(r.submerged_area for r in response.regions)
        total_affected = sum(r.affected_population for r in response.regions)
        total_loss = sum(r.estimated_loss for r in response.regions)
        
        high_risk = sum(1 for r in response.regions if r.severity in [SeverityLevel.HIGH, SeverityLevel.VERY_HIGH])
        critical = sum(1 for r in response.regions if r.severity == SeverityLevel.CRITICAL)
        
        return FloodStatistics(
            total_submerged_area=total_submerged,
            total_affected_population=total_affected,
            total_estimated_loss=total_loss,
            high_risk_regions=high_risk,
            critical_regions=critical,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.post("/refresh")
async def refresh_region_data():
    """
    Manually trigger refresh of region data from satellite sources
    
    This endpoint initiates a background task to update all region data
    """
    try:
        # In production, this would trigger a background task
        logger.info("Region data refresh initiated")
        
        return {
            "success": True,
            "message": "Region data refresh initiated",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh data: {str(e)}")
