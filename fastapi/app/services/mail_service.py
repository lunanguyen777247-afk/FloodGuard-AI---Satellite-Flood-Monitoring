import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict
import logging
from datetime import datetime
from jinja2 import Template
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class MailService:
    """Service for sending email and Telegram notifications"""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> bool:
        """
        Send email notification
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (text or HTML)
            html: Whether body is HTML
            
        Returns:
            bool: Success status
        """
        try:
            message = MIMEMultipart('alternative')
            message['From'] = self.settings.EMAIL_FROM
            message['To'] = to
            message['Subject'] = subject
            
            if html:
                message.attach(MIMEText(body, 'html'))
            else:
                message.attach(MIMEText(body, 'plain'))
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.settings.SMTP_HOST,
                port=self.settings.SMTP_PORT,
                username=self.settings.SMTP_USER,
                password=self.settings.SMTP_PASSWORD,
                start_tls=True
            )
            
            logger.info(f"Email sent successfully to {to}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False
    
    async def send_flood_alert(
        self,
        to: str,
        regions_data: List[Dict],
        risk_level: str,
        recommendations: List[str]
    ) -> bool:
        """
        Send flood alert email
        
        Args:
            to: Recipient email
            regions_data: List of affected regions
            risk_level: Overall risk level
            recommendations: List of recommendations
            
        Returns:
            bool: Success status
        """
        subject = f"⚠️ Cảnh báo ngập lụt: Mức độ {risk_level}"
        
        # Create HTML email
        html_body = self._create_alert_email_html(
            regions_data,
            risk_level,
            recommendations
        )
        
        return await self.send_email(to, subject, html_body, html=True)
    
    def _create_alert_email_html(
        self,
        regions_data: List[Dict],
        risk_level: str,
        recommendations: List[str]
    ) -> str:
        """Create HTML template for flood alert email"""
        
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                  color: white; padding: 20px; border-radius: 10px 10px 0 0; }
        .header h1 { margin: 0; font-size: 24px; }
        .content { background: #f9f9f9; padding: 20px; }
        .alert-box { background: #fff3cd; border-left: 4px solid #ffc107; 
                     padding: 15px; margin: 15px 0; }
        .region-card { background: white; padding: 15px; margin: 10px 0; 
                       border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .region-name { font-weight: bold; font-size: 18px; color: #667eea; }
        .severity-high { color: #dc3545; font-weight: bold; }
        .severity-moderate { color: #ffc107; font-weight: bold; }
        .severity-low { color: #28a745; font-weight: bold; }
        .recommendations { background: #e7f3ff; padding: 15px; border-radius: 8px; }
        .footer { background: #333; color: white; padding: 15px; 
                  border-radius: 0 0 10px 10px; text-align: center; font-size: 12px; }
        ul { margin: 10px 0; }
        li { margin: 5px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌊 FloodGuard-AI</h1>
            <p>Cảnh báo tình hình ngập lụt</p>
        </div>
        
        <div class="content">
            <div class="alert-box">
                <strong>⚠️ Mức độ cảnh báo: {{ risk_level }}</strong><br>
                <small>Thời gian: {{ current_time }}</small>
            </div>
            
            <h2>📍 Các khu vực bị ảnh hưởng</h2>
            {% for region in regions %}
            <div class="region-card">
                <div class="region-name">{{ region.name }}</div>
                <p>
                    <strong>Mức độ:</strong> 
                    <span class="severity-{{ region.severity|lower }}">{{ region.severity }}</span><br>
                    <strong>Diện tích ngập:</strong> {{ region.submergedArea|round(1) }} km²<br>
                    <strong>Dân số ảnh hưởng:</strong> {{ "{:,}".format(region.affectedPopulation) }} người<br>
                    <strong>Thiệt hại ước tính:</strong> {{ region.estimatedLoss|round(1) }} tỷ VND
                </p>
            </div>
            {% endfor %}
            
            <div class="recommendations">
                <h3>💡 Khuyến nghị</h3>
                <ul>
                    {% for rec in recommendations %}
                    <li>{{ rec }}</li>
                    {% endfor %}
                </ul>
            </div>
            
            <p style="margin-top: 20px; font-size: 14px; color: #666;">
                Vui lòng theo dõi thông tin cập nhật tại 
                <a href="https://floodguard-ai.com">floodguard-ai.com</a>
            </p>
        </div>
        
        <div class="footer">
            <p>FloodGuard-AI - Hệ thống cảnh báo ngập lụt thông minh</p>
            <p>© 2024 FloodGuard-AI. Tất cả quyền được bảo lưu.</p>
        </div>
    </div>
</body>
</html>
"""
        
        template = Template(template_str)
        
        return template.render(
            risk_level=risk_level,
            current_time=datetime.now().strftime("%d/%m/%Y %H:%M"),
            regions=regions_data,
            recommendations=recommendations
        )
    
    async def send_daily_report(
        self,
        to: str,
        report_data: Dict
    ) -> bool:
        """
        Send daily flood report
        
        Args:
            to: Recipient email
            report_data: Report data including analysis and statistics
            
        Returns:
            bool: Success status
        """
        subject = f"📊 Báo cáo ngập lụt hàng ngày - {datetime.now().strftime('%d/%m/%Y')}"
        
        html_body = self._create_daily_report_html(report_data)
        
        return await self.send_email(to, subject, html_body, html=True)
    
    def _create_daily_report_html(self, report_data: Dict) -> str:
        """Create HTML template for daily report"""
        
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 700px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                  color: white; padding: 25px; border-radius: 10px 10px 0 0; }
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; 
                      margin: 20px 0; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; 
                     box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .stat-value { font-size: 32px; font-weight: bold; color: #667eea; }
        .stat-label { font-size: 14px; color: #666; margin-top: 5px; }
        .summary { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .footer { background: #333; color: white; padding: 15px; 
                  border-radius: 0 0 10px 10px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Báo cáo ngập lụt hàng ngày</h1>
            <p>{{ report_date }}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{{ total_regions }}</div>
                <div class="stat-label">Khu vực giám sát</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ total_affected|int }}</div>
                <div class="stat-label">Người bị ảnh hưởng</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ total_area|round(1) }}</div>
                <div class="stat-label">Diện tích ngập (km²)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ total_loss|round(1) }}</div>
                <div class="stat-label">Thiệt hại (tỷ VND)</div>
            </div>
        </div>
        
        <div class="summary">
            <h3>Tóm tắt tình hình</h3>
            <p>{{ summary }}</p>
        </div>
        
        <div class="footer">
            <p>FloodGuard-AI | <a href="https://floodguard-ai.com" style="color: #667eea;">floodguard-ai.com</a></p>
        </div>
    </div>
</body>
</html>
"""
        
        template = Template(template_str)
        
        return template.render(
            report_date=datetime.now().strftime("%d/%m/%Y"),
            total_regions=report_data.get('total_regions', 0),
            total_affected=report_data.get('total_affected', 0),
            total_area=report_data.get('total_area', 0),
            total_loss=report_data.get('total_loss', 0),
            summary=report_data.get('summary', 'Không có dữ liệu')
        )
    
    async def send_telegram_message(
        self,
        chat_id: str,
        message: str
    ) -> bool:
        """
        Send message via Telegram Bot
        
        Args:
            chat_id: Telegram chat ID
            message: Message text
            
        Returns:
            bool: Success status
        """
        try:
            if not self.settings.TELEGRAM_BOT_TOKEN:
                logger.warning("Telegram bot token not configured")
                return False
            
            # Import telegram library
            from telegram import Bot
            
            bot = Bot(token=self.settings.TELEGRAM_BOT_TOKEN)
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info(f"Telegram message sent to {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    async def send_telegram_flood_alert(
        self,
        chat_id: str,
        regions_data: List[Dict],
        risk_level: str
    ) -> bool:
        """
        Send flood alert via Telegram
        
        Args:
            chat_id: Telegram chat ID
            regions_data: List of affected regions
            risk_level: Overall risk level
            
        Returns:
            bool: Success status
        """
        
        message = f"""
🌊 <b>CẢNH BÁO NGẬP LỤT</b>

⚠️ Mức độ: <b>{risk_level}</b>
🕐 Thời gian: {datetime.now().strftime("%d/%m/%Y %H:%M")}

📍 <b>Các khu vực bị ảnh hưởng:</b>
"""
        
        for region in regions_data[:5]:  # Limit to top 5
            message += f"""
• <b>{region['name']}</b>
  Mức độ: {region['severity']}
  Diện tích: {region['submergedArea']:.1f} km²
  Dân số: {region['affectedPopulation']:,} người
"""
        
        if len(regions_data) > 5:
            message += f"\n<i>... và {len(regions_data) - 5} khu vực khác</i>\n"
        
        message += "\n🔗 Chi tiết: https://floodguard-ai.com"
        
        return await self.send_telegram_message(chat_id, message)


# Create singleton instance
mail_service = MailService()
