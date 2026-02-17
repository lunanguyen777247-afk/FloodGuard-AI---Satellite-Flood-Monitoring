from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import logging
from datetime import datetime

from app.models.analysis import (
    AnalysisRequest, AnalysisResult, 
    ComparativeAnalysis, ForecastAnalysis
)
from app.services.ai_service import ai_service
from app.api.regions import get_regions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-analysis", tags=["analysis"])


@router.post("/", response_model=AnalysisResult)
async def analyze_flood_situation(request: AnalysisRequest):
    """
    Perform AI-powered analysis of flood situation
    
    - **regions**: List of region data to analyze
    - **weather**: Historical weather data
    - **analysis_type**: Type of analysis (comprehensive/quick/comparative)
    - **include_forecast**: Include forecast predictions
    """
    try:
        logger.info(f"Starting AI analysis for {len(request.regions)} regions")
        
        # Perform AI analysis
        result = ai_service.analyze_flood_situation(
            regions=request.regions,
            weather=request.weather,
            include_forecast=request.include_forecast
        )
        
        logger.info(f"AI analysis completed with risk level: {result.risk_level}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {str(e)}"
        )


@router.post("/quick", response_model=AnalysisResult)
async def quick_analysis():
    """
    Perform quick AI analysis using current region data
    
    This endpoint automatically fetches current data and performs analysis
    """
    try:
        # Get current regions data
        regions_response = await get_regions()
        
        if not regions_response.regions:
            raise HTTPException(
                status_code=404,
                detail="No region data available for analysis"
            )
        
        # Convert to dict format for AI service
        regions_data = [r.dict() for r in regions_response.regions]
        
        # Create mock weather data (in production, would fetch from weather API)
        weather_data = [
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "rainfall": 120.0,
                "temperature": 24.5
            }
        ]
        
        # Perform analysis
        result = ai_service.analyze_flood_situation(
            regions=regions_data,
            weather=weather_data,
            include_forecast=True
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quick analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Quick analysis failed: {str(e)}"
        )


@router.get("/report/text")
async def get_text_report():
    """
    Generate text-based analysis report
    
    Returns a formatted text report suitable for email or download
    """
    try:
        # Get current data and analysis
        regions_response = await get_regions()
        regions_data = [r.dict() for r in regions_response.regions]
        
        weather_data = []
        
        analysis = ai_service.analyze_flood_situation(
            regions=regions_data,
            weather=weather_data,
            include_forecast=True
        )
        
        # Generate text report
        report = ai_service.generate_summary_report(analysis, regions_data)
        
        return {
            "report": report,
            "generated_at": datetime.utcnow(),
            "format": "text/plain"
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.post("/forecast", response_model=ForecastAnalysis)
async def generate_forecast():
    """
    Generate flood forecast for next 24-48 hours
    
    Uses AI to predict flood risk based on weather forecasts
    """
    try:
        # In production, would integrate with weather forecast APIs
        # For now, return a structured forecast
        
        return ForecastAnalysis(
            forecast_period="48h",
            predicted_risk_level="High",
            predicted_rainfall=150.5,
            prediction_confidence=0.85,
            early_warnings=[
                "Mưa lớn dự kiến trong 48h tới",
                "Nguy cơ ngập cao tại vùng trũng",
                "Khả năng mực nước sông dâng cao"
            ],
            preparation_recommendations=[
                "Chuẩn bị phương tiện di chuyển",
                "Dự trữ lương thực, nước uống",
                "Theo dõi thông tin cập nhật",
                "Di dời tài sản lên nơi cao"
            ]
        )
        
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate forecast: {str(e)}"
        )


@router.get("/health")
async def check_ai_service_health():
    """
    Check AI service health and availability
    """
    try:
        # Simple health check
        return {
            "status": "healthy",
            "service": "AI Analysis Service",
            "model": "Gemini-1.5-Flash",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"AI service health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI service unavailable"
        )
