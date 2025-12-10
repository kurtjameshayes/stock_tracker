"""
Alert-related Pydantic schemas.

Schemas for creating and managing stock price alerts.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from decimal import Decimal
from app.models.enums import AlertType, NotificationChannel


class AlertCondition(BaseModel):
    """Schema for alert condition parameters."""
    threshold: Optional[Decimal] = None
    percentage: Optional[Decimal] = None
    period: Optional[str] = None  # e.g., "1d", "1w", "1h"
    indicator_value: Optional[Decimal] = None
    comparison: Optional[str] = None  # e.g., "greater_than", "less_than"
    additional_params: Dict[str, Any] = {}


class AlertBase(BaseModel):
    """Base alert schema."""
    stock_id: str
    type: AlertType
    condition: AlertCondition
    notification_channels: List[NotificationChannel] = [NotificationChannel.EMAIL]
    is_active: bool = True


class AlertCreate(AlertBase):
    """Schema for creating a new alert."""
    pass


class AlertUpdate(BaseModel):
    """Schema for updating an alert."""
    condition: Optional[AlertCondition] = None
    notification_channels: Optional[List[NotificationChannel]] = None
    is_active: Optional[bool] = None


class AlertResponse(AlertBase):
    """Schema for alert response."""
    id: str = Field(..., alias="_id")
    user_id: str
    triggered_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        populate_by_name = True


class AlertHistoryResponse(BaseModel):
    """Schema for alert history entry."""
    id: str = Field(..., alias="_id")
    alert_id: str
    stock_id: str
    triggered_value: Decimal
    condition: AlertCondition
    notifications_sent: List[NotificationChannel]
    timestamp: datetime

    class Config:
        populate_by_name = True


class AlertTestRequest(BaseModel):
    """Schema for testing alert condition."""
    stock_id: str
    type: AlertType
    condition: AlertCondition


class AlertTestResponse(BaseModel):
    """Schema for alert test result."""
    would_trigger: bool
    current_value: Decimal
    threshold_value: Optional[Decimal] = None
    message: str
