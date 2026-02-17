from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging
from datetime import datetime
from typing import List

from app.models.subscribe import (
    SubscriptionCreate, Subscription, SubscriptionResponse,
    UnsubscribeRequest, SubscriptionStatistics, NotificationContent
)
from app.services.mail_service import mail_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscribe", tags=["subscriptions"])

# In-memory storage (in production, use database)
subscriptions_db = {}
subscription_counter = 0


@router.post("/", response_model=SubscriptionResponse)
async def create_subscription(
    subscription: SubscriptionCreate,
    background_tasks: BackgroundTasks
):
    """
    Create a new subscription for flood alerts
    
    - **contact**: Email address or Telegram ID
    - **frequency**: Notification frequency (realtime/hourly/daily/weekly)
    - **channel**: Delivery channel (email/telegram/both)
    - **regions**: Specific regions to monitor (empty = all regions)
    - **min_severity**: Minimum severity level to notify
    """
    global subscription_counter
    
    try:
        # Generate subscription ID
        subscription_counter += 1
        sub_id = f"sub_{subscription_counter}"
        
        # Create subscription object
        new_sub = Subscription(
            id=sub_id,
            **subscription.dict(),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Store in database
        subscriptions_db[sub_id] = new_sub
        
        # Send confirmation email in background
        if subscription.channel in ["email", "both"]:
            background_tasks.add_task(
                send_confirmation_email,
                subscription.contact,
                subscription.frequency
            )
        
        logger.info(f"New subscription created: {sub_id}")
        
        # Determine notification schedule message
        schedule_msg = {
            "realtime": "Bạn sẽ nhận thông báo ngay khi có cảnh báo mới",
            "hourly": "Báo cáo sẽ được gửi mỗi giờ",
            "daily": "Báo cáo sẽ được gửi vào 08:00 AM hàng ngày",
            "weekly": "Báo cáo sẽ được gửi vào thứ 2 hàng tuần"
        }.get(subscription.frequency, "Báo cáo sẽ được gửi theo lịch trình đã chọn")
        
        return SubscriptionResponse(
            success=True,
            message=f"Đăng ký thành công! {schedule_msg}",
            subscription=new_sub
        )
        
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create subscription: {str(e)}"
        )


@router.get("/", response_model=List[Subscription])
async def list_subscriptions():
    """
    List all active subscriptions (admin endpoint)
    """
    try:
        return list(subscriptions_db.values())
    except Exception as e:
        logger.error(f"Error listing subscriptions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list subscriptions: {str(e)}"
        )


@router.delete("/")
async def unsubscribe(request: UnsubscribeRequest):
    """
    Unsubscribe from flood alerts
    
    - **contact**: Email or Telegram ID to unsubscribe
    - **reason**: Optional reason for unsubscribing
    """
    try:
        # Find subscription by contact
        found = False
        for sub_id, sub in subscriptions_db.items():
            if sub.contact == request.contact:
                sub.is_active = False
                sub.updated_at = datetime.utcnow()
                found = True
                logger.info(f"Subscription {sub_id} deactivated. Reason: {request.reason}")
        
        if not found:
            raise HTTPException(
                status_code=404,
                detail="Subscription not found"
            )
        
        return {
            "success": True,
            "message": "Đã hủy đăng ký thành công"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unsubscribe: {str(e)}"
        )


@router.get("/statistics", response_model=SubscriptionStatistics)
async def get_subscription_statistics():
    """
    Get statistics about subscriptions
    """
    try:
        active_subs = [s for s in subscriptions_db.values() if s.is_active]
        
        email_count = sum(1 for s in active_subs if s.channel in ["email", "both"])
        telegram_count = sum(1 for s in active_subs if s.channel in ["telegram", "both"])
        daily_count = sum(1 for s in active_subs if s.frequency == "daily")
        
        return SubscriptionStatistics(
            total_subscriptions=len(subscriptions_db),
            active_subscriptions=len(active_subs),
            email_subscriptions=email_count,
            telegram_subscriptions=telegram_count,
            daily_frequency=daily_count,
            notifications_sent_today=0,  # Would track from logs
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.post("/send-test")
async def send_test_notification(contact: str):
    """
    Send a test notification to verify setup
    
    - **contact**: Email or Telegram ID to send test to
    """
    try:
        # Create test notification content
        test_regions = [
            {
                "name": "Test Region",
                "severity": "Moderate",
                "submergedArea": 100.5,
                "affectedPopulation": 1000,
                "estimatedLoss": 10.5
            }
        ]
        
        test_recommendations = [
            "Đây là thông báo kiểm tra",
            "Hệ thống hoạt động bình thường"
        ]
        
        # Send email
        success = await mail_service.send_flood_alert(
            to=contact,
            regions_data=test_regions,
            risk_level="Test",
            recommendations=test_recommendations
        )
        
        if success:
            return {
                "success": True,
                "message": "Thông báo kiểm tra đã được gửi"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send test notification"
            )
        
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send test: {str(e)}"
        )


async def send_confirmation_email(email: str, frequency: str):
    """
    Background task to send confirmation email
    """
    try:
        await mail_service.send_email(
            to=email,
            subject="Xác nhận đăng ký FloodGuard-AI",
            body=f"""
            Xin chào,
            
            Bạn đã đăng ký nhận thông báo ngập lụt từ FloodGuard-AI.
            
            Tần suất: {frequency}
            
            Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi!
            
            FloodGuard-AI Team
            """,
            html=False
        )
        logger.info(f"Confirmation email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {e}")
