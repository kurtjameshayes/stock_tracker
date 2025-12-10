"""
Alert API endpoints.

Handles alert creation, management, and history.
"""

from fastapi import APIRouter, Depends, Path
from typing import List
from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate
from app.services.alert_service import AlertService
from app.api.dependencies import get_alert_service
from app.core.security import get_current_user_id

router = APIRouter()


@router.get("", response_model=List[AlertResponse])
async def get_alerts(
    active_only: bool = False,
    current_user_id: str = Depends(get_current_user_id),
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Get all alerts for the current user.

    Returns user's alerts, optionally filtered to active ones only.
    """
    alerts = await alert_service.get_user_alerts(current_user_id, active_only)
    return alerts


@router.post("", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    current_user_id: str = Depends(get_current_user_id),
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Create a new price alert.

    Creates an alert that will trigger when the specified condition is met.
    """
    alert = await alert_service.create_alert(current_user_id, alert_data)
    return alert


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str = Path(...),
    current_user_id: str = Depends(get_current_user_id),
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Get alert details by ID.

    Returns detailed information about a specific alert.
    """
    alert = await alert_service.get_alert(alert_id, current_user_id)
    return alert


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    update_data: AlertUpdate,
    current_user_id: str = Depends(get_current_user_id),
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Update an alert.

    Updates alert configuration, notification channels, or active status.
    """
    alert = await alert_service.update_alert(alert_id, current_user_id, update_data)
    return alert


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    current_user_id: str = Depends(get_current_user_id),
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Delete an alert.

    Permanently removes the alert.
    """
    success = await alert_service.delete_alert(alert_id, current_user_id)
    return {"message": "Alert deleted successfully" if success else "Failed to delete alert"}


@router.get("/{alert_id}/history")
async def get_alert_history(
    alert_id: str,
    current_user_id: str = Depends(get_current_user_id),
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Get alert trigger history.

    Returns history of when the alert was triggered.
    """
    history = await alert_service.get_alert_history(alert_id, current_user_id)
    return {"alert_id": alert_id, "history": history}
