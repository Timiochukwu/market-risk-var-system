# Day 026: Frontend Dashboard (React Basics)

**Duration**: 2-2.5 hours | **Difficulty**: Intermediate | **Prerequisites**: Day 001-025

---

## 📋 What You'll Build

- React dashboard setup
- API integration with backend
- VaR display components
- Real-time data fetching
- Charts with Recharts
- Responsive layout

---

## 💡 Dashboard Overview

```
┌─────────────────────────────────────────┐
│  Market Risk VaR Dashboard              │
├─────────────────────────────────────────┤
│                                          │
│  Portfolio Summary                       │
│  ┌──────┬──────┬──────┬──────┐          │
│  │ VaR  │ CVaR │Sharpe│Status│          │
│  └──────┴──────┴──────┴──────┘          │
│                                          │
│  VaR Chart (Historical Trend)            │
│  ┌────────────────────────────┐         │
│  │  📈 Line Chart             │         │
│  └────────────────────────────┘         │
│                                          │
│  Recent Calculations                     │
│  ┌────────────────────────────┐         │
│  │ Ticker | VaR | Method | Date│        │
│  └────────────────────────────┘         │
│                                          │
└─────────────────────────────────────────┘
```

---

## 💻 Implementation

### Step 1: Setup React App

```bash
# Create React app
npx create-react-app var-dashboard
cd var-dashboard

# Install dependencies
npm install axios recharts react-router-dom

# Install TailwindCSS (optional but recommended)
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

---

### Step 2: API Service

Create `src/services/api.js`:

```javascript
/**
 * API Service for VaR Backend
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class VaRAPI {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add token to requests if available
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  // ==========================================
  // Authentication
  // ==========================================

  async login(username, password) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const response = await this.client.post('/auth/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    const { access_token } = response.data;
    localStorage.setItem('access_token', access_token);
    return access_token;
  }

  async register(username, email, password) {
    const response = await this.client.post('/auth/register', {
      username,
      email,
      password,
    });
    return response.data;
  }

  logout() {
    localStorage.removeItem('access_token');
  }

  async getCurrentUser() {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  // ==========================================
  // VaR Calculations
  // ==========================================

  async calculateVaR(ticker, options = {}) {
    const {
      method = 'historical',
      positionValue = 1000000,
      confidenceLevel = 0.95,
    } = options;

    const response = await this.client.post('/api/v1/var/calculate-and-store', null, {
      params: { ticker, method, position_value: positionValue, confidence_level: confidenceLevel },
    });

    return response.data;
  }

  async getVaRHistory(ticker, days = 30, method = null) {
    const params = { days };
    if (method) params.method = method;

    const response = await this.client.get(`/api/v1/var/history/${ticker}`, { params });
    return response.data;
  }

  async getVaRTrend(ticker, days = 30, method = null) {
    const params = { days };
    if (method) params.method = method;

    const response = await this.client.get(`/api/v1/var/trend/${ticker}`, { params });
    return response.data;
  }

  async batchCalculateVaR(tickers, method = 'historical') {
    const response = await this.client.post('/api/v1/var/batch-calculate', {
      tickers,
      method,
    });
    return response.data;
  }

  // ==========================================
  // Portfolio
  // ==========================================

  async getPositions() {
    const response = await this.client.get('/api/v1/positions');
    return response.data;
  }

  async getRateLimitStatus() {
    const response = await this.client.get('/api/v1/rate-limit/status');
    return response.data;
  }
}

export default new VaRAPI();
```

---

### Step 3: Dashboard Components

Create `src/components/VaRCard.jsx`:

```jsx
/**
 * VaR Summary Card Component
 */

import React from 'react';

const VaRCard = ({ title, value, subtitle, color = 'blue' }) => {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    red: 'bg-red-500',
    yellow: 'bg-yellow-500',
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border-l-4" style={{ borderColor: colorClasses[color] }}>
      <h3 className="text-gray-600 text-sm font-semibold uppercase">{title}</h3>
      <p className="text-3xl font-bold mt-2">{value}</p>
      {subtitle && <p className="text-gray-500 text-sm mt-1">{subtitle}</p>}
    </div>
  );
};

export default VaRCard;
```

Create `src/components/VaRChart.jsx`:

```jsx
/**
 * VaR Trend Chart Component
 */

import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const VaRChart = ({ data, title = 'VaR Trend' }) => {
  // Transform data for chart
  const chartData = data.calculations?.map((calc) => ({
    date: new Date(calc.calculation_date).toLocaleDateString(),
    VaR: calc.var_amount,
    CVaR: calc.cvar_amount,
  })) || [];

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
          <Legend />
          <Line type="monotone" dataKey="VaR" stroke="#3b82f6" strokeWidth={2} />
          <Line type="monotone" dataKey="CVaR" stroke="#ef4444" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default VaRChart;
```

Create `src/components/CalculationTable.jsx`:

```jsx
/**
 * Recent Calculations Table
 */

import React from 'react';

const CalculationTable = ({ calculations }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold mb-4">Recent Calculations</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-2 text-left">Date</th>
              <th className="px-4 py-2 text-left">Method</th>
              <th className="px-4 py-2 text-right">VaR</th>
              <th className="px-4 py-2 text-right">VaR %</th>
              <th className="px-4 py-2 text-right">CVaR</th>
            </tr>
          </thead>
          <tbody>
            {calculations?.slice(0, 10).map((calc, idx) => (
              <tr key={idx} className="border-b hover:bg-gray-50">
                <td className="px-4 py-2">
                  {new Date(calc.calculation_date).toLocaleDateString()}
                </td>
                <td className="px-4 py-2">
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                    {calc.method}
                  </span>
                </td>
                <td className="px-4 py-2 text-right font-semibold">
                  ${calc.var_amount.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </td>
                <td className="px-4 py-2 text-right">
                  {calc.var_percentage.toFixed(3)}%
                </td>
                <td className="px-4 py-2 text-right">
                  ${calc.cvar_amount?.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default CalculationTable;
```

---

### Step 4: Main Dashboard Page

Create `src/pages/Dashboard.jsx`:

```jsx
/**
 * Main Dashboard Page
 */

import React, { useState, useEffect } from 'react';
import VaRAPI from '../services/api';
import VaRCard from '../components/VaRCard';
import VaRChart from '../components/VaRChart';
import CalculationTable from '../components/CalculationTable';

const Dashboard = () => {
  const [ticker, setTicker] = useState('AAPL');
  const [history, setHistory] = useState(null);
  const [trend, setTrend] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, [ticker]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch VaR history
      const historyData = await VaRAPI.getVaRHistory(ticker, 30);
      setHistory(historyData);

      // Fetch trend
      const trendData = await VaRAPI.getVaRTrend(ticker, 30);
      setTrend(trendData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCalculateVaR = async () => {
    setLoading(true);
    try {
      await VaRAPI.calculateVaR(ticker);
      await fetchData(); // Refresh data
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const latestCalc = history?.calculations?.[0];

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800">Market Risk Dashboard</h1>
          <p className="text-gray-600 mt-1">Value at Risk Analysis</p>
        </div>

        {/* Ticker Input */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Ticker Symbol
              </label>
              <input
                type="text"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="AAPL"
              />
            </div>
            <button
              onClick={handleCalculateVaR}
              disabled={loading}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
            >
              {loading ? 'Calculating...' : 'Calculate VaR'}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Summary Cards */}
        {latestCalc && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <VaRCard
              title="VaR (95%)"
              value={`$${latestCalc.var_amount.toLocaleString()}`}
              subtitle="1-day Value at Risk"
              color="blue"
            />
            <VaRCard
              title="VaR %"
              value={`${latestCalc.var_percentage.toFixed(3)}%`}
              subtitle="Percentage of position"
              color="yellow"
            />
            <VaRCard
              title="CVaR"
              value={`$${latestCalc.cvar_amount?.toLocaleString()}`}
              subtitle="Expected Shortfall"
              color="red"
            />
            <VaRCard
              title="Trend"
              value={trend?.trend?.trend || 'N/A'}
              subtitle={`${trend?.trend?.change_percentage?.toFixed(2)}% change`}
              color={trend?.trend?.trend === 'increasing' ? 'red' : 'green'}
            />
          </div>
        )}

        {/* Chart */}
        {history && (
          <div className="mb-6">
            <VaRChart data={history} title={`VaR Trend - ${ticker}`} />
          </div>
        )}

        {/* Recent Calculations Table */}
        {history && <CalculationTable calculations={history.calculations} />}
      </div>
    </div>
  );
};

export default Dashboard;
```

---

### Step 5: App Entry Point

Update `src/App.js`:

```jsx
import React from 'react';
import Dashboard from './pages/Dashboard';
import './App.css';

function App() {
  return (
    <div className="App">
      <Dashboard />
    </div>
  );
}

export default App;
```

Update `src/App.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

---

## 🧪 Test the Dashboard

### Step 1: Start Backend

```bash
# Terminal 1: Start FastAPI backend
cd src/api
uvicorn main:app --reload --port 8000
```

### Step 2: Configure CORS

Update `src/api/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Market Risk VaR API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 3: Start Frontend

```bash
# Terminal 2: Start React app
cd var-dashboard
npm start

# Opens browser at http://localhost:3000
```

### Step 4: Test Features

1. **View Dashboard**: Opens with AAPL by default
2. **Change Ticker**: Type "MSFT" and click "Calculate VaR"
3. **View Chart**: See VaR trend over 30 days
4. **View Table**: See recent calculations

---

## 🧪 Test with curl (Backend Verification)

```bash
# Ensure backend is returning correct data for frontend

# Get VaR history (what frontend fetches)
curl -X GET "http://localhost:8000/api/v1/var/history/AAPL?days=30" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{count, calculations: .calculations | length}'

# Get trend (for trend card)
curl -X GET "http://localhost:8000/api/v1/var/trend/AAPL" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.trend | {trend, change_percentage}'

# Calculate new VaR (what button triggers)
curl -X POST "http://localhost:8000/api/v1/var/calculate-and-store" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"ticker": "AAPL"}' \
  -H "Content-Type: application/json" \
  | jq '{ticker, var_amount, var_percentage}'
```

---

## 📱 Dashboard Features

### Implemented:
✅ Responsive layout with Tailwind CSS
✅ VaR summary cards
✅ Interactive chart with Recharts
✅ Recent calculations table
✅ Real-time data fetching
✅ Ticker switching
✅ Loading and error states

### To Add (Optional):
- Login page
- Multiple ticker comparison
- Method selector (historical/parametric/monte carlo)
- Confidence level slider
- Export to CSV/Excel
- Dark mode

---

## 🎨 Customization

### Change Colors:

```jsx
// In VaRCard.jsx
const colorClasses = {
  blue: 'bg-blue-600',      // Change to darker blue
  green: 'bg-emerald-500',  // Use emerald instead
  // ...
};
```

### Add More Metrics:

```jsx
// In Dashboard.jsx
<VaRCard
  title="Sharpe Ratio"
  value={metrics?.sharpe_ratio?.toFixed(2) || 'N/A'}
  subtitle="Risk-adjusted return"
  color="green"
/>
```

---

## ✅ Completed

✅ React dashboard setup
✅ API service with axios
✅ VaR summary cards
✅ Interactive charts with Recharts
✅ Recent calculations table
✅ CORS configuration
✅ Responsive design with Tailwind

**Next**: Real-time WebSocket Updates (Day 027)
