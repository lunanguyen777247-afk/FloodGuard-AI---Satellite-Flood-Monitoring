from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import date, datetime, timedelta
import logging

from app.models.weather import (
    Weather, WeatherResponse, WeatherQuery,
    WeatherStatistics, SatelliteWeatherData
)
from app.services.gee_service import gee_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/", response_model=WeatherResponse)
async def get_weather_data(
    region_id: Optional[str] = Query(None, description="Filter by region ID"),
    from_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get weather data for regions
    
    - **region_id**: Optional region ID to filter
    - **from_date**: Start date for data range
    - **to_date**: End date for data range
    """
    try:
        # Set default date range if not provided
        if not to_date:
            to_date = date.today()
        if not from_date:
            from_date = to_date - timedelta(days=7)
        
        # Validate date range
        if from_date > to_date:
            raise HTTPException(
                status_code=400,
                detail="from_date must be before to_date"
            )
        
        weather_data = []
        current_date = from_date
        
        # Generate weather data for date range
        while current_date <= to_date:
            # In production, fetch from weather API or database
            # For now, generate sample data
            weather = Weather(
                id=f"w_{current_date.strftime('%Y%m%d')}",
                region_id=region_id or "1",
                date=current_date,
                rainfall=120.5,  # Would be real data
                temperature=24.5,
                humidity=85.0,
                wind_speed=15.2,
                pressure=1010.5,
                created_at=datetime.utcnow()
            )
            weather_data.append(weather)
            current_date += timedelta(days=1)
        
        return WeatherResponse(
            total=len(weather_data),
            weather_data=weather_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting weather data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get weather data: {str(e)}"
        )


@router.get("/statistics", response_model=WeatherStatistics)
async def get_weather_statistics(
    region_id: str = Query(..., description="Region ID"),
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date")
):
    """
    Get weather statistics for a specific region and period
    """
    try:
        # Get weather data
        response = await get_weather_data(region_id, from_date, to_date)
        
        if not response.weather_data:
            raise HTTPException(
                status_code=404,
                detail="No weather data found for specified period"
            )
        
        # Calculate statistics
        total_rainfall = sum(w.rainfall for w in response.weather_data)
        avg_temperature = sum(w.temperature for w in response.weather_data) / len(response.weather_data)
        
        max_rainfall_day = max(response.weather_data, key=lambda w: w.rainfall)
        rainy_days = sum(1 for w in response.weather_data if w.rainfall > 1.0)
        
        return WeatherStatistics(
            region_id=region_id,
            period_start=from_date,
            period_end=to_date,
            total_rainfall=total_rainfall,
            avg_temperature=avg_temperature,
            max_rainfall_day=max_rainfall_day.date,
            max_rainfall_amount=max_rainfall_day.rainfall,
            rainy_days=rainy_days
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating weather statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate statistics: {str(e)}"
        )


@router.get("/satellite", response_model=SatelliteWeatherData)
async def get_satellite_weather(
    region_id: str = Query(..., description="Region ID"),
    date_param: date = Query(..., alias="date", description="Date for satellite data")
):
    """
    Get satellite-based weather data (GPM/TRMM)
    """
    try:
        # In production, fetch from GEE
        return SatelliteWeatherData(
            region_id=region_id,
            date=date_param,
            satellite_source="GPM IMERG",
            rainfall_estimate=145.2,
            coverage_quality=0.92,
            data_url=None
        )
        
    except Exception as e:
        logger.error(f"Error getting satellite weather: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get satellite data: {str(e)}"
        )
