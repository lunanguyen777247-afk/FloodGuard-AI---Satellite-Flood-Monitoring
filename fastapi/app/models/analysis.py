from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """Risk assessment levels"""
    VERY_LOW = "Very Low"
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    VERY_HIGH = "Very High"
    CRITICAL = "Critical"


class AnalysisRequest(BaseModel):
    """Request model for AI analysis"""
    regions: List[Dict[str, Any]] = Field(..., description="List of region data")
    weather: List[Dict[str, Any]] = Field(..., description="List of weather data")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis")
    include_forecast: bool = Field(default=True, description="Include forecast in analysis")
    
    @validator('regions')
    def validate_regions(cls, v):
        if not v:
            raise ValueError('At least one region is required')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "regions": [
                    {
                        "id": "1",
                        "name": "Quảng Trị",
                        "submerged_area": 450.5,
                        "rainfall": 320.0,
                        "severity": "High"
                    }
                ],
                "weather": [
                    {
                        "date": "2024-01-15",
                        "rainfall": 120.5,
                        "temperature": 24.5
                    }
                ],
                "analysis_type": "comprehensive",
                "include_forecast": True
            }
        }


class Recommendation(BaseModel):
    """Individual recommendation"""
    priority: str = Field(..., description="Priority level (High/Medium/Low)")
    category: str = Field(..., description="Category (Evacuation/Infrastructure/Emergency)")
    action: str = Field(..., description="Recommended action")
    target_regions: List[str] = Field(..., description="Affected regions")
    timeframe: str = Field(..., description="Implementation timeframe")


class AnalysisResult(BaseModel):
    """AI analysis result model"""
    summary: str = Field(..., description="Executive summary of flood situation")
    risk_assessment: str = Field(..., description="Overall risk assessment")
    risk_level: RiskLevel = Field(..., description="Categorized risk level")
    recommendations: List[str] = Field(..., description="List of recommendations")
    detailed_recommendations: Optional[List[Recommendation]] = Field(None, description="Detailed recommendations")
    confidence_score: float = Field(..., ge=0, le=1, description="AI confidence score (0-1)")
    estimated_total_loss: float = Field(..., ge=0, description="Total estimated loss in million VND")
    key_findings: List[str] = Field(default_factory=list, description="Key findings from analysis")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "summary": "Tình trạng ngập lụt nghiêm trọng tại miền Trung Việt Nam...",
                "risk_assessment": "Rủi ro cực cao với diện tích ngập rộng...",
                "risk_level": "Critical",
                "recommendations": [
                    "Sơ tán dân cư vùng trũng ngập sâu",
                    "Tăng cường hệ thống thoát nước",
                    "Chuẩn bị vật tư y tế và cứu trợ"
                ],
                "confidence_score": 0.94,
                "estimated_total_loss": 450.8,
                "key_findings": [
                    "Lượng mưa vượt ngưỡng cảnh báo",
                    "12,500 người bị ảnh hưởng"
                ],
                "analysis_timestamp": "2024-01-15T10:30:00"
            }
        }


class RegionRiskAnalysis(BaseModel):
    """Risk analysis for individual region"""
    region_id: str = Field(..., description="Region ID")
    region_name: str = Field(..., description="Region name")
    risk_level: RiskLevel = Field(..., description="Risk level")
    risk_score: float = Field(..., ge=0, le=100, description="Risk score (0-100)")
    contributing_factors: List[str] = Field(..., description="Factors contributing to risk")
    vulnerable_population: int = Field(..., description="Number of vulnerable people")
    critical_infrastructure_at_risk: int = Field(..., description="Number of critical facilities at risk")
    recommended_actions: List[str] = Field(..., description="Specific actions for this region")
    
    class Config:
        json_schema_extra = {
            "example": {
                "region_id": "1",
                "region_name": "Quảng Trị",
                "risk_level": "Critical",
                "risk_score": 87.5,
                "contributing_factors": [
                    "Lượng mưa cao (320mm)",
                    "Diện tích ngập lớn (450km²)",
                    "Mật độ dân cư cao"
                ],
                "vulnerable_population": 3500,
                "critical_infrastructure_at_risk": 12,
                "recommended_actions": [
                    "Sơ tán khẩn cấp vùng ngập sâu",
                    "Cắt điện các khu vực ngập"
                ]
            }
        }


class ComparativeAnalysis(BaseModel):
    """Comparative analysis between regions"""
    comparison_date: datetime = Field(default_factory=datetime.utcnow)
    total_regions_analyzed: int = Field(..., description="Total regions in analysis")
    most_affected_region: str = Field(..., description="Most affected region name")
    least_affected_region: str = Field(..., description="Least affected region name")
    regional_analyses: List[RegionRiskAnalysis] = Field(..., description="Individual region analyses")
    overall_trend: str = Field(..., description="Overall flood trend description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "comparison_date": "2024-01-15T10:30:00",
                "total_regions_analyzed": 6,
                "most_affected_region": "Quảng Trị",
                "least_affected_region": "Thanh Hóa",
                "overall_trend": "Xu hướng tăng về diện tích và mức độ ngập"
            }
        }


class ForecastAnalysis(BaseModel):
    """Forecast-based analysis"""
    forecast_period: str = Field(..., description="Forecast period (e.g., '24h', '3 days')")
    predicted_risk_level: RiskLevel = Field(..., description="Predicted risk level")
    predicted_rainfall: float = Field(..., ge=0, description="Predicted total rainfall in mm")
    prediction_confidence: float = Field(..., ge=0, le=1, description="Prediction confidence")
    early_warnings: List[str] = Field(..., description="Early warning messages")
    preparation_recommendations: List[str] = Field(..., description="Preparation recommendations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "forecast_period": "48h",
                "predicted_risk_level": "High",
                "predicted_rainfall": 180.5,
                "prediction_confidence": 0.82,
                "early_warnings": [
                    "Mưa lớn dự kiến trong 48h tới",
                    "Nguy cơ ngập cao tại vùng trũng"
                ],
                "preparation_recommendations": [
                    "Chuẩn bị phương tiện di chuyển",
                    "Dự trữ lương thực, nước uống"
                ]
            }
        }


class AnalysisHistory(BaseModel):
    """Historical analysis record"""
    analysis_id: str = Field(..., description="Unique analysis ID")
    analysis_type: str = Field(..., description="Type of analysis")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    result: AnalysisResult = Field(..., description="Analysis result")
    regions_analyzed: List[str] = Field(..., description="List of region IDs")
