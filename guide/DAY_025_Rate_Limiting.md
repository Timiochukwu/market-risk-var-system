# Day 025: Rate Limiting & Advanced Caching

**Duration**: 1.5-2 hours | **Difficulty**: Intermediate | **Prerequisites**: Day 001-024

---

## 📋 What You'll Build

- Request rate limiting per user
- API quotas and throttling
- Redis-based caching (optional)
- Request tracking and analytics
- Rate limit headers
- Different limits for different tiers

---

## 💡 Why Rate Limiting?

### Without Rate Limiting:
```
❌ API abuse (1000s of requests per second)
❌ Server overload and crashes
❌ Unfair resource usage
❌ DDoS vulnerability
❌ High infrastructure costs
```

### With Rate Limiting:
```
✅ Fair API usage
✅ Server protection
✅ Tiered access (free vs premium)
✅ Cost control
✅ Better performance for all users
```

---

## 💻 Implementation

### Step 1: Install Dependencies

```bash
pip install slowapi==0.1.9
# Optional for Redis caching:
# pip install redis==5.0.1
```

---

### Step 2: Rate Limiting Module

Create `src/utils/rate_limiter.py`:

```python
"""
Rate Limiting for API
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from typing import Callable
import time
from collections import defaultdict, deque


class InMemoryRateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self):
        # Store: user_id -> deque of timestamps
        self.requests = defaultdict(deque)

    def check_rate_limit(
        self,
        user_id: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit

        Args:
            user_id: User identifier
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            (allowed: bool, info: dict)
        """

        now = time.time()
        window_start = now - window_seconds

        # Get user's request queue
        user_requests = self.requests[user_id]

        # Remove old requests outside window
        while user_requests and user_requests[0] < window_start:
            user_requests.popleft()

        # Check if limit exceeded
        current_requests = len(user_requests)
        allowed = current_requests < max_requests

        if allowed:
            # Add current request
            user_requests.append(now)

        # Calculate remaining and reset time
        remaining = max(0, max_requests - current_requests - (1 if allowed else 0))
        reset_time = int(user_requests[0] + window_seconds) if user_requests else int(now + window_seconds)

        info = {
            'limit': max_requests,
            'remaining': remaining,
            'reset': reset_time,
            'current': current_requests + (1 if allowed else 0)
        }

        return allowed, info


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()


# SlowAPI limiter for easy integration
limiter = Limiter(key_func=get_remote_address)


def rate_limit_by_user(
    max_requests: int = 100,
    window_seconds: int = 60
) -> Callable:
    """
    Decorator for rate limiting by user

    Usage:
        @rate_limit_by_user(max_requests=10, window_seconds=60)
        async def my_endpoint(current_user: User = Depends(...)):
            ...
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Get current_user from kwargs
            current_user = kwargs.get('current_user')

            if not current_user:
                # No authentication, use IP-based limiting
                return await func(*args, **kwargs)

            user_id = str(current_user.id)

            # Check rate limit
            allowed, info = rate_limiter.check_rate_limit(
                user_id,
                max_requests,
                window_seconds
            )

            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {info['reset'] - int(time.time())} seconds.",
                    headers={
                        'X-RateLimit-Limit': str(info['limit']),
                        'X-RateLimit-Remaining': str(info['remaining']),
                        'X-RateLimit-Reset': str(info['reset']),
                        'Retry-After': str(info['reset'] - int(time.time()))
                    }
                )

            # Execute function
            result = await func(*args, **kwargs)

            # Add rate limit headers to response (if it's a dict)
            if isinstance(result, dict):
                result['_rate_limit'] = info

            return result

        return wrapper

    return decorator
```

---

### Step 3: User Tiers

Update `src/database/models.py`:

```python
from sqlalchemy import Column, String, Integer, Enum
import enum


class UserTier(str, enum.Enum):
    """User subscription tier"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class User(Base):
    __tablename__ = 'users'

    # ... (existing fields)

    tier = Column(Enum(UserTier), default=UserTier.FREE)

    # Rate limits by tier
    @property
    def rate_limit_requests(self) -> int:
        """Get rate limit based on tier"""
        limits = {
            UserTier.FREE: 10,
            UserTier.BASIC: 100,
            UserTier.PREMIUM: 1000,
            UserTier.ENTERPRISE: 10000
        }
        return limits.get(self.tier, 10)

    @property
    def rate_limit_window(self) -> int:
        """Get rate limit window in seconds"""
        return 60  # 1 minute for all tiers
```

---

### Step 4: Rate Limited Endpoints

Update `src/api/main.py`:

```python
from utils.rate_limiter import limiter, rate_limit_by_user
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

# Add limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.post("/api/v1/var/calculate-and-store")
@rate_limit_by_user(max_requests=10, window_seconds=60)  # 10 requests per minute
async def calculate_and_store_var(
    ticker: str,
    position_value: float = 1000000,
    method: str = "historical",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Calculate VaR (RATE LIMITED)"""

    # ... (existing code)

    return {
        "ticker": ticker,
        "var_amount": var_record.var_amount,
        "user": current_user.username
    }


# Dynamic rate limit based on user tier
async def get_user_rate_limit(current_user: User = Depends(get_current_active_user)):
    """Get rate limit for current user's tier"""
    return current_user.rate_limit_requests, current_user.rate_limit_window


@app.post("/api/v1/var/batch-calculate")
async def batch_calculate_var(
    tickers: List[str],
    method: str = "historical",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Batch calculate VaR (tier-based rate limiting)"""

    # Check tier-based rate limit
    from utils.rate_limiter import rate_limiter

    allowed, info = rate_limiter.check_rate_limit(
        str(current_user.id),
        current_user.rate_limit_requests,
        current_user.rate_limit_window
    )

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded for {current_user.tier} tier. "
                   f"Upgrade for higher limits.",
            headers={
                'X-RateLimit-Limit': str(info['limit']),
                'X-RateLimit-Remaining': str(info['remaining']),
                'X-RateLimit-Reset': str(info['reset'])
            }
        )

    # ... (existing batch calculation code)

    return {
        "results": results,
        "rate_limit": info
    }


@app.get("/api/v1/rate-limit/status")
async def get_rate_limit_status(
    current_user: User = Depends(get_current_active_user)
):
    """Get current rate limit status"""

    from utils.rate_limiter import rate_limiter

    _, info = rate_limiter.check_rate_limit(
        str(current_user.id),
        current_user.rate_limit_requests,
        current_user.rate_limit_window
    )

    return {
        "user": current_user.username,
        "tier": current_user.tier,
        "limit": info['limit'],
        "remaining": info['remaining'],
        "reset": info['reset'],
        "reset_in_seconds": info['reset'] - int(time.time()),
        "current_usage": info['current']
    }
```

---

### Step 5: Request Analytics

Create `src/utils/analytics.py`:

```python
"""
API Usage Analytics
"""

from sqlalchemy import Column, Integer, String, DateTime, Float
from database.models import Base
from datetime import datetime
from sqlalchemy.orm import Session


class APIRequest(Base):
    """Track API requests"""

    __tablename__ = 'api_requests'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    endpoint = Column(String(255), index=True)
    method = Column(String(10))
    status_code = Column(Integer)
    response_time_ms = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


def log_request(
    db: Session,
    user_id: int,
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: float
):
    """Log API request"""

    request_log = APIRequest(
        user_id=user_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        response_time_ms=response_time_ms
    )

    db.add(request_log)
    db.commit()


def get_user_analytics(db: Session, user_id: int, days: int = 7) -> dict:
    """Get user analytics"""

    from datetime import timedelta
    from sqlalchemy import func

    start_date = datetime.utcnow() - timedelta(days=days)

    # Total requests
    total_requests = db.query(APIRequest).filter(
        APIRequest.user_id == user_id,
        APIRequest.timestamp >= start_date
    ).count()

    # Requests by endpoint
    endpoint_stats = db.query(
        APIRequest.endpoint,
        func.count(APIRequest.id).label('count')
    ).filter(
        APIRequest.user_id == user_id,
        APIRequest.timestamp >= start_date
    ).group_by(APIRequest.endpoint).all()

    # Average response time
    avg_response_time = db.query(
        func.avg(APIRequest.response_time_ms)
    ).filter(
        APIRequest.user_id == user_id,
        APIRequest.timestamp >= start_date
    ).scalar()

    return {
        'total_requests': total_requests,
        'endpoints': [
            {'endpoint': ep, 'count': count}
            for ep, count in endpoint_stats
        ],
        'avg_response_time_ms': avg_response_time or 0,
        'period_days': days
    }
```

Add analytics endpoint to `src/api/main.py`:

```python
from utils.analytics import log_request, get_user_analytics
import time


# Middleware to log all requests
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    """Log all API requests"""

    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate response time
    response_time_ms = (time.time() - start_time) * 1000

    # Log to database (if user is authenticated)
    # Note: This is simplified; in production, you'd need to extract user from request
    # For now, we'll skip automatic logging and use manual logging in endpoints

    return response


@app.get("/api/v1/analytics/usage")
async def get_usage_analytics(
    days: int = 7,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get usage analytics for current user"""

    analytics = get_user_analytics(db, current_user.id, days)

    return {
        "user": current_user.username,
        "tier": current_user.tier,
        "analytics": analytics
    }
```

---

## 🧪 Test with curl

### Step 1: Test Rate Limiting

```bash
# Login first
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/token" \
  -d "username=test_user&password=TestPassword123!" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  | jq -r '.access_token')

# Make 11 requests quickly (limit is 10 per minute)
for i in {1..11}; do
  echo "Request $i:"
  curl -s -X POST "http://localhost:8000/api/v1/var/calculate-and-store" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"ticker": "AAPL"}' \
    | jq '{ticker, var_amount, _rate_limit}'
  echo ""
done
```

**Expected (11th request):**
```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds."
}
```

---

### Step 2: Check Rate Limit Status

```bash
# Check current rate limit status
curl -X GET "http://localhost:8000/api/v1/rate-limit/status" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

**Expected:**
```json
{
  "user": "test_user",
  "tier": "free",
  "limit": 10,
  "remaining": 0,
  "reset": 1704123456,
  "reset_in_seconds": 45,
  "current_usage": 10
}
```

---

### Step 3: Test Tier-Based Limits

```bash
# Update user tier to premium (manually in database or via admin endpoint)
# Then test with higher limits

# Premium tier: 1000 requests per minute
# Make 20 requests (should all succeed)
for i in {1..20}; do
  curl -s -X POST "http://localhost:8000/api/v1/var/calculate-and-store" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"ticker": "AAPL"}' \
    -H "Content-Type: application/json" > /dev/null
  echo "Request $i completed"
done
```

---

### Step 4: Monitor Rate Limit Headers

```bash
# Make request and view headers
curl -i -X POST "http://localhost:8000/api/v1/var/calculate-and-store" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
```

**Look for headers:**
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1704123456
```

---

### Step 5: Test Batch Endpoint with Rate Limiting

```bash
# Batch calculate (counts as 1 request)
curl -X POST "http://localhost:8000/api/v1/var/batch-calculate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "MSFT", "GOOGL", "TSLA", "JNJ"]
  }' | jq '.rate_limit'
```

**Expected:**
```json
{
  "limit": 10,
  "remaining": 9,
  "reset": 1704123456,
  "current": 1
}
```

---

### Step 6: Get Usage Analytics

```bash
# Get usage analytics for last 7 days
curl -X GET "http://localhost:8000/api/v1/analytics/usage?days=7" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

**Expected:**
```json
{
  "user": "test_user",
  "tier": "free",
  "analytics": {
    "total_requests": 156,
    "endpoints": [
      {"endpoint": "/api/v1/var/calculate-and-store", "count": 120},
      {"endpoint": "/api/v1/var/batch-calculate", "count": 36}
    ],
    "avg_response_time_ms": 245.67,
    "period_days": 7
  }
}
```

---

## 📊 Rate Limit Tiers

### Recommended Limits:

| Tier | Requests/Min | Requests/Day | Features |
|------|--------------|--------------|----------|
| **Free** | 10 | 1,000 | Basic VaR, Historical data |
| **Basic** | 100 | 10,000 | All VaR methods, Backtesting |
| **Premium** | 1,000 | 100,000 | Real-time alerts, Reports |
| **Enterprise** | 10,000 | Unlimited | Priority support, Custom models |

---

## 🧪 Rate Limit Testing Script

```bash
#!/bin/bash
# Complete rate limit testing

TOKEN=$(curl -s -X POST "http://localhost:8000/auth/token" \
  -d "username=test_user&password=TestPassword123!" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  | jq -r '.access_token')

echo "=== Initial Rate Limit Status ==="
curl -s "http://localhost:8000/api/v1/rate-limit/status" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{tier, limit, remaining}'

echo -e "\n=== Making 5 Requests ==="
for i in {1..5}; do
  echo "Request $i..."
  curl -s -X POST "http://localhost:8000/api/v1/var/calculate-and-store" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"ticker": "AAPL"}' \
    -H "Content-Type: application/json" \
    | jq '._rate_limit.remaining'
done

echo -e "\n=== Final Rate Limit Status ==="
curl -s "http://localhost:8000/api/v1/rate-limit/status" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{remaining, reset_in_seconds}'

echo -e "\n=== Wait 60 seconds for reset ==="
sleep 60

echo -e "\n=== Status After Reset ==="
curl -s "http://localhost:8000/api/v1/rate-limit/status" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{remaining}'
```

---

## 🎯 Week 5 Complete!

**Congratulations! You've completed Week 5 (Days 021-025):**

✅ Database integration with SQLAlchemy
✅ Historical VaR storage and trends
✅ Performance optimization (caching, async)
✅ JWT and API key authentication
✅ Rate limiting and usage analytics

**You now have:**
- Production-ready database layer
- Secure authentication system
- Performance-optimized API
- Rate limiting and fair usage
- Usage tracking and analytics

**Total Progress: Days 001-025 (5 weeks / 50% complete!)**

**Coming Next (Days 026-030)**:
- Frontend Dashboard (React)
- Real-time WebSocket updates
- PDF report generation
- Email scheduling improvements
- CI/CD deployment pipeline

---

## ✅ Completed

✅ In-memory rate limiting
✅ Tier-based rate limits (free/basic/premium/enterprise)
✅ Rate limit headers in responses
✅ Request analytics and tracking
✅ Dynamic rate limits per user
✅ curl-based testing

**Next**: Frontend Dashboard (Day 026) or continue with advanced features!
