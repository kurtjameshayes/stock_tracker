"""
Portfolio API endpoints.

Handles portfolio, position, and transaction management.
"""

from fastapi import APIRouter, Depends, Path, Query
from typing import List
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioResponse, PortfolioUpdate,
    TransactionCreate, TransactionResponse, PositionResponse
)
from app.services.portfolio_service import PortfolioService
from app.api.dependencies import get_portfolio_service
from app.core.security import get_current_user_id

router = APIRouter()


@router.get("", response_model=List[PortfolioResponse])
async def get_portfolios(
    current_user_id: str = Depends(get_current_user_id),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """
    Get all portfolios for the current user.

    Returns all portfolios owned by the authenticated user.
    """
    portfolios = await portfolio_service.get_user_portfolios(current_user_id)
    return portfolios


@router.post("", response_model=PortfolioResponse)
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    current_user_id: str = Depends(get_current_user_id),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """
    Create a new portfolio.

    Creates a new portfolio for tracking investments.
    """
    portfolio = await portfolio_service.create_portfolio(current_user_id, portfolio_data)
    return portfolio


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: str = Path(...),
    current_user_id: str = Depends(get_current_user_id),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """
    Get portfolio by ID.

    Returns portfolio details.
    """
    portfolio = await portfolio_service.get_portfolio(portfolio_id, current_user_id)
    return portfolio


@router.get("/{portfolio_id}/positions", response_model=List[PositionResponse])
async def get_portfolio_positions(
    portfolio_id: str,
    current_user_id: str = Depends(get_current_user_id),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """
    Get all positions in a portfolio.

    Returns all current holdings in the portfolio.
    """
    positions = await portfolio_service.get_portfolio_positions(
        portfolio_id, current_user_id
    )
    return positions


@router.post("/{portfolio_id}/transactions", response_model=TransactionResponse)
async def create_transaction(
    portfolio_id: str,
    transaction_data: TransactionCreate,
    current_user_id: str = Depends(get_current_user_id),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """
    Record a new transaction.

    Records a buy, sell, or other transaction in the portfolio.
    """
    transaction = await portfolio_service.add_transaction(
        portfolio_id, current_user_id, transaction_data
    )
    return transaction


@router.get("/{portfolio_id}/transactions", response_model=List[TransactionResponse])
async def get_portfolio_transactions(
    portfolio_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user_id: str = Depends(get_current_user_id),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """
    Get transaction history.

    Returns transaction history for the portfolio.
    """
    transactions = await portfolio_service.get_portfolio_transactions(
        portfolio_id, current_user_id, skip, limit
    )
    return transactions
