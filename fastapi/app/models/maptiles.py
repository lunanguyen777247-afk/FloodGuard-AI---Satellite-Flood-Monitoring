from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import date, datetime
from enum import Enum


class MapLayer(str, Enum):
    """Available map layers"""
    SAR = "sar"  # Sentinel-1 SAR
    OPTICAL = "optical"  # Sentinel-2 Optical
    RAINFALL = "rainfall"  # GPM/TRMM Rainfall
    DEM = "dem"  # Digital Elevation Model
    FLOOD_MASK = "flood_mask"  # Flood water mask
    POPULATION = "population"  # Population density
    INFRASTRUCTURE = "infrastructure"  # Critical infrastructure


class TileFormat(str, Enum):
    """Tile output formats"""
    PNG = "png"
    JPEG = "jpeg"
    TIFF = "tiff"
    GEOJSON = "geojson"


class TileRequest(BaseModel):
    """Request model for map tiles"""
    layer: MapLayer = Field(..., description="Map layer to fetch")
    bbox: List[float] = Field(..., description="Bounding box [minLon, minLat, maxLon, maxLat]")
    date: Optional[date] = Field(None, description="Date for time-series data")
    format: TileFormat = Field(default=TileFormat.PNG, description="Output format")
    width: Optional[int] = Field(512, ge=256, le=2048, description="Image width in pixels")
    height: Optional[int] = Field(512, ge=256, le=2048, description="Image height in pixels")
    
    @validator('bbox')
    def validate_bbox(cls, v):
        if len(v) != 4:
            raise ValueError('Bounding box must have 4 coordinates [minLon, minLat, maxLon, maxLat]')
        if v[0] >= v[2] or v[1] >= v[3]:
            raise ValueError('Invalid bounding box coordinates')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "layer": "flood_mask",
                "bbox": [107.0, 16.5, 107.5, 17.0],
                "date": "2024-01-15",
                "format": "png",
                "width": 1024,
                "height": 1024
            }
        }


class TileResponse(BaseModel):
    """Response model for tile data"""
    layer: MapLayer = Field(..., description="Requested layer")
    bbox: List[float] = Field(..., description="Bounding box")
    date: Optional[date] = Field(None, description="Data date")
    format: TileFormat = Field(..., description="Data format")
    url: Optional[str] = Field(None, description="URL to download tile")
    data: Optional[str] = Field(None, description="Base64 encoded data (for small tiles)")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "layer": "flood_mask",
                "bbox": [107.0, 16.5, 107.5, 17.0],
                "date": "2024-01-15",
                "format": "png",
                "url": "https://api.floodguard.com/tiles/flood_mask_20240115.png",
                "metadata": {
                    "resolution": "30m",
                    "crs": "EPSG:4326",
                    "water_pixels": 15420
                },
                "generated_at": "2024-01-15T10:30:00"
            }
        }


class GeoJSONFeature(BaseModel):
    """GeoJSON feature model"""
    type: Literal["Feature"] = "Feature"
    geometry: dict = Field(..., description="GeoJSON geometry")
    properties: dict = Field(..., description="Feature properties")


class GeoJSONResponse(BaseModel):
    """GeoJSON response model"""
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: List[GeoJSONFeature] = Field(..., description="List of features")
    metadata: dict = Field(default_factory=dict, description="Collection metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[107.0, 16.5], [107.5, 16.5], [107.5, 17.0], [107.0, 17.0], [107.0, 16.5]]]
                        },
                        "properties": {
                            "region": "Quảng Trị",
                            "water_area": 450.5,
                            "severity": "High"
                        }
                    }
                ],
                "metadata": {
                    "generated_at": "2024-01-15T10:30:00",
                    "total_features": 1
                }
            }
        }


class LayerMetadata(BaseModel):
    """Metadata for map layer"""
    layer: MapLayer = Field(..., description="Layer name")
    description: str = Field(..., description="Layer description")
    source: str = Field(..., description="Data source")
    resolution: str = Field(..., description="Spatial resolution")
    temporal_resolution: Optional[str] = Field(None, description="Temporal resolution")
    available_dates: List[date] = Field(default_factory=list, description="Available dates")
    bbox: List[float] = Field(..., description="Layer extent")
    
    class Config:
        json_schema_extra = {
            "example": {
                "layer": "sar",
                "description": "Sentinel-1 SAR imagery for flood detection",
                "source": "Copernicus Sentinel-1",
                "resolution": "10m",
                "temporal_resolution": "6-12 days",
                "available_dates": ["2024-01-01", "2024-01-10", "2024-01-15"],
                "bbox": [102.0, 8.0, 110.0, 24.0]
            }
        }


class AvailableLayersResponse(BaseModel):
    """Response with available map layers"""
    layers: List[LayerMetadata] = Field(..., description="List of available layers")
    total: int = Field(..., description="Total number of layers")


class TileCache(BaseModel):
    """Tile cache information"""
    layer: MapLayer = Field(..., description="Layer name")
    bbox: List[float] = Field(..., description="Bounding box")
    date: Optional[date] = Field(None, description="Data date")
    cached_at: datetime = Field(default_factory=datetime.utcnow)
    file_path: str = Field(..., description="Path to cached file")
    file_size: int = Field(..., description="File size in bytes")
    expires_at: datetime = Field(..., description="Cache expiry time")


class FloodExtentAnalysis(BaseModel):
    """Analysis of flood extent from map data"""
    region_id: str = Field(..., description="Region ID")
    date: date = Field(..., description="Analysis date")
    total_area: float = Field(..., ge=0, description="Total area in km²")
    flooded_area: float = Field(..., ge=0, description="Flooded area in km²")
    flood_percentage: float = Field(..., ge=0, le=100, description="Percentage flooded")
    max_depth: Optional[float] = Field(None, description="Maximum flood depth in meters")
    affected_settlements: int = Field(..., ge=0, description="Number of affected settlements")
    geometry: Optional[dict] = Field(None, description="GeoJSON geometry of flood extent")
    
    class Config:
        json_schema_extra = {
            "example": {
                "region_id": "1",
                "date": "2024-01-15",
                "total_area": 1200.5,
                "flooded_area": 450.5,
                "flood_percentage": 37.5,
                "max_depth": 2.8,
                "affected_settlements": 45,
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": []
                }
            }
        }
