import google.generativeai as genai
from typing import Dict, List, Any
import logging
import json
from datetime import datetime
from app.core.config import get_settings
from app.models.analysis import AnalysisResult, RiskLevel, Recommendation

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered flood analysis using Google Gemini"""
    
    def __init__(self):
        self.settings = get_settings()
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Google Gemini AI"""
        try:
            genai.configure(api_key=self.settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(self.settings.GEMINI_MODEL)
            logger.info("Google Gemini AI initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {e}")
            raise
    
    def analyze_flood_situation(
        self,
        regions: List[Dict[str, Any]],
        weather: List[Dict[str, Any]],
        include_forecast: bool = True
    ) -> AnalysisResult:
        """
        Analyze flood situation using AI
        
        Args:
            regions: List of region data with flood information
            weather: List of weather data
            include_forecast: Include forecast in analysis
            
        Returns:
            AnalysisResult: Comprehensive flood analysis
        """
        try:
            # Prepare prompt for AI
            prompt = self._build_analysis_prompt(regions, weather, include_forecast)
            
            # Generate analysis
            response = self.model.generate_content(prompt)
            
            # Parse response
            analysis = self._parse_ai_response(response.text, regions)
            
            logger.info(f"AI analysis completed for {len(regions)} regions")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            raise
    
    def _build_analysis_prompt(
        self,
        regions: List[Dict[str, Any]],
        weather: List[Dict[str, Any]],
        include_forecast: bool
    ) -> str:
        """Build comprehensive prompt for AI analysis"""
        
        prompt = """Bạn là chuyên gia phân tích ngập lụt cho hệ thống FloodGuard-AI tại Việt Nam. 
Hãy phân tích tình hình ngập lụt dựa trên dữ liệu sau và đưa ra đánh giá chi tiết.

THÔNG TIN DỮ LIỆU:

"""
        # Add regions data
        prompt += "## Dữ liệu các vùng ngập:\n"
        for i, region in enumerate(regions, 1):
            prompt += f"""
{i}. {region.get('name', 'Unknown')}:
   - Diện tích ngập: {region.get('submergedArea', 0):.1f} km²
   - Lượng mưa: {region.get('rainfall', 0):.1f} mm
   - Độ sâu trung bình: {region.get('avgDepth', 0):.1f} m
   - Mức độ nghiêm trọng: {region.get('severity', 'Unknown')}
   - Dân số ảnh hưởng: {region.get('affectedPopulation', 0):,} người
   - Thiệt hại ước tính: {region.get('estimatedLoss', 0):.1f} tỷ VND
"""
        
        # Add weather data
        if weather:
            prompt += "\n## Dữ liệu thời tiết gần đây:\n"
            for w in weather[-7:]:  # Last 7 days
                prompt += f"- {w.get('date')}: Mưa {w.get('rainfall', 0):.1f}mm, Nhiệt độ {w.get('temperature', 0):.1f}°C\n"
        
        prompt += """

YÊU CẦU PHÂN TÍCH:

1. TỔNG QUAN TÌNH HÌNH:
   - Đánh giá tổng thể tình trạng ngập lụt
   - Các khu vực nghiêm trọng nhất
   - Xu hướng phát triển

2. PHÂN TÍCH RỦI RO:
   - Mức độ rủi ro tổng thể (Very Low/Low/Moderate/High/Very High/Critical)
   - Các yếu tố đóng góp vào rủi ro
   - Đánh giá tác động đến cộng đồng và kinh tế

3. KHUYẾN NGHỊ HÀNH ĐỘNG:
   - Các biện pháp ứng phó khẩn cấp
   - Hành động ngắn hạn (1-3 ngày)
   - Biện pháp trung và dài hạn
   - Ưu tiên theo mức độ quan trọng

4. DỰ BÁO VÀ CẢNH BÁO:
   - Dự báo diễn biến trong 24-48h tới
   - Các cảnh báo cần thiết
   - Khuyến nghị chuẩn bị

ĐỊNH DẠNG TRẢ LỜI (JSON):
{
    "summary": "Tóm tắt tình hình ngập lụt (2-3 câu)",
    "risk_assessment": "Đánh giá chi tiết về rủi ro (1 đoạn văn)",
    "risk_level": "Very Low/Low/Moderate/High/Very High/Critical",
    "confidence_score": 0.85,
    "key_findings": [
        "Phát hiện quan trọng 1",
        "Phát hiện quan trọng 2"
    ],
    "recommendations": [
        "Khuyến nghị 1",
        "Khuyến nghị 2",
        "Khuyến nghị 3"
    ],
    "detailed_recommendations": [
        {
            "priority": "High/Medium/Low",
            "category": "Evacuation/Infrastructure/Emergency/Prevention",
            "action": "Hành động cụ thể",
            "target_regions": ["Khu vực 1", "Khu vực 2"],
            "timeframe": "Ngay lập tức/1-3 ngày/1 tuần"
        }
    ]
}

Hãy trả lời bằng JSON hợp lệ, KHÔNG thêm markdown hay text khác.
"""
        
        return prompt
    
    def _parse_ai_response(
        self,
        response_text: str,
        regions: List[Dict[str, Any]]
    ) -> AnalysisResult:
        """Parse AI response and create AnalysisResult"""
        
        try:
            # Clean response text
            clean_text = response_text.strip()
            if clean_text.startswith('```json'):
                clean_text = clean_text[7:]
            if clean_text.endswith('```'):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            # Parse JSON
            data = json.loads(clean_text)
            
            # Calculate total estimated loss
            total_loss = sum(r.get('estimatedLoss', 0) for r in regions)
            
            # Map risk level
            risk_level_map = {
                "Very Low": RiskLevel.VERY_LOW,
                "Low": RiskLevel.LOW,
                "Moderate": RiskLevel.MODERATE,
                "High": RiskLevel.HIGH,
                "Very High": RiskLevel.VERY_HIGH,
                "Critical": RiskLevel.CRITICAL
            }
            
            risk_level = risk_level_map.get(
                data.get('risk_level', 'Moderate'),
                RiskLevel.MODERATE
            )
            
            # Parse detailed recommendations
            detailed_recs = []
            for rec in data.get('detailed_recommendations', []):
                detailed_recs.append(Recommendation(
                    priority=rec.get('priority', 'Medium'),
                    category=rec.get('category', 'General'),
                    action=rec.get('action', ''),
                    target_regions=rec.get('target_regions', []),
                    timeframe=rec.get('timeframe', 'Unknown')
                ))
            
            # Create result
            result = AnalysisResult(
                summary=data.get('summary', 'Phân tích tình hình ngập lụt'),
                risk_assessment=data.get('risk_assessment', ''),
                risk_level=risk_level,
                recommendations=data.get('recommendations', []),
                detailed_recommendations=detailed_recs if detailed_recs else None,
                confidence_score=data.get('confidence_score', 0.8),
                estimated_total_loss=total_loss,
                key_findings=data.get('key_findings', []),
                analysis_timestamp=datetime.utcnow()
            )
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            # Return fallback result
            return self._create_fallback_result(regions)
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return self._create_fallback_result(regions)
    
    def _create_fallback_result(self, regions: List[Dict[str, Any]]) -> AnalysisResult:
        """Create fallback analysis result when AI fails"""
        
        total_loss = sum(r.get('estimatedLoss', 0) for r in regions)
        total_affected = sum(r.get('affectedPopulation', 0) for r in regions)
        
        # Determine risk level based on severity
        severity_counts = {}
        for r in regions:
            severity = r.get('severity', 'Low')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        if severity_counts.get('Critical', 0) > 0:
            risk_level = RiskLevel.CRITICAL
        elif severity_counts.get('High', 0) > 0:
            risk_level = RiskLevel.VERY_HIGH
        else:
            risk_level = RiskLevel.HIGH
        
        return AnalysisResult(
            summary=f"Phân tích {len(regions)} khu vực ngập lụt với tổng {total_affected:,} người bị ảnh hưởng.",
            risk_assessment=f"Tình trạng ngập lụt nghiêm trọng với thiệt hại ước tính {total_loss:.1f} tỷ VND.",
            risk_level=risk_level,
            recommendations=[
                "Sơ tán dân cư vùng ngập sâu",
                "Tăng cường hệ thống thoát nước",
                "Chuẩn bị vật tư y tế và cứu trợ",
                "Theo dõi dự báo thời tiết"
            ],
            confidence_score=0.75,
            estimated_total_loss=total_loss,
            key_findings=[
                f"{len(regions)} khu vực bị ảnh hưởng",
                f"{total_affected:,} người cần hỗ trợ"
            ],
            analysis_timestamp=datetime.utcnow()
        )
    
    def generate_summary_report(
        self,
        analysis: AnalysisResult,
        regions: List[Dict[str, Any]]
    ) -> str:
        """
        Generate text summary report from analysis
        
        Args:
            analysis: Analysis result
            regions: Region data
            
        Returns:
            str: Formatted report text
        """
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════╗
║          BÁO CÁO PHÂN TÍCH NGẬP LỤT - FLOODGUARD-AI                 ║
║          Thời gian: {analysis.analysis_timestamp.strftime('%d/%m/%Y %H:%M')}                            ║
╚══════════════════════════════════════════════════════════════════════╝

1. TỔNG QUAN TÌNH HÌNH
{analysis.summary}

2. ĐÁNH GIÁ RỦI RO: {analysis.risk_level.value}
{analysis.risk_assessment}

Độ tin cậy: {analysis.confidence_score*100:.0f}%
Thiệt hại ước tính: {analysis.estimated_total_loss:.1f} tỷ VND

3. CÁC PHÁT HIỆN QUAN TRỌNG
"""
        for i, finding in enumerate(analysis.key_findings, 1):
            report += f"   {i}. {finding}\n"
        
        report += "\n4. KHUYẾN NGHỊ HÀNH ĐỘNG\n"
        for i, rec in enumerate(analysis.recommendations, 1):
            report += f"   {i}. {rec}\n"
        
        if analysis.detailed_recommendations:
            report += "\n5. CHI TIẾT KHUYẾN NGHỊ\n"
            for rec in analysis.detailed_recommendations:
                report += f"""
   [{rec.priority}] {rec.category}
   Hành động: {rec.action}
   Khu vực: {', '.join(rec.target_regions)}
   Thời gian: {rec.timeframe}
"""
        
        report += "\n6. CHI TIẾT CÁC KHU VỰC\n"
        for region in regions:
            report += f"""
   • {region['name']}
     - Diện tích ngập: {region['submergedArea']:.1f} km²
     - Dân số ảnh hưởng: {region['affectedPopulation']:,} người
     - Mức độ: {region['severity']}
"""
        
        report += "\n" + "═" * 70 + "\n"
        report += "Báo cáo được tạo tự động bởi FloodGuard-AI\n"
        
        return report


# Create singleton instance
ai_service = AIService()
