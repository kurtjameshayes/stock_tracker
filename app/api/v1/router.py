"""
API v1 router configuration.

Aggregates all v1 endpoint routers.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, stocks, alerts, watchlists, portfolios, analytics
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(watchlists.router, prefix="/watchlists", tags=["Watchlists"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["Portfolios"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
