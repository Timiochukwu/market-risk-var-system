# 📊 Market Risk VaR - Frontend Dashboard

Professional React dashboard for the Market Risk VaR System.

## Features

- ✅ Real-time VaR calculations (6 methods)
- ✅ Portfolio breakdown visualization
- ✅ VaR history charts
- ✅ Backtesting results (Kupiec, Christoffersen, Traffic Light)
- ✅ Risk metrics (Sharpe, Sortino, Max Drawdown)
- ✅ Dark/Light mode
- ✅ Mobile responsive
- ✅ Export to PDF/Excel

## Quick Start

```bash
cd market-risk-var/frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Tech Stack

- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Recharts
- SWR

## API Connection

Configure in `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The dashboard connects to the FastAPI backend running on port 8000.

## Dashboard Sections

1. **Key Metrics** - Portfolio value, VaR, Sharpe ratio, Max drawdown
2. **VaR Methods** - Comparison of 6 VaR calculation methods
3. **Portfolio Breakdown** - Asset allocation pie chart
4. **VaR History** - 30-day VaR trend
5. **Backtesting** - Model validation results

## Deploy

```bash
npm run build
npm start
```

Or deploy to Vercel:
```bash
vercel
```
