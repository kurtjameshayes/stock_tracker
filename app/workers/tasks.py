"""
Celery tasks for background processing.

Defines asynchronous tasks for price updates, alert checking,
and data cleanup.
"""

from app.workers.celery_app import celery_app
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
import logging
import asyncio

logger = logging.getLogger(__name__)


def get_database():
    """Get database connection for Celery tasks."""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    return client[settings.MONGODB_DB_NAME]


@celery_app.task(name="app.workers.tasks.update_all_stock_prices")
def update_all_stock_prices():
    """
    Update prices for all tracked stocks.

    Fetches latest prices from external APIs for all stocks
    in the database.
    """
    logger.info("Starting price update task")

    try:
        # Import here to avoid circular imports
        from app.repositories.stock_repository import StockRepository
        from app.services.data_ingestion_service import DataIngestionService

        db = get_database()

        # Run async code in sync context
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        stock_repo = StockRepository(db)
        price_repo = StockPriceRepository(db)
        ingestion_service = DataIngestionService(stock_repo, price_repo)

        # Get all stocks
        stocks = loop.run_until_complete(stock_repo.find_many(limit=1000))

        symbols = [stock["symbol"] for stock in stocks]

        # Update prices
        results = loop.run_until_complete(
            ingestion_service.bulk_update_prices(symbols)
        )

        logger.info(f"Price update completed: {results}")

        return results

    except Exception as e:
        logger.error(f"Error in price update task: {e}")
        raise


@celery_app.task(name="app.workers.tasks.check_all_alerts")
def check_all_alerts():
    """
    Check all active alerts against current prices.

    Evaluates alert conditions and triggers notifications
    when conditions are met.
    """
    logger.info("Starting alert check task")

    try:
        from app.repositories.alert_repository import AlertRepository, AlertHistoryRepository
        from app.repositories.stock_repository import StockPriceRepository
        from app.services.alert_service import AlertService
        from decimal import Decimal

        db = get_database()
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        alert_repo = AlertRepository(db)
        history_repo = AlertHistoryRepository(db)
        price_repo = StockPriceRepository(db)

        alert_service = AlertService(alert_repo, history_repo, price_repo)

        # Get all active alerts
        all_alerts = loop.run_until_complete(
            alert_repo.find_many({"is_active": True})
        )

        triggered_count = 0

        # Group alerts by stock for efficiency
        alerts_by_stock = {}
        for alert in all_alerts:
            stock_id = alert["stock_id"]
            if stock_id not in alerts_by_stock:
                alerts_by_stock[stock_id] = []
            alerts_by_stock[stock_id].append(alert)

        # Check each stock's alerts
        for stock_id, alerts in alerts_by_stock.items():
            # Get latest price
            latest_price = loop.run_until_complete(
                price_repo.get_latest_price(stock_id)
            )

            if not latest_price:
                continue

            current_price = Decimal(str(latest_price["close"]))

            # Check each alert
            count = loop.run_until_complete(
                alert_service.check_alerts_for_stock(stock_id, current_price)
            )

            triggered_count += count

        logger.info(f"Alert check completed: {triggered_count} alerts triggered")

        return {"triggered": triggered_count, "checked": len(all_alerts)}

    except Exception as e:
        logger.error(f"Error in alert check task: {e}")
        raise


@celery_app.task(name="app.workers.tasks.cleanup_old_data")
def cleanup_old_data():
    """
    Clean up old data to manage database size.

    Removes or archives old price data and history beyond
    retention period.
    """
    logger.info("Starting data cleanup task")

    try:
        from datetime import datetime, timedelta

        db = get_database()
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Delete alert history older than 1 year
        one_year_ago = datetime.utcnow() - timedelta(days=365)

        alert_history_collection = db.alert_history
        result = loop.run_until_complete(
            alert_history_collection.delete_many(
                {"timestamp": {"$lt": one_year_ago}}
            )
        )

        logger.info(f"Deleted {result.deleted_count} old alert history entries")

        return {"deleted_alert_history": result.deleted_count}

    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        raise


@celery_app.task(name="app.workers.tasks.ingest_stock_data")
def ingest_stock_data(symbol: str, period: str = "1mo"):
    """
    Ingest historical data for a specific stock.

    Args:
        symbol: Stock symbol
        period: Time period to fetch

    Returns:
        Number of prices ingested
    """
    logger.info(f"Ingesting data for {symbol}")

    try:
        from app.repositories.stock_repository import StockRepository, StockPriceRepository
        from app.services.data_ingestion_service import DataIngestionService

        db = get_database()
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        stock_repo = StockRepository(db)
        price_repo = StockPriceRepository(db)
        ingestion_service = DataIngestionService(stock_repo, price_repo)

        # Ingest stock and prices
        stock_id = loop.run_until_complete(
            ingestion_service.ingest_stock(symbol)
        )

        if not stock_id:
            return {"error": "Failed to ingest stock"}

        count = loop.run_until_complete(
            ingestion_service.ingest_historical_prices(symbol, period)
        )

        logger.info(f"Ingested {count} prices for {symbol}")

        return {"symbol": symbol, "prices_ingested": count}

    except Exception as e:
        logger.error(f"Error ingesting data for {symbol}: {e}")
        raise
