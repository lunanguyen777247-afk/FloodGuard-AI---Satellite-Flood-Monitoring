from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date


class WeatherBase(BaseModel):
    """Base weather data model"""
    date: date = Field(..., description="Date of weather record")
    rainfall: float = Field(..., ge=0, description="Rainfall in mm")
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Humidity percentage")
    wind_speed: Optional[float] = Field(None, ge=0, description="Wind speed in km/h")
    pressure: Optional[float] = Field(None, description="Atmospheric pressure in hPa")


class WeatherCreate(WeatherBase):
    """Schema for creating weather record"""
    region_id: str = Field(..., description="Associated region ID")


class Weather(WeatherBase):
    """Full weather model"""
    id: str = Field(..., description="Unique weather record ID")
    region_id: str = Field(..., description="Associated region ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "w1",
                "region_id": "1",
                "date": "2024-01-15",
                "rainfall": 120.5,
                "temperature": 24.5,
                "humidity": 85.0,
                "wind_speed": 15.2,
                "pressure": 1010.5,
                "created_at": "2024-01-15T08:00:00"
            }
        }


class WeatherQuery(BaseModel):
    """Query parameters for weather data"""
    region_id: Optional[str] = Field(None, description="Filter by region ID")
    from_date: Optional[date] = Field(None, description="Start date (YYYY-MM-DD)")
    to_date: Optional[date] = Field(None, description="End date (YYYY-MM-DD)")
    
    @validator('to_date')
    def validate_date_range(cls, v, values):
        if v and 'from_date' in values and values['from_date']:
            if v < values['from_date']:
                raise ValueError('to_date must be after from_date')
        return v


class WeatherResponse(BaseModel):
    """Response model for weather data"""
    total: int = Field(..., description="Total number of records")
    weather_data: List[Weather] = Field(..., description="List of weather records")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 7,
                "weather_data": [
                    {
                        "id": "w1",
                        "region_id": "1",
                        "date": "2024-01-15",
                        "rainfall": 120.5,
                        "temperature": 24.5,
                        "humidity": 85.0,
                        "wind_speed": 15.2,
                        "pressure": 1010.5,
                        "created_at": "2024-01-15T08:00:00"
                    }
                ]
            }
        }


class WeatherForecast(BaseModel):
    """Weather forecast model"""
    region_id: str = Field(..., description="Region ID")
    forecast_date: date = Field(..., description="Forecast date")
    predicted_rainfall: float = Field(..., ge=0, description="Predicted rainfall in mm")
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence (0-1)")
    risk_level: str = Field(..., description="Flood risk level")
    
    class Config:
        json_schema_extra = {
            "example": {
                "region_id": "1",
                "forecast_date": "2024-01-16",
                "predicted_rainfall": 85.5,
                "confidence": 0.87,
                "risk_level": "Moderate"
            }
        }


class WeatherStatistics(BaseModel):
    """Weather statistics for a region/period"""
    region_id: str = Field(..., description="Region ID")
    period_start: date = Field(..., description="Period start date")
    period_end: date = Field(..., description="Period end date")
    total_rainfall: float = Field(..., description="Total rainfall in mm")
    avg_temperature: float = Field(..., description="Average temperature")
    max_rainfall_day: date = Field(..., description="Day with maximum rainfall")
    max_rainfall_amount: float = Field(..., description="Maximum daily rainfall")
    rainy_days: int = Field(..., description="Number of rainy days")
    
    class Config:
        json_schema_extra = {
            "example": {
                "region_id": "1",
                "period_start": "2024-01-01",
                "period_end": "2024-01-15",
                "total_rainfall": 450.5,
                "avg_temperature": 23.8,
                "max_rainfall_day": "2024-01-10",
                "max_rainfall_amount": 180.5,
                "rainy_days": 12
            }
        }


class SatelliteWeatherData(BaseModel):
    """Satellite-based weather data (GPM/TRMM)"""
    region_id: str = Field(..., description="Region ID")
    date: date = Field(..., description="Date of satellite pass")
    satellite_source: str = Field(..., description="Satellite source (GPM/TRMM)")
    rainfall_estimate: float = Field(..., ge=0, description="Rainfall estimate in mm")
    coverage_quality: float = Field(..., ge=0, le=1, description="Data quality (0-1)")
    data_url: Optional[str] = Field(None, description="URL to raw data")
