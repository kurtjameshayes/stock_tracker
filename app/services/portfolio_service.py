"""
Portfolio service for managing investment portfolios.

Handles portfolio, position, and transaction management with
performance calculations.
"""

from typing import List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from app.repositories.portfolio_repository import (
    PortfolioRepository, PositionRepository, TransactionRepository
)
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, TransactionCreate,
    PortfolioPerformance
)
from app.models.enums import TransactionType
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class PortfolioService:
    """Service for portfolio management."""

    def __init__(
        self,
        portfolio_repository: PortfolioRepository,
        position_repository: PositionRepository,
        transaction_repository: TransactionRepository
    ):
        """
        Initialize portfolio service.

        Args:
            portfolio_repository: Portfolio repository instance
            position_repository: Position repository instance
            transaction_repository: Transaction repository instance
        """
        self.portfolio_repo = portfolio_repository
        self.position_repo = position_repository
        self.transaction_repo = transaction_repository

    async def create_portfolio(
        self,
        user_id: str,
        portfolio_data: PortfolioCreate
    ) -> Dict[str, Any]:
        """
        Create a new portfolio.

        Args:
            user_id: User ID
            portfolio_data: Portfolio creation data

        Returns:
            Created portfolio document
        """
        portfolio_doc = portfolio_data.model_dump()
        portfolio_doc["user_id"] = user_id

        portfolio_id = await self.portfolio_repo.create(portfolio_doc)
        portfolio = await self.portfolio_repo.get_by_id(portfolio_id)

        logger.info(f"Created portfolio {portfolio_id} for user {user_id}")

        return portfolio

    async def get_user_portfolios(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all portfolios for a user.

        Args:
            user_id: User ID

        Returns:
            List of portfolio documents
        """
        return await self.portfolio_repo.get_user_portfolios(user_id)

    async def get_portfolio(self, portfolio_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get portfolio by ID.

        Args:
            portfolio_id: Portfolio ID
            user_id: User ID (for authorization)

        Returns:
            Portfolio document

        Raises:
            HTTPException: If portfolio not found or unauthorized
        """
        portfolio = await self.portfolio_repo.get_by_id(portfolio_id)

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )

        if portfolio["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this portfolio"
            )

        return portfolio

    async def add_transaction(
        self,
        portfolio_id: str,
        user_id: str,
        transaction_data: TransactionCreate
    ) -> Dict[str, Any]:
        """
        Add a transaction to portfolio and update positions.

        Args:
            portfolio_id: Portfolio ID
            user_id: User ID (for authorization)
            transaction_data: Transaction data

        Returns:
            Created transaction document
        """
        # Check authorization
        await self.get_portfolio(portfolio_id, user_id)

        transaction_doc = transaction_data.model_dump()
        transaction_doc["portfolio_id"] = portfolio_id

        # Convert Decimals to floats for MongoDB
        for key in ["quantity", "price", "fees"]:
            if key in transaction_doc and transaction_doc[key] is not None:
                transaction_doc[key] = float(transaction_doc[key])

        transaction_id = await self.transaction_repo.create_transaction(transaction_doc)

        # Update position
        await self._update_position_from_transaction(portfolio_id, transaction_doc)

        transaction = await self.transaction_repo.get_by_id(transaction_id)

        logger.info(f"Added transaction {transaction_id} to portfolio {portfolio_id}")

        return transaction

    async def _update_position_from_transaction(
        self,
        portfolio_id: str,
        transaction: Dict[str, Any]
    ) -> None:
        """
        Update position based on transaction.

        Args:
            portfolio_id: Portfolio ID
            transaction: Transaction document
        """
        stock_id = transaction["stock_id"]
        transaction_type = TransactionType(transaction["type"])
        quantity = Decimal(str(transaction["quantity"]))
        price = Decimal(str(transaction["price"]))

        # Get existing position
        position = await self.position_repo.get_position(portfolio_id, stock_id)

        if transaction_type == TransactionType.BUY:
            if position:
                # Update existing position
                current_qty = Decimal(str(position["quantity"]))
                current_avg = Decimal(str(position["average_cost"]))

                new_qty = current_qty + quantity
                new_avg = ((current_qty * current_avg) + (quantity * price)) / new_qty

                await self.position_repo.update(position["_id"], {
                    "quantity": float(new_qty),
                    "average_cost": float(new_avg),
                    "last_update_date": datetime.utcnow()
                })
            else:
                # Create new position
                position_data = {
                    "portfolio_id": portfolio_id,
                    "stock_id": stock_id,
                    "quantity": float(quantity),
                    "average_cost": float(price),
                    "first_purchase_date": transaction.get("timestamp", datetime.utcnow()).date(),
                    "last_update_date": datetime.utcnow()
                }
                await self.position_repo.create(position_data)

        elif transaction_type == TransactionType.SELL:
            if position:
                current_qty = Decimal(str(position["quantity"]))
                new_qty = current_qty - quantity

                if new_qty <= 0:
                    # Close position
                    await self.position_repo.delete(position["_id"])
                else:
                    # Reduce quantity
                    await self.position_repo.update(position["_id"], {
                        "quantity": float(new_qty),
                        "last_update_date": datetime.utcnow()
                    })

    async def get_portfolio_positions(
        self,
        portfolio_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all positions in a portfolio.

        Args:
            portfolio_id: Portfolio ID
            user_id: User ID (for authorization)

        Returns:
            List of position documents
        """
        # Check authorization
        await self.get_portfolio(portfolio_id, user_id)

        return await self.position_repo.get_portfolio_positions(portfolio_id)

    async def get_portfolio_transactions(
        self,
        portfolio_id: str,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get transactions for a portfolio.

        Args:
            portfolio_id: Portfolio ID
            user_id: User ID (for authorization)
            skip: Number to skip
            limit: Maximum to return

        Returns:
            List of transaction documents
        """
        # Check authorization
        await self.get_portfolio(portfolio_id, user_id)

        return await self.transaction_repo.get_portfolio_transactions(
            portfolio_id, skip, limit
        )
