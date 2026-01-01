# Day 027: Real-time WebSocket Updates

**Duration**: 2 hours | **Difficulty**: Intermediate-Advanced | **Prerequisites**: Day 001-026

---

## 📋 What You'll Build

- WebSocket server with FastAPI
- Real-time VaR updates
- Live price monitoring
- WebSocket client in React
- Connection management
- Event broadcasting

---

## 💡 Why WebSockets?

### HTTP Polling (Old Way):
```
Client: "Any updates?" → Server: "No"
Client: "Any updates?" → Server: "No"
Client: "Any updates?" → Server: "Yes, new VaR!"

❌ Wasteful (100 requests, 1 useful)
❌ High latency (polling interval)
❌ Server load (constant requests)
```

### WebSockets (New Way):
```
Client ←→ Server (persistent connection)
Server: "New VaR!" → Client (instant push)

✅ Efficient (single connection)
✅ Low latency (instant updates)
✅ Low server load
```

---

## 💻 Implementation

### Step 1: Install Dependencies

```bash
# Backend
pip install python-socketio==5.10.0 python-socketio[asyncio]==5.10.0

# Frontend (already in React project)
cd var-dashboard
npm install socket.io-client
```

---

### Step 2: WebSocket Server

Create `src/websocket/socket_manager.py`:

```python
"""
WebSocket Manager for Real-time Updates
"""

import socketio
from typing import Dict, List
import asyncio
import logging

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*'  # Configure properly in production
)

# Track connected clients
connected_clients: Dict[str, dict] = {}


@sio.event
async def connect(sid, environ):
    """Client connected"""
    logger.info(f"Client connected: {sid}")
    connected_clients[sid] = {
        'connected_at': asyncio.get_event_loop().time(),
        'subscriptions': []
    }
    await sio.emit('connection_established', {'sid': sid}, room=sid)


@sio.event
async def disconnect(sid):
    """Client disconnected"""
    logger.info(f"Client disconnected: {sid}")
    if sid in connected_clients:
        del connected_clients[sid]


@sio.event
async def subscribe_ticker(sid, data):
    """Subscribe to ticker updates"""
    ticker = data.get('ticker')
    if not ticker:
        return

    if sid in connected_clients:
        if ticker not in connected_clients[sid]['subscriptions']:
            connected_clients[sid]['subscriptions'].append(ticker)
            logger.info(f"Client {sid} subscribed to {ticker}")
            await sio.emit('subscribed', {'ticker': ticker}, room=sid)


@sio.event
async def unsubscribe_ticker(sid, data):
    """Unsubscribe from ticker updates"""
    ticker = data.get('ticker')
    if not ticker:
        return

    if sid in connected_clients:
        if ticker in connected_clients[sid]['subscriptions']:
            connected_clients[sid]['subscriptions'].remove(ticker)
            logger.info(f"Client {sid} unsubscribed from {ticker}")
            await sio.emit('unsubscribed', {'ticker': ticker}, room=sid)


async def broadcast_var_update(ticker: str, var_data: dict):
    """
    Broadcast VaR update to all subscribed clients

    Args:
        ticker: Ticker symbol
        var_data: VaR calculation data
    """
    # Find clients subscribed to this ticker
    for sid, client_data in connected_clients.items():
        if ticker in client_data['subscriptions']:
            await sio.emit('var_update', {
                'ticker': ticker,
                'data': var_data
            }, room=sid)

    logger.info(f"Broadcasted VaR update for {ticker}")


async def broadcast_alert(alert_type: str, message: str, data: dict = None):
    """
    Broadcast alert to all connected clients

    Args:
        alert_type: Type of alert (breach, warning, info)
        message: Alert message
        data: Additional data
    """
    await sio.emit('alert', {
        'type': alert_type,
        'message': message,
        'data': data or {}
    })

    logger.info(f"Broadcasted alert: {alert_type} - {message}")


def get_connection_stats() -> dict:
    """Get WebSocket connection statistics"""
    return {
        'total_connections': len(connected_clients),
        'clients': [
            {
                'sid': sid,
                'subscriptions': data['subscriptions'],
                'connected_seconds': asyncio.get_event_loop().time() - data['connected_at']
            }
            for sid, data in connected_clients.items()
        ]
    }
```

---

### Step 3: Integrate WebSocket with FastAPI

Update `src/api/main.py`:

```python
import socketio
from websocket.socket_manager import sio, broadcast_var_update, broadcast_alert, get_connection_stats

# Create Socket.IO ASGI app
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# Update the app to use socket_app
# Change: uvicorn main:app
# To: uvicorn main:socket_app


@app.post("/api/v1/var/calculate-and-store-realtime")
async def calculate_and_store_var_realtime(
    ticker: str,
    position_value: float = 1000000,
    method: str = "historical",
    confidence_level: float = 0.95,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Calculate VaR and broadcast via WebSocket"""

    # Calculate VaR (existing logic)
    data = data_collector.fetch_stock_data(ticker, period="2y")
    returns = preprocessor.prepare_returns_data(data)['Returns']

    var_calc = VaRCalculator(confidence_level=confidence_level)
    var_result = var_calc.historical_var(returns, position_value)

    # Store in database
    position = crud.get_or_create_position(db, ticker, position_value)
    var_record = crud.create_var_calculation(
        db=db,
        position_id=position.id,
        method=method,
        confidence_level=confidence_level,
        var_amount=var_result['VaR'],
        var_percentage=var_result['VaR_Percentage'],
        cvar_amount=var_result.get('CVaR')
    )

    # Broadcast update via WebSocket
    await broadcast_var_update(ticker, {
        'var_id': var_record.id,
        'var_amount': var_record.var_amount,
        'var_percentage': var_record.var_percentage,
        'cvar_amount': var_record.cvar_amount,
        'method': method,
        'timestamp': var_record.calculation_date.isoformat()
    })

    return {
        "ticker": ticker,
        "var_id": var_record.id,
        "var_amount": var_record.var_amount,
        "broadcasted": True
    }


@app.get("/api/v1/websocket/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return get_connection_stats()


@app.post("/api/v1/websocket/broadcast-alert")
async def broadcast_alert_endpoint(
    alert_type: str,
    message: str,
    data: dict = None,
    current_user: User = Depends(get_current_admin_user)
):
    """Broadcast alert to all clients (admin only)"""
    await broadcast_alert(alert_type, message, data)
    return {"message": "Alert broadcasted"}
```

---

### Step 4: React WebSocket Client

Create `src/services/websocket.js`:

```javascript
/**
 * WebSocket Service for Real-time Updates
 */

import io from 'socket.io-client';

const WS_URL = process.env.REACT_APP_WS_URL || 'http://localhost:8000';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
  }

  connect() {
    if (this.socket?.connected) {
      console.log('Already connected');
      return;
    }

    this.socket = io(WS_URL, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected:', this.socket.id);
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
    });

    this.socket.on('connection_established', (data) => {
      console.log('Connection established:', data);
    });

    this.socket.on('var_update', (data) => {
      console.log('VaR update received:', data);
      this.emit('var_update', data);
    });

    this.socket.on('alert', (data) => {
      console.log('Alert received:', data);
      this.emit('alert', data);
    });

    this.socket.on('subscribed', (data) => {
      console.log('Subscribed to:', data.ticker);
    });

    this.socket.on('unsubscribed', (data) => {
      console.log('Unsubscribed from:', data.ticker);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  subscribeTicker(ticker) {
    if (this.socket?.connected) {
      this.socket.emit('subscribe_ticker', { ticker });
    }
  }

  unsubscribeTicker(ticker) {
    if (this.socket?.connected) {
      this.socket.emit('unsubscribe_ticker', { ticker });
    }
  }

  // Event emitter pattern
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    };
  }

  emit(event, data) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach((callback) => callback(data));
    }
  }

  isConnected() {
    return this.socket?.connected || false;
  }
}

export default new WebSocketService();
```

---

### Step 5: React Component with WebSocket

Update `src/pages/Dashboard.jsx`:

```jsx
import React, { useState, useEffect } from 'react';
import VaRAPI from '../services/api';
import WebSocketService from '../services/websocket';
import VaRCard from '../components/VaRCard';
import VaRChart from '../components/VaRChart';
import CalculationTable from '../components/CalculationTable';

const Dashboard = () => {
  const [ticker, setTicker] = useState('AAPL');
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    // Connect WebSocket
    WebSocketService.connect();

    // Listen for connection status
    const checkConnection = setInterval(() => {
      setWsConnected(WebSocketService.isConnected());
    }, 1000);

    // Listen for VaR updates
    const unsubscribeVarUpdate = WebSocketService.on('var_update', (data) => {
      console.log('Received VaR update:', data);
      // Refresh data
      fetchData();
      // Show notification
      showNotification(`VaR updated for ${data.ticker}: $${data.data.var_amount.toLocaleString()}`);
    });

    // Listen for alerts
    const unsubscribeAlert = WebSocketService.on('alert', (data) => {
      console.log('Received alert:', data);
      setAlerts((prev) => [...prev, data].slice(-5)); // Keep last 5 alerts
    });

    return () => {
      clearInterval(checkConnection);
      unsubscribeVarUpdate();
      unsubscribeAlert();
      WebSocketService.disconnect();
    };
  }, []);

  useEffect(() => {
    if (wsConnected) {
      // Subscribe to ticker updates
      WebSocketService.subscribeTicker(ticker);
    }

    return () => {
      if (wsConnected) {
        WebSocketService.unsubscribeTicker(ticker);
      }
    };
  }, [ticker, wsConnected]);

  useEffect(() => {
    fetchData();
  }, [ticker]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const historyData = await VaRAPI.getVaRHistory(ticker, 30);
      setHistory(historyData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const showNotification = (message) => {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('VaR Update', { body: message });
    }
  };

  const handleCalculateVaR = async () => {
    setLoading(true);
    try {
      // Use real-time endpoint
      await VaRAPI.calculateVaR(ticker);
      // Update will come via WebSocket
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header with WebSocket Status */}
        <div className="mb-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">Market Risk Dashboard</h1>
            <p className="text-gray-600 mt-1">Real-time Value at Risk Analysis</p>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-600">
              {wsConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* Alerts */}
        {alerts.length > 0 && (
          <div className="mb-6 space-y-2">
            {alerts.map((alert, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-lg ${
                  alert.type === 'breach' ? 'bg-red-100 text-red-800' :
                  alert.type === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-blue-100 text-blue-800'
                }`}
              >
                {alert.message}
              </div>
            ))}
          </div>
        )}

        {/* Rest of dashboard (same as before) */}
        {/* ... */}
      </div>
    </div>
  );
};

export default Dashboard;
```

---

## 🧪 Test WebSocket

### Step 1: Start Server

```bash
# Start with Socket.IO support
cd src/api
uvicorn main:socket_app --reload --port 8000

# Should see: "Socket.IO server running"
```

### Step 2: Test with wscat (CLI tool)

```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c "ws://localhost:8000/socket.io/?EIO=4&transport=websocket"

# Subscribe to ticker
> {"type": "subscribe_ticker", "data": {"ticker": "AAPL"}}
```

### Step 3: Test with curl (HTTP endpoints)

```bash
# Get WebSocket stats
curl -X GET "http://localhost:8000/api/v1/websocket/stats" | jq '.'
```

**Expected:**
```json
{
  "total_connections": 2,
  "clients": [
    {
      "sid": "abc123",
      "subscriptions": ["AAPL", "MSFT"],
      "connected_seconds": 45.6
    }
  ]
}
```

```bash
# Calculate VaR and broadcast
curl -X POST "http://localhost:8000/api/v1/var/calculate-and-store-realtime" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "method": "historical"
  }' | jq '.'
```

**Expected:**
```json
{
  "ticker": "AAPL",
  "var_id": 123,
  "var_amount": 28456.78,
  "broadcasted": true
}
```

**WebSocket clients will receive:**
```json
{
  "ticker": "AAPL",
  "data": {
    "var_id": 123,
    "var_amount": 28456.78,
    "var_percentage": 2.8457,
    "timestamp": "2026-01-01T10:30:00"
  }
}
```

### Step 4: Broadcast Alert (Admin)

```bash
# Broadcast alert to all connected clients
curl -X POST "http://localhost:8000/api/v1/websocket/broadcast-alert" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "alert_type": "breach",
    "message": "VaR breach detected for AAPL",
    "data": {"ticker": "AAPL", "breach_amount": 5000}
  }'
```

---

## 🎯 Real-time Features

### Implemented:
✅ WebSocket server with Socket.IO
✅ Real-time VaR updates
✅ Client subscription system
✅ Alert broadcasting
✅ Connection management
✅ Auto-reconnection

### Use Cases:
- Live VaR monitoring during trading hours
- Instant breach notifications
- Multi-user dashboards (everyone sees updates)
- Real-time portfolio updates

---

## ✅ Completed

✅ WebSocket server with FastAPI + Socket.IO
✅ Real-time VaR broadcasting
✅ Ticker subscription system
✅ Alert notifications
✅ React WebSocket client
✅ Connection status monitoring
✅ Auto-reconnection handling

**Next**: PDF Report Generation (Day 028)
