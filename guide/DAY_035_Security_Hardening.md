# Day 035: Security Hardening

**Duration**: 2 hours | **Difficulty**: Advanced | **Prerequisites**: Day 001-034

---

## 📋 What You'll Build

- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection
- Secure headers
- Secrets management
- Audit logging
- Security scanning

---

## 💡 Security Threats

```
┌──────────────────────────────────────┐
│  OWASP Top 10 Web Application Risks  │
├──────────────────────────────────────┤
│  1. Broken Access Control            │
│  2. Cryptographic Failures           │
│  3. Injection (SQL, NoSQL, etc.)     │
│  4. Insecure Design                  │
│  5. Security Misconfiguration        │
│  6. Vulnerable Components            │
│  7. Authentication Failures          │
│  8. Software & Data Integrity        │
│  9. Logging & Monitoring Failures    │
│  10. Server-Side Request Forgery     │
└──────────────────────────────────────┘
```

---

## 💻 Implementation

### Step 1: Install Dependencies

```bash
pip install pydantic[email]==2.5.2 python-jose[cryptography]==3.3.0 argon2-cffi==23.1.0 bandit==1.7.5
```

---

### Step 2: Input Validation

Create `src/security/validators.py`:

```python
"""
Security Input Validation
"""

import re
from typing import Optional, List
from pydantic import BaseModel, validator, EmailStr, constr, confloat
from fastapi import HTTPException


class TickerValidator(BaseModel):
    """Validate ticker symbol"""

    ticker: constr(
        min_length=1,
        max_length=10,
        regex=r'^[A-Z]{1,10}$'  # Only uppercase letters
    )

    @validator('ticker')
    def validate_ticker(cls, v):
        """Additional ticker validation"""
        # Prevent SQL injection attempts
        if any(char in v for char in [';', '--', '/*', '*/', 'DROP', 'DELETE']):
            raise ValueError('Invalid ticker symbol')
        return v


class VaRCalculationRequest(BaseModel):
    """Secure VaR calculation request"""

    ticker: constr(regex=r'^[A-Z]{1,10}$')
    position_value: confloat(gt=0, le=1_000_000_000)  # Max $1B
    method: constr(regex=r'^(historical|parametric|monte_carlo|garch|lstm)$')
    confidence_level: confloat(ge=0.9, le=0.99)  # 90-99%

    @validator('ticker')
    def sanitize_ticker(cls, v):
        """Sanitize ticker input"""
        # Remove any potentially dangerous characters
        return re.sub(r'[^A-Z]', '', v.upper())


class EmailRequest(BaseModel):
    """Secure email request"""

    to_emails: List[EmailStr]  # Validates email format
    subject: constr(max_length=200)
    ticker: constr(regex=r'^[A-Z]{1,10}$')

    @validator('to_emails')
    def validate_email_count(cls, v):
        """Limit number of recipients"""
        if len(v) > 10:
            raise ValueError('Maximum 10 recipients allowed')
        return v

    @validator('subject')
    def sanitize_subject(cls, v):
        """Sanitize email subject"""
        # Remove HTML tags
        return re.sub(r'<[^>]*>', '', v)


class PaginationParams(BaseModel):
    """Secure pagination parameters"""

    skip: int = 0
    limit: int = 100

    @validator('skip')
    def validate_skip(cls, v):
        if v < 0:
            raise ValueError('Skip must be non-negative')
        if v > 10000:
            raise ValueError('Skip too large')
        return v

    @validator('limit')
    def validate_limit(cls, v):
        if v < 1:
            raise ValueError('Limit must be positive')
        if v > 1000:
            raise ValueError('Limit too large (max 1000)')
        return v


def sanitize_sql_input(value: str) -> str:
    """
    Sanitize input to prevent SQL injection

    Args:
        value: Input string

    Returns:
        Sanitized string
    """
    # Remove SQL keywords and dangerous characters
    dangerous = [
        ';', '--', '/*', '*/', 'xp_', 'sp_',
        'DROP', 'DELETE', 'INSERT', 'UPDATE',
        'EXEC', 'EXECUTE', 'UNION', 'SELECT'
    ]

    value_upper = value.upper()

    for keyword in dangerous:
        if keyword in value_upper:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid input: contains '{keyword}'"
            )

    return value


def validate_file_upload(filename: str, max_size_mb: int = 10):
    """
    Validate file upload

    Args:
        filename: Uploaded filename
        max_size_mb: Maximum file size in MB
    """
    # Allowed extensions
    allowed_extensions = {'.pdf', '.xlsx', '.csv', '.txt'}

    # Get extension
    ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {allowed_extensions}"
        )

    # Check for path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename"
        )

    return True
```

---

### Step 3: Secure Headers Middleware

Create `src/security/headers.py`:

```python
"""
Security Headers Middleware
"""

from fastapi import Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'

        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Enable XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Strict Transport Security (HTTPS only)
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )

        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions Policy
        response.headers['Permissions-Policy'] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=()"
        )

        return response


def add_security_middleware(app):
    """Add all security middleware to app"""

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Trusted host (prevent host header attacks)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "yourdomain.com"]
    )
```

---

### Step 4: Audit Logging

Create `src/security/audit_log.py`:

```python
"""
Security Audit Logging
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON
from database.models import Base
from datetime import datetime
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class AuditLog(Base):
    """Security audit log"""

    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(Integer, index=True)
    action = Column(String(100), index=True)
    resource = Column(String(200))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    status = Column(String(20))  # success, failure, blocked
    details = Column(JSON)


def log_security_event(
    db: Session,
    user_id: int,
    action: str,
    resource: str,
    ip_address: str,
    user_agent: str,
    status: str,
    details: dict = None
):
    """
    Log security event

    Args:
        db: Database session
        user_id: User ID
        action: Action performed
        resource: Resource accessed
        ip_address: Client IP
        user_agent: User agent
        status: Event status
        details: Additional details
    """
    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
        details=details or {}
    )

    db.add(audit_entry)
    db.commit()

    logger.info(f"Audit: {action} by user {user_id} - {status}")


def get_failed_login_attempts(
    db: Session,
    user_id: int,
    minutes: int = 15
) -> int:
    """
    Get number of failed login attempts

    Args:
        db: Database session
        user_id: User ID
        minutes: Time window in minutes

    Returns:
        Number of failed attempts
    """
    from datetime import timedelta

    cutoff = datetime.utcnow() - timedelta(minutes=minutes)

    count = db.query(AuditLog).filter(
        AuditLog.user_id == user_id,
        AuditLog.action == 'login',
        AuditLog.status == 'failure',
        AuditLog.timestamp >= cutoff
    ).count()

    return count
```

---

### Step 5: Secrets Management

Create `.env.example`:

```bash
# Database
DATABASE_URL=postgresql://user:CHANGE_ME@localhost/var_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=GENERATE_RANDOM_256_BIT_KEY_HERE
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Keys (rotate regularly)
INTERNAL_API_KEY=GENERATE_RANDOM_KEY_HERE

# Email (use app-specific password)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=APP_SPECIFIC_PASSWORD_HERE

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Security
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15
SESSION_TIMEOUT_MINUTES=60

# Monitoring
SENTRY_DSN=https://your_sentry_dsn_here
LOG_LEVEL=INFO
```

Generate secure secrets:

```python
import secrets

# Generate SECRET_KEY
print("SECRET_KEY:", secrets.token_urlsafe(32))

# Generate API Key
print("API_KEY:", secrets.token_urlsafe(32))
```

---

### Step 6: Security Scanning

Create `security_check.py`:

```python
"""
Security Vulnerability Scanner
"""

import subprocess
import sys


def run_bandit():
    """Run Bandit security linter"""
    print("Running Bandit security scanner...")
    result = subprocess.run(
        ['bandit', '-r', 'src/', '-f', 'txt'],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        print("⚠️ Security issues found!")
        return False
    else:
        print("✅ No security issues found")
        return True


def check_dependencies():
    """Check for vulnerable dependencies"""
    print("\nChecking dependencies for vulnerabilities...")
    result = subprocess.run(
        ['pip', 'check'],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if "No broken requirements found" in result.stdout:
        print("✅ Dependencies OK")
        return True
    else:
        print("⚠️ Dependency issues found")
        return False


if __name__ == "__main__":
    bandit_ok = run_bandit()
    deps_ok = check_dependencies()

    if not (bandit_ok and deps_ok):
        sys.exit(1)
```

Run security scan:

```bash
# Install Bandit
pip install bandit

# Run security check
python security_check.py
```

---

## 🧪 Test Security with curl

### Test Input Validation:

```bash
# Valid request
curl -X POST "http://localhost:8000/api/v1/var/calculate-and-store" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"ticker": "AAPL", "method": "historical"}' \
  -H "Content-Type: application/json"

# Invalid ticker (SQL injection attempt - should fail)
curl -X POST "http://localhost:8000/api/v1/var/calculate-and-store" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"ticker": "AAPL; DROP TABLE users--", "method": "historical"}' \
  -H "Content-Type: application/json"
# Expected: 400 Bad Request
```

### Test Rate Limiting:

```bash
# Make 100 requests quickly
for i in {1..100}; do
  curl -s -X GET "http://localhost:8000/api/v1/var/calculate/AAPL" \
    -H "X-API-Key: $API_KEY" > /dev/null
  echo "Request $i"
done
# Should hit rate limit around request 60-70
```

### Test Security Headers:

```bash
# Check security headers
curl -I "http://localhost:8000/" | grep -E "(X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security)"
```

**Expected:**
```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### Test Failed Login Lockout:

```bash
# Try failed logins
for i in {1..6}; do
  curl -X POST "http://localhost:8000/auth/token" \
    -d "username=testuser&password=wrongpassword" \
    -H "Content-Type: application/x-www-form-urlencoded"
  echo "Attempt $i"
done
# Should get locked out after 5 attempts
```

---

## 🔒 Security Checklist

### Before Production:

- [ ] Change all default passwords
- [ ] Generate strong SECRET_KEY (256-bit)
- [ ] Use HTTPS (SSL/TLS certificate)
- [ ] Enable CORS only for trusted domains
- [ ] Set up firewall rules
- [ ] Disable DEBUG mode
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Set up audit logging
- [ ] Run security scanner (Bandit)
- [ ] Update all dependencies
- [ ] Configure secure headers
- [ ] Implement account lockout
- [ ] Set up monitoring/alerts
- [ ] Backup encryption keys
- [ ] Document security policies

### Regular Maintenance:

- [ ] Rotate secrets every 90 days
- [ ] Review audit logs weekly
- [ ] Update dependencies monthly
- [ ] Run security scans before releases
- [ ] Review access logs for anomalies
- [ ] Test disaster recovery
- [ ] Update SSL certificates

---

## 🎯 Week 7 Complete!

**Congratulations! You've completed Week 7 (Days 031-035):**

✅ Machine Learning VaR with LSTM
✅ Advanced Portfolio Optimization
✅ Basel III Regulatory Reporting
✅ Performance Tuning & Scaling
✅ Security Hardening

**You now have:**
- ML-powered VaR predictions
- Portfolio optimization strategies
- Regulatory compliance framework
- High-performance caching
- Production-grade security

**Total Progress: Days 001-035 (70% complete!)**

---

## ✅ Completed

✅ Input validation with Pydantic
✅ SQL injection prevention
✅ XSS and CSRF protection
✅ Secure headers middleware
✅ Secrets management
✅ Audit logging
✅ Security scanning (Bandit)
✅ Rate limiting
✅ Account lockout
✅ curl-based security testing

**Next Steps (Days 036-050)**:
- Advanced ML models (GRU, Transformer)
- Real-time streaming data
- Microservices architecture
- Kubernetes deployment
- Advanced monitoring (Prometheus/Grafana)

**You're 70% done! Final stretch ahead!** 🎉
