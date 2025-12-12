# Stock API Example: Retrieving Stock Information

This example demonstrates how to retrieve stock information from the Stock Tracker API for a given ticker symbol.

## Example: Ford Motor Company (Symbol: F)

### API Endpoint

```
GET /api/v1/stocks/{symbol}
```

### Request

**Using curl:**
```bash
curl -X GET "http://localhost:8000/api/v1/stocks/F" \
  -H "Accept: application/json"
```

**Using Python requests:**
```python
import requests

response = requests.get("http://localhost:8000/api/v1/stocks/F")
stock_data = response.json()
print(stock_data)
```

**Using JavaScript fetch:**
```javascript
fetch('http://localhost:8000/api/v1/stocks/F')
  .then(response => response.json())
  .then(data => console.log(data));
```

### Raw Response

```json
{
  "id": "507f1f77bcf86cd799439011",
  "symbol": "F",
  "name": "Ford Motor Company",
  "exchange": "NYSE",
  "sector": "Consumer Cyclical",
  "industry": "Auto Manufacturers",
  "currency": "USD",
  "metadata": {
    "country": "United States",
    "website": "https://www.ford.com",
    "description": "Ford Motor Company designs, manufactures, markets, and services automobiles and trucks worldwide.",
    "employees": 173000,
    "market_cap": 42500000000
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-12-12T14:22:35Z"
}
```

---

## Getting Current Price Quote

### API Endpoint

```
GET /api/v1/stocks/{symbol}/quote
```

### Request

```bash
curl -X GET "http://localhost:8000/api/v1/stocks/F/quote" \
  -H "Accept: application/json"
```

### Raw Response

```json
{
  "symbol": "F",
  "current_price": 10.85,
  "change": 0.23,
  "percent_change": 2.17,
  "volume": 45230156,
  "open": 10.62,
  "high": 10.92,
  "low": 10.58,
  "previous_close": 10.62,
  "timestamp": "2024-12-12T16:00:00Z"
}
```

---

## Getting Historical Price Data

### API Endpoint

```
GET /api/v1/stocks/{symbol}/history?start_date={date}&end_date={date}
```

### Request

```bash
curl -X GET "http://localhost:8000/api/v1/stocks/F/history?start_date=2024-12-01&end_date=2024-12-10" \
  -H "Accept: application/json"
```

### Raw Response

```json
[
  {
    "id": "507f1f77bcf86cd799439101",
    "stock_id": "507f1f77bcf86cd799439011",
    "open": 10.45,
    "high": 10.68,
    "low": 10.32,
    "close": 10.55,
    "adjusted_close": 10.55,
    "volume": 38500000,
    "timestamp": "2024-12-02T00:00:00Z",
    "source": "YAHOO_FINANCE"
  },
  {
    "id": "507f1f77bcf86cd799439102",
    "stock_id": "507f1f77bcf86cd799439011",
    "open": 10.55,
    "high": 10.72,
    "low": 10.48,
    "close": 10.62,
    "adjusted_close": 10.62,
    "volume": 42100000,
    "timestamp": "2024-12-03T00:00:00Z",
    "source": "YAHOO_FINANCE"
  },
  {
    "id": "507f1f77bcf86cd799439103",
    "stock_id": "507f1f77bcf86cd799439011",
    "open": 10.60,
    "high": 10.85,
    "low": 10.52,
    "close": 10.78,
    "adjusted_close": 10.78,
    "volume": 51200000,
    "timestamp": "2024-12-04T00:00:00Z",
    "source": "YAHOO_FINANCE"
  }
]
```

---

## Error Responses

### Stock Not Found (404)

```bash
curl -X GET "http://localhost:8000/api/v1/stocks/INVALID"
```

```json
{
  "detail": "Stock not found"
}
```

### Invalid Request (422)

```json
{
  "detail": [
    {
      "loc": ["query", "start_date"],
      "msg": "invalid date format",
      "type": "value_error"
    }
  ]
}
```

---

## Response Field Descriptions

### Stock Details Response

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier for the stock record |
| `symbol` | string | Stock ticker symbol (e.g., "F") |
| `name` | string | Full company name |
| `exchange` | string | Stock exchange (NYSE, NASDAQ, AMEX, etc.) |
| `sector` | string | Business sector classification |
| `industry` | string | Specific industry within the sector |
| `currency` | string | Trading currency (e.g., "USD") |
| `metadata` | object | Additional company information |
| `created_at` | datetime | Record creation timestamp |
| `updated_at` | datetime | Last update timestamp |

### Quote Response

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | string | Stock ticker symbol |
| `current_price` | decimal | Latest trading price |
| `change` | decimal | Price change from previous close |
| `percent_change` | decimal | Percentage change from previous close |
| `volume` | integer | Trading volume for the day |
| `open` | decimal | Opening price |
| `high` | decimal | Day's high price |
| `low` | decimal | Day's low price |
| `previous_close` | decimal | Previous day's closing price |
| `timestamp` | datetime | Quote timestamp |
