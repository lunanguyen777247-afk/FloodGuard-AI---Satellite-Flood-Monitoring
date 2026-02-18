from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    """Flood severity levels"""
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    CRITICAL = "Critical"


class RegionBase(BaseModel):
    """Base region model"""
    name: str = Field(..., description="Region name (province/city)")
    submerged_area: float = Field(..., ge=0, description="Submerged area in km²")
    rainfall: float = Field(..., ge=0, description="Total rainfall in mm")
    avg_depth: float = Field(..., ge=0, description="Average flood depth in meters")
    severity: SeverityLevel = Field(..., description="Flood severity level")
    affected_population: int = Field(..., ge=0, description="Number of affected people")
    estimated_loss: float = Field(..., ge=0, description="Estimated loss in million VND")


class RegionCreate(RegionBase):
    """Schema for creating a new region record"""
    pass


class RegionUpdate(BaseModel):
    """Schema for updating region data"""
    submerged_area: Optional[float] = Field(None, ge=0)
    rainfall: Optional[float] = Field(None, ge=0)
    avg_depth: Optional[float] = Field(None, ge=0)
    severity: Optional[SeverityLevel] = None
    affected_population: Optional[int] = Field(None, ge=0)
    estimated_loss: Optional[float] = Field(None, ge=0)


class Region(RegionBase):
    """Full region model with metadata"""
    id: str = Field(..., description="Unique region identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "1",
                "name": "Quảng Trị",
                "submerged_area": 450.5,
                "rainfall": 320.0,
                "avg_depth": 1.2,
                "severity": "High",
                "affected_population": 12500,
                "estimated_loss": 125.5,
                "created_at": "2024-01-15T08:00:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }


class RegionDetail(Region):
    """Detailed region information with geographic data"""
    latitude: float = Field(..., description="Center latitude")
    longitude: float = Field(..., description="Center longitude")
    bbox: List[float] = Field(..., description="Bounding box [minLon, minLat, maxLon, maxLat]")
    geometry: Optional[dict] = Field(None, description="GeoJSON geometry")
    
    @validator('bbox')
    def validate_bbox(cls, v):
        if len(v) != 4:
            raise ValueError('Bounding box must have 4 coordinates')
        return v


class RegionListResponse(BaseModel):
    """Response model for list of regions"""
    total: int = Field(..., description="Total number of regions")
    regions: List[Region] = Field(..., description="List of regions")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "timestamp": "2024-01-15T10:30:00",
                "regions": [
                    {
                        "id": "1",
                        "name": "Quảng Trị",
                        "submerged_area": 450.5,
                        "rainfall": 320.0,
                        "avg_depth": 1.2,
                        "severity": "High",
                        "affected_population": 12500,
                        "estimated_loss": 125.5,
                        "created_at": "2024-01-15T08:00:00",
                        "updated_at": "2024-01-15T10:30:00"
                    }
                ]
            }
        }


class FloodStatistics(BaseModel):
    """Overall flood statistics"""
    total_submerged_area: float = Field(..., description="Total submerged area in km²")
    total_affected_population: int = Field(..., description="Total affected people")
    total_estimated_loss: float = Field(..., description="Total loss in million VND")
    high_risk_regions: int = Field(..., description="Number of high-risk regions")
    critical_regions: int = Field(..., description="Number of critical regions")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class AdminSummaryItem(BaseModel):
    name: str
    flooded_area_ha: float
    flooded_pct: float
    severity: str
    avgDepth_m: float = 0.0
    estimated_loss_billion_vnd: float = 0.0
    affected_population: int = 0


class AdminSummaryResponse(BaseModel):
    country: str
    date_range: dict
    admin_summary: List[AdminSummaryItem]


class GeoJSONResponse(BaseModel):
    type: str
    features: List[dict]
