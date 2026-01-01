# Day 030: CI/CD & Deployment

**Duration**: 2-2.5 hours | **Difficulty**: Intermediate-Advanced | **Prerequisites**: Day 001-029

---

## 📋 What You'll Build

- Docker containerization
- Docker Compose for multi-service
- GitHub Actions CI/CD pipeline
- Automated testing
- Deployment to cloud (DigitalOcean/AWS)
- Environment configuration

---

## 💡 Deployment Strategy

```
┌─────────────────────────────────────────┐
│  Development                             │
│  - Local development                     │
│  - Feature branches                      │
└──────────────┬──────────────────────────┘
               │ git push
               ▼
┌─────────────────────────────────────────┐
│  GitHub Actions CI/CD                    │
│  1. Run tests                            │
│  2. Build Docker image                   │
│  3. Push to registry                     │
│  4. Deploy to production                 │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Production (Cloud)                      │
│  - Docker containers                     │
│  - PostgreSQL database                   │
│  - Nginx reverse proxy                   │
│  - Auto-scaling                          │
└─────────────────────────────────────────┘
```

---

## 💻 Implementation

### Step 1: Dockerfile

Create `Dockerfile`:

```dockerfile
# Multi-stage build for smaller image
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================
# Final stage
# ============================================
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src/ /app/src/
COPY .env.example /app/.env

# Create non-root user
RUN useradd -m -u 1000 varuser && \
    chown -R varuser:varuser /app

USER varuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "src.api.main:socket_app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `.dockerignore`:

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.gitignore
.mypy_cache
.pytest_cache
.hypothesis
*.db
*.sqlite
var_system.db
```

---

### Step 2: Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: var_postgres
    environment:
      POSTGRES_DB: var_system
      POSTGRES_USER: var_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U var_user -d var_system"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis (for caching)
  redis:
    image: redis:7-alpine
    container_name: var_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI Application
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: var_api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://var_user:${POSTGRES_PASSWORD:-changeme}@postgres:5432/var_system
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY:-your-secret-key-change-in-production}
      SMTP_HOST: ${SMTP_HOST}
      SMTP_PORT: ${SMTP_PORT}
      SMTP_USER: ${SMTP_USER}
      SMTP_PASSWORD: ${SMTP_PASSWORD}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./src:/app/src  # For development hot-reload
    restart: unless-stopped

  # Nginx Reverse Proxy (Optional - for production)
  nginx:
    image: nginx:alpine
    container_name: var_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro  # SSL certificates
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

---

### Step 3: Environment Configuration

Create `.env.example`:

```bash
# Database
DATABASE_URL=postgresql://var_user:changeme@localhost:5432/var_system

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=generate-a-secure-random-key-here

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com

# Application
DEBUG=False
LOG_LEVEL=INFO

# API Configuration
API_TITLE=Market Risk VaR API
API_VERSION=1.0.0
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

---

### Step 4: GitHub Actions CI/CD

Create `.github/workflows/ci-cd.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  # ==========================================
  # Test Job
  # ==========================================
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: var_system_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run linting
        run: |
          pip install flake8
          flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics

      - name: Run tests
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/var_system_test
          SECRET_KEY: test-secret-key
        run: |
          pytest tests/ -v --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: false

  # ==========================================
  # Build and Push Docker Image
  # ==========================================
  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            ${{ secrets.DOCKER_USERNAME }}/var-system:latest
            ${{ secrets.DOCKER_USERNAME }}/var-system:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ==========================================
  # Deploy to Production (Optional)
  # ==========================================
  deploy:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/var-system
            docker-compose pull
            docker-compose up -d --force-recreate
            docker system prune -af
```

---

### Step 5: Health Check Endpoint

Add to `src/api/main.py`:

```python
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint for monitoring"""

    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {}
    }

    # Check database
    try:
        db.execute("SELECT 1")
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)}"

    # Check cache
    try:
        from utils.cache import cache
        cache.set("health_check", "ok", ttl=10)
        value = cache.get("health_check")
        health_status["checks"]["cache"] = "ok" if value == "ok" else "error"
    except Exception as e:
        health_status["checks"]["cache"] = f"error: {str(e)}"

    # Return 503 if unhealthy
    status_code = 200 if health_status["status"] == "healthy" else 503

    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Market Risk VaR API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
```

---

## 🧪 Test Locally with Docker

### Build and Run:

```bash
# Build Docker image
docker build -t var-system:latest .

# Run single container
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./var_system.db \
  var-system:latest

# Test health check
curl http://localhost:8000/health | jq '.'
```

**Expected:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-01T10:30:00",
  "version": "1.0.0",
  "checks": {
    "database": "ok",
    "cache": "ok"
  }
}
```

### Run with Docker Compose:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Check status
docker-compose ps

# Test API
curl http://localhost:8000/health | jq '.'

# Stop services
docker-compose down
```

---

## 🚀 Deploy to Cloud

### Option 1: DigitalOcean

```bash
# 1. Create Droplet (Ubuntu 22.04)
# 2. SSH into server
ssh root@your-server-ip

# 3. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 4. Install Docker Compose
apt install docker-compose

# 5. Clone repository
git clone https://github.com/yourusername/market-risk-var-system.git
cd market-risk-var-system

# 6. Create .env file
cp .env.example .env
nano .env  # Edit with production values

# 7. Start services
docker-compose up -d

# 8. Check logs
docker-compose logs -f
```

### Option 2: AWS EC2

```bash
# Similar process on AWS EC2
# 1. Launch EC2 instance (Ubuntu)
# 2. Configure security groups (port 80, 443, 8000)
# 3. SSH and install Docker
# 4. Deploy with Docker Compose
```

---

## 🧪 Test Deployment with curl

```bash
# Test health endpoint
curl https://yourdomain.com/health | jq '.'

# Test API
curl https://yourdomain.com/api/v1/var/calculate/AAPL \
  -H "X-API-Key: $API_KEY" | jq '.'

# Test with authentication
curl -X POST https://yourdomain.com/auth/token \
  -d "username=testuser&password=testpass" \
  -H "Content-Type: application/x-www-form-urlencoded" | jq '.'
```

---

## 📊 Deployment Checklist

### Before Deployment:
- [ ] Update SECRET_KEY to random secure value
- [ ] Configure production database (PostgreSQL)
- [ ] Set up SMTP credentials
- [ ] Configure CORS origins
- [ ] Set DEBUG=False
- [ ] Create .env file with production values
- [ ] Set up SSL certificates (Let's Encrypt)
- [ ] Configure firewall rules
- [ ] Set up backup strategy

### After Deployment:
- [ ] Test health endpoint
- [ ] Test API endpoints
- [ ] Check logs for errors
- [ ] Monitor resource usage
- [ ] Set up monitoring (e.g., Prometheus, Grafana)
- [ ] Configure auto-restart on failure
- [ ] Set up log rotation
- [ ] Test email notifications
- [ ] Run integration tests

---

## 🎯 Week 6 Complete!

**Congratulations! You've completed Week 6 (Days 026-030):**

✅ React frontend dashboard
✅ Real-time WebSocket updates
✅ PDF report generation
✅ Advanced email scheduling
✅ Docker containerization
✅ CI/CD with GitHub Actions
✅ Production deployment

**You now have:**
- Full-stack VaR system (backend + frontend)
- Real-time monitoring
- Automated reporting
- Production-ready deployment
- CI/CD pipeline
- Cloud deployment

**Total Progress: Days 001-030 (60% complete!)**

---

## ✅ Completed

✅ Dockerfile for containerization
✅ Docker Compose multi-service setup
✅ GitHub Actions CI/CD pipeline
✅ Automated testing
✅ Health check endpoints
✅ Cloud deployment guide
✅ Production configuration

**Next Steps (Days 031-050)**:
- Machine Learning VaR models
- Advanced backtesting
- Portfolio optimization
- Regulatory reporting
- Performance tuning
- Security hardening

**Congratulations on completing 60% of the course!** 🎉
