# Day 024: API Authentication & Security

**Duration**: 2 hours | **Difficulty**: Intermediate-Advanced | **Prerequisites**: Day 001-023

---

## 📋 What You'll Build

- JWT (JSON Web Token) authentication
- User registration and login
- Password hashing with bcrypt
- Protected API endpoints
- API key generation
- Token refresh mechanism

---

## 💡 Why Authentication?

### Without Authentication:
```
❌ Anyone can access your API
❌ No usage tracking per user
❌ No rate limiting per user
❌ Security risk
❌ Can't monetize API access
```

### With Authentication:
```
✅ Secure API access
✅ Track usage per user
✅ Different access levels (admin, user, read-only)
✅ API keys for programmatic access
✅ Audit trail
```

---

## 💻 Implementation

### Step 1: Install Dependencies

```bash
pip install python-jose[cryptography]==3.3.0 passlib[bcrypt]==1.7.4 python-multipart==0.0.6
```

---

### Step 2: User Model

Add to `src/database/models.py`:

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
import secrets


class User(Base):
    """User account"""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    api_key = Column(String(64), unique=True, nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"

    @staticmethod
    def generate_api_key() -> str:
        """Generate random API key"""
        return secrets.token_urlsafe(32)
```

---

### Step 3: Authentication Module

Create `src/auth/auth.py`:

```python
"""
Authentication and Security
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.orm import Session
import os

from database.connection import get_db
from database.models import User

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# API Key scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# ============================================================================
# Password Utilities
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


# ============================================================================
# User Authentication
# ============================================================================

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""

    user = db.query(User).filter(User.username == username).first()

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    return user


# ============================================================================
# JWT Token
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    """Decode JWT token and return username"""

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None


# ============================================================================
# Dependencies (for FastAPI)
# ============================================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token"""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    username = decode_access_token(token)

    if username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    return current_user


async def verify_api_key(
    api_key: str = Depends(api_key_header),
    db: Session = Depends(get_db)
) -> User:
    """Verify API key"""

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )

    user = db.query(User).filter(User.api_key == api_key).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user
```

---

### Step 4: API Endpoints

Create `src/api/auth_routes.py`:

```python
"""
Authentication Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import timedelta

from database.connection import get_db
from database.models import User
from auth.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["authentication"])


# ============================================================================
# Schemas
# ============================================================================

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool
    api_key: str = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# ============================================================================
# Routes
# ============================================================================

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user"""

    # Check if username exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )

    # Check if email exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Create user
    hashed_password = get_password_hash(user_data.password)
    api_key = User.generate_api_key()

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        api_key=api_key
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get JWT token"""

    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user


@router.post("/api-key/regenerate")
async def regenerate_api_key(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Regenerate API key"""

    new_api_key = User.generate_api_key()
    current_user.api_key = new_api_key

    db.commit()
    db.refresh(current_user)

    return {
        "api_key": current_user.api_key,
        "message": "API key regenerated successfully"
    }
```

---

### Step 5: Protect Existing Endpoints

Update `src/api/main.py`:

```python
from auth.auth import get_current_active_user, verify_api_key
from auth.auth_routes import router as auth_router

# Include auth routes
app.include_router(auth_router)


# Protected endpoint example
@app.post("/api/v1/var/calculate-and-store")
async def calculate_and_store_var(
    ticker: str,
    position_value: float = 1000000,
    method: str = "historical",
    confidence_level: float = 0.95,
    current_user: User = Depends(get_current_active_user),  # ← Requires authentication
    db: Session = Depends(get_db)
):
    """Calculate VaR and store (PROTECTED)"""

    # ... (existing code)

    return {
        "ticker": ticker,
        "var_amount": var_record.var_amount,
        "user": current_user.username  # Track who made the request
    }


# API Key protected endpoint
@app.get("/api/v1/var/calculate/{ticker}")
async def calculate_var(
    ticker: str,
    user: User = Depends(verify_api_key)  # ← Requires API key
):
    """Calculate VaR using API key"""

    # ... (existing code)

    return {
        "ticker": ticker,
        "var_amount": result['VaR'],
        "api_user": user.username
    }
```

---

## 🧪 Test with curl

### Step 1: Register User

```bash
# Register new user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_trader",
    "email": "john@example.com",
    "password": "SecurePassword123!"
  }' | jq '.'
```

**Expected:**
```json
{
  "id": 1,
  "username": "john_trader",
  "email": "john@example.com",
  "is_active": true,
  "is_admin": false,
  "api_key": "xK9mP4nQ8rT2vW6yZ3cF5hJ7kL0mN4pR"
}
```

**Save the API key!**

---

### Step 2: Login and Get Token

```bash
# Login
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john_trader&password=SecurePassword123!" \
  | jq '.'
```

**Expected:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Save the token!**

```bash
# Set token as environment variable for easy reuse
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### Step 3: Access Protected Endpoints with JWT

```bash
# Get current user info (requires token)
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

**Expected:**
```json
{
  "id": 1,
  "username": "john_trader",
  "email": "john@example.com",
  "is_active": true,
  "is_admin": false,
  "api_key": "xK9mP4nQ8rT2vW6yZ3cF5hJ7kL0mN4pR"
}
```

```bash
# Calculate and store VaR (protected endpoint)
curl -X POST "http://localhost:8000/api/v1/var/calculate-and-store" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "method": "historical"
  }' | jq '.'
```

---

### Step 4: Access with API Key

```bash
# Set API key
export API_KEY="xK9mP4nQ8rT2vW6yZ3cF5hJ7kL0mN4pR"

# Use API key for authentication
curl -X GET "http://localhost:8000/api/v1/var/calculate/AAPL" \
  -H "X-API-Key: $API_KEY" \
  | jq '.'
```

**Expected:**
```json
{
  "ticker": "AAPL",
  "var_amount": 28456.78,
  "api_user": "john_trader"
}
```

---

### Step 5: Test Authentication Failures

```bash
# Without token (should fail)
curl -X GET "http://localhost:8000/auth/me"
```

**Expected:**
```json
{
  "detail": "Not authenticated"
}
```

```bash
# Invalid token (should fail)
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer invalid_token"
```

**Expected:**
```json
{
  "detail": "Could not validate credentials"
}
```

```bash
# Invalid API key (should fail)
curl -X GET "http://localhost:8000/api/v1/var/calculate/AAPL" \
  -H "X-API-Key: invalid_key"
```

**Expected:**
```json
{
  "detail": "Invalid API key"
}
```

---

### Step 6: Regenerate API Key

```bash
# Regenerate API key
curl -X POST "http://localhost:8000/auth/api-key/regenerate" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

**Expected:**
```json
{
  "api_key": "bN5qR8tU1wY4zA7cE0fH3jK6mP9sV2xZ",
  "message": "API key regenerated successfully"
}
```

---

## 🔒 Security Best Practices

### 1. Use Strong Secret Key

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set in environment
export SECRET_KEY="your-generated-secret-key"
```

### 2. Use HTTPS in Production

```bash
# Never send tokens over HTTP in production!
# Always use HTTPS to encrypt traffic
```

### 3. Set Strong Password Requirements

```python
# Add to registration
import re

def validate_password(password: str):
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain lowercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain digit")
```

---

## 🧪 Complete Authentication Workflow

```bash
#!/bin/bash
# Complete authentication test

echo "=== 1. Register User ==="
REGISTER_RESPONSE=$(curl -s -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "email": "test@example.com",
    "password": "TestPassword123!"
  }')

echo $REGISTER_RESPONSE | jq '.username, .api_key'

echo -e "\n=== 2. Login ==="
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test_user&password=TestPassword123!")

TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')
echo "Token: ${TOKEN:0:20}..."

echo -e "\n=== 3. Get User Info ==="
curl -s -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{username, email, is_active}'

echo -e "\n=== 4. Calculate VaR (Protected) ==="
curl -s -X POST "http://localhost:8000/api/v1/var/calculate-and-store" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}' \
  | jq '{ticker, var_amount, user}'
```

---

## ✅ Completed

✅ JWT authentication with tokens
✅ User registration and login
✅ Password hashing with bcrypt
✅ Protected API endpoints
✅ API key authentication
✅ Token-based and API key-based access
✅ curl-based testing

**Next**: Rate Limiting & Caching (Day 025)
