from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class NotificationFrequency(str, Enum):
    """Notification frequency options"""
    REALTIME = "realtime"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    TELEGRAM = "telegram"
    BOTH = "both"


class SubscriptionBase(BaseModel):
    """Base subscription model"""
    contact: str = Field(..., description="Email address or Telegram ID")
    frequency: NotificationFrequency = Field(
        default=NotificationFrequency.DAILY,
        description="Notification frequency"
    )
    channel: NotificationChannel = Field(
        default=NotificationChannel.EMAIL,
        description="Notification channel"
    )
    regions: Optional[List[str]] = Field(
        None,
        description="Specific regions to monitor (empty = all regions)"
    )
    min_severity: Optional[str] = Field(
        "Moderate",
        description="Minimum severity level to notify"
    )


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating a subscription"""
    
    @validator('contact')
    def validate_contact(cls, v, values):
        channel = values.get('channel')
        if channel == NotificationChannel.EMAIL or channel == NotificationChannel.BOTH:
            # Basic email validation
            if '@' not in v:
                raise ValueError('Invalid email format')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "contact": "user@example.com",
                "frequency": "daily",
                "channel": "email",
                "regions": ["Quảng Trị", "Thừa Thiên Huế"],
                "min_severity": "Moderate"
            }
        }


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription"""
    frequency: Optional[NotificationFrequency] = None
    channel: Optional[NotificationChannel] = None
    regions: Optional[List[str]] = None
    min_severity: Optional[str] = None
    is_active: Optional[bool] = None


class Subscription(SubscriptionBase):
    """Full subscription model"""
    id: str = Field(..., description="Unique subscription ID")
    is_active: bool = Field(default=True, description="Subscription status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_notification_at: Optional[datetime] = Field(
        None,
        description="Last notification sent time"
    )
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "sub_123",
                "contact": "user@example.com",
                "frequency": "daily",
                "channel": "email",
                "regions": ["Quảng Trị"],
                "min_severity": "Moderate",
                "is_active": True,
                "created_at": "2024-01-15T08:00:00",
                "updated_at": "2024-01-15T08:00:00",
                "last_notification_at": None
            }
        }


class SubscriptionResponse(BaseModel):
    """Response after creating/updating subscription"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    subscription: Optional[Subscription] = Field(None, description="Subscription details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Đăng ký thành công. Báo cáo sẽ được gửi vào 08:00 AM hàng ngày.",
                "subscription": {
                    "id": "sub_123",
                    "contact": "user@example.com",
                    "frequency": "daily",
                    "channel": "email",
                    "is_active": True
                }
            }
        }


class UnsubscribeRequest(BaseModel):
    """Request to unsubscribe"""
    contact: str = Field(..., description="Email or Telegram ID to unsubscribe")
    reason: Optional[str] = Field(None, description="Optional unsubscribe reason")


class NotificationLog(BaseModel):
    """Log of sent notifications"""
    id: str = Field(..., description="Notification log ID")
    subscription_id: str = Field(..., description="Related subscription ID")
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    channel: NotificationChannel = Field(..., description="Channel used")
    status: str = Field(..., description="Delivery status (sent/failed)")
    content_summary: str = Field(..., description="Brief content summary")
    error_message: Optional[str] = Field(None, description="Error if failed")


class NotificationContent(BaseModel):
    """Content for notification"""
    subject: str = Field(..., description="Email subject or message title")
    summary: str = Field(..., description="Brief summary")
    regions_data: List[dict] = Field(..., description="Detailed region data")
    risk_level: str = Field(..., description="Overall risk level")
    recommendations: List[str] = Field(..., description="Key recommendations")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Cảnh báo ngập lụt: Quảng Trị - Mức độ Cao",
                "summary": "Tình hình ngập lụt nghiêm trọng tại 3 khu vực...",
                "regions_data": [
                    {
                        "name": "Quảng Trị",
                        "severity": "High",
                        "submerged_area": 450.5
                    }
                ],
                "risk_level": "High",
                "recommendations": [
                    "Sơ tán dân cư vùng ngập",
                    "Tăng cường cứu trợ"
                ],
                "generated_at": "2024-01-15T08:00:00"
            }
        }


class SubscriptionStatistics(BaseModel):
    """Statistics about subscriptions"""
    total_subscriptions: int = Field(..., description="Total number of subscriptions")
    active_subscriptions: int = Field(..., description="Active subscriptions")
    email_subscriptions: int = Field(..., description="Email channel subscriptions")
    telegram_subscriptions: int = Field(..., description="Telegram channel subscriptions")
    daily_frequency: int = Field(..., description="Daily frequency subscriptions")
    notifications_sent_today: int = Field(..., description="Notifications sent today")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
