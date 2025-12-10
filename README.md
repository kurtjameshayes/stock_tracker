# Stock Tracker Backend

A comprehensive backend system for tracking stock prices, generating alerts, and performing technical analysis for informed trading decisions.

## Features

### Core Functionality
- **Real-time Stock Price Tracking**: Monitor stock prices from multiple exchanges
- **Price Alerts**: Set customizable alerts based on price thresholds and technical indicators
- **Technical Analysis**: Comprehensive suite of technical indicators and chart pattern recognition
- **Portfolio Management**: Track investments, positions, and performance
- **Watchlists**: Organize and monitor groups of stocks
- **Historical Data**: Access and analyze historical price data

### Technical Analysis Indicators
- **Trend Indicators**: SMA, EMA, MACD, ADX
- **Momentum Indicators**: RSI, Stochastic, CCI, ROC
- **Volatility Indicators**: Bollinger Bands, ATR, Standard Deviation
- **Volume Indicators**: OBV, VWAP, Volume Profile
- **Support/Resistance**: Fibonacci Retracements, Pivot Points

### Advanced Features
- WebSocket support for real-time updates
- Background job processing with Celery
- Caching layer with Redis
- RESTful API with comprehensive documentation
- JWT-based authentication
- Rate limiting
- Extensible data source integrations

## Technology Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: MongoDB
- **Cache**: Redis
- **Task Queue**: Celery
- **Data Analysis**: Pandas, NumPy, TA-Lib
- **Authentication**: JWT (JSON Web Tokens)
- **Testing**: Pytest
- **Containerization**: Docker & Docker Compose

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    API Gateway/Load Balancer             │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                     FastAPI Application                  │
│                    (REST API + WebSocket)                │
└─────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┴───────────────────┐
        ↓                   ↓                   ↓
┌───────────────┐  ┌────────────────┐  ┌──────────────┐
│ Price Tracker │  │ Alert Engine   │  │ Analytics    │
│   Service     │  │    Service     │  │   Service    │
└───────────────┘  └────────────────┘  └──────────────┘
        ↓                   ↓                   ↓
┌───────────────────────────────────────────────────────┐
│            Data Layer (MongoDB + Redis)               │
└───────────────────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────────────────┐
│           Celery Workers (Background Tasks)           │
└───────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites
- Python 3.11 or higher
- MongoDB 7.0+
- Redis 7.0+
- Docker & Docker Compose (optional)

### Using Docker (Recommended)

1. **Clone the repository**
```bash
git clone <repository-url>
cd stock_tracker
```

2. **Create environment file**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start services**
```bash
docker-compose up -d
```

4. **Access the application**
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Celery Flower: http://localhost:5555

### Manual Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd stock_tracker
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start MongoDB and Redis**
```bash
# MongoDB
mongod --dbpath /path/to/data

# Redis
redis-server
```

6. **Run the application**
```bash
# Start FastAPI server
uvicorn main:app --reload

# Start Celery worker (in another terminal)
celery -A app.workers.celery_app worker --loglevel=info

# Start Celery beat (in another terminal)
celery -A app.workers.celery_app beat --loglevel=info
```

## Configuration

Edit the `.env` file to configure the application:

```env
# Application
APP_NAME=Stock Tracker Backend
SECRET_KEY=your-secret-key
DEBUG=True

# Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=stock_tracker

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
JWT_SECRET_KEY=your-jwt-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External APIs
ALPHA_VANTAGE_API_KEY=your-key
FINNHUB_API_KEY=your-key
```

## API Documentation

Once the application is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Authentication

1. **Register a new user**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "password": "SecurePass123"
  }'
```

2. **Login**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

3. **Use the access token in subsequent requests**
```bash
curl -X GET "http://localhost:8000/api/v1/stocks/AAPL" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Key Endpoints

#### Stocks
- `GET /api/v1/stocks/search?q=AAPL` - Search stocks
- `GET /api/v1/stocks/{symbol}` - Get stock details
- `GET /api/v1/stocks/{symbol}/quote` - Get current quote
- `GET /api/v1/stocks/{symbol}/history` - Get historical data
- `POST /api/v1/stocks/{symbol}/ingest` - Ingest stock data

#### Alerts
- `GET /api/v1/alerts` - List user alerts
- `POST /api/v1/alerts` - Create alert
- `PUT /api/v1/alerts/{id}` - Update alert
- `DELETE /api/v1/alerts/{id}` - Delete alert

#### Watchlists
- `GET /api/v1/watchlists` - List watchlists
- `POST /api/v1/watchlists` - Create watchlist
- `POST /api/v1/watchlists/{id}/stocks` - Add stock to watchlist
- `DELETE /api/v1/watchlists/{id}/stocks/{stock_id}` - Remove stock

#### Portfolios
- `GET /api/v1/portfolios` - List portfolios
- `POST /api/v1/portfolios` - Create portfolio
- `GET /api/v1/portfolios/{id}/positions` - Get positions
- `POST /api/v1/portfolios/{id}/transactions` - Record transaction

#### Analytics
- `GET /api/v1/analytics/{symbol}/moving-averages` - Get moving averages
- `GET /api/v1/analytics/{symbol}/momentum` - Get momentum indicators
- `GET /api/v1/analytics/{symbol}/trend` - Get trend indicators
- `GET /api/v1/analytics/{symbol}/volatility` - Get volatility indicators

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_user_service.py

# Run with verbose output
pytest -v
```

## Development

### Project Structure

```
stock_tracker/
├── app/
│   ├── api/              # API endpoints
│   │   └── v1/
│   │       └── endpoints/
│   ├── core/             # Core functionality
│   ├── models/           # Data models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── repositories/     # Data access layer
│   ├── workers/          # Celery tasks
│   └── utils/            # Utilities
├── config/               # Configuration
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker configuration
└── docker-compose.yml    # Docker Compose configuration
```

### Code Style

The project follows Python best practices:
- Type hints for all functions
- Comprehensive docstrings
- Clean code principles
- SOLID principles
- Repository pattern for data access
- Service layer for business logic

### Adding New Features

1. Define schemas in `app/schemas/`
2. Create repository in `app/repositories/`
3. Implement service in `app/services/`
4. Add API endpoints in `app/api/v1/endpoints/`
5. Write tests in `tests/`

## Background Tasks

The application uses Celery for background processing:

- **Price Updates**: Fetches latest prices every minute
- **Alert Checking**: Evaluates alerts every 30 seconds
- **Data Cleanup**: Removes old data daily at 2 AM

Monitor tasks with Flower: http://localhost:5555

## Performance Optimization

- **Caching**: Redis caches frequently accessed data
- **Database Indexing**: Optimized indexes for common queries
- **Connection Pooling**: MongoDB connection pooling
- **Async Operations**: Asynchronous I/O for better performance
- **Background Processing**: Heavy tasks offloaded to Celery workers

## Security

- JWT-based authentication
- Password hashing with bcrypt
- Rate limiting
- Input validation with Pydantic
- SQL injection prevention (MongoDB)
- CORS configuration
- Environment-based secrets

## Monitoring

- Health check endpoint: `/health`
- Celery task monitoring with Flower
- Structured logging
- Error tracking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License

## Support

For issues and questions:
- GitHub Issues: [Repository Issues](https://github.com/your-repo/issues)
- Documentation: http://localhost:8000/docs

## Roadmap

- [ ] Add cryptocurrency support
- [ ] Implement machine learning price predictions
- [ ] Add social sentiment analysis
- [ ] Create mobile app
- [ ] Add options trading analysis
- [ ] Implement backtesting engine
- [ ] Add news aggregation
- [ ] Support multiple currencies

## Acknowledgments

- FastAPI for the excellent web framework
- MongoDB for flexible data storage
- TA-Lib for technical analysis
- The open-source community
