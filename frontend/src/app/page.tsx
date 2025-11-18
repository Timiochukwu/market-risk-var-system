'use client'

import { useState, useEffect } from 'react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { TrendingDown, TrendingUp, Activity, AlertTriangle, BarChart3, PieChart as PieChartIcon, Settings, Download, RefreshCw } from 'lucide-react'

export default function VaRDashboard() {
  const [varData, setVarData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [selectedMethod, setSelectedMethod] = useState('all')
  const [confidenceLevel, setConfidenceLevel] = useState(0.95)

  useEffect(() => {
    fetchVarData()
  }, [selectedMethod, confidenceLevel])

  const fetchVarData = async () => {
    setLoading(true)
    try {
      // Mock data - replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      setVarData(getMockData())
    } catch (error) {
      console.error('Error fetching VaR data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getMockData = () => ({
    portfolio_value: 2547891,
    var_95: 48250,
    var_99: 72180,
    cvar_95: 58900,
    sharpe_ratio: 2.43,
    sortino_ratio: 3.12,
    max_drawdown: -0.087,
    var_methods: {
      historical: 45200,
      parametric_normal: 48250,
      parametric_t: 51300,
      monte_carlo: 47800,
      garch: 52100,
      eva: 49500
    },
    portfolio_breakdown: [
      { asset: 'AAPL', value: 500000, weight: 0.20 },
      { asset: 'MSFT', value: 450000, weight: 0.18 },
      { asset: 'GOOGL', value: 400000, weight: 0.16 },
      { asset: 'AMZN', value: 350000, weight: 0.14 },
      { asset: 'META', value: 300000, weight: 0.12 },
      { asset: 'Others', value: 547891, weight: 0.20 }
    ],
    var_history: Array.from({ length: 30 }, (_, i) => ({
      date: `Day ${i + 1}`,
      var: 45000 + Math.random() * 10000,
      returns: -2000 + Math.random() * 4000
    })),
    backtest_results: {
      exceptions: 3,
      expected_exceptions: 5,
      kupiec_pvalue: 0.234,
      christoffersen_pvalue: 0.456,
      traffic_light: 'Green'
    }
  })

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading VaR data...</p>
        </div>
      </div>
    )
  }

  const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#6366f1']

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-600 rounded-lg">
                <Activity className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Market Risk VaR</h1>
                <p className="text-sm text-gray-600 dark:text-gray-400">Real-time Value at Risk Analysis</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={fetchVarData} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2">
                <RefreshCw className="h-4 w-4" />
                Refresh
              </button>
              <button className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors flex items-center gap-2">
                <Download className="h-4 w-4" />
                Export
              </button>
              <button className="p-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                <Settings className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Portfolio Value"
            value={`$${varData.portfolio_value.toLocaleString()}`}
            change="+12.4%"
            isPositive={true}
            icon={<TrendingUp className="h-5 w-5" />}
          />
          <MetricCard
            title="VaR (95%)"
            value={`$${varData.var_95.toLocaleString()}`}
            subtitle="1-day horizon"
            icon={<AlertTriangle className="h-5 w-5" />}
            color="red"
          />
          <MetricCard
            title="Sharpe Ratio"
            value={varData.sharpe_ratio.toFixed(2)}
            subtitle="Excellent"
            isPositive={true}
            icon={<BarChart3 className="h-5 w-5" />}
          />
          <MetricCard
            title="Max Drawdown"
            value={`${(varData.max_drawdown * 100).toFixed(2)}%`}
            subtitle="30-day"
            isPositive={false}
            icon={<TrendingDown className="h-5 w-5" />}
          />
        </div>

        {/* VaR Methods Comparison */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">VaR Methods Comparison</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={Object.entries(varData.var_methods).map(([method, value]) => ({
                method: method.replace(/_/g, ' ').toUpperCase(),
                value: value
              }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="method" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Portfolio Breakdown</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={varData.portfolio_breakdown}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ asset, weight }) => `${asset} (${(weight * 100).toFixed(1)}%)`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {varData.portfolio_breakdown.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* VaR History */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">VaR History (30 Days)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={varData.var_history}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="var" stroke="#ef4444" strokeWidth={2} name="VaR (95%)" />
              <Line type="monotone" dataKey="returns" stroke="#10b981" strokeWidth={2} name="Daily Returns" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Backtesting Results */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Backtesting Results</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                {varData.backtest_results.exceptions}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">VaR Exceptions</div>
              <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                Expected: {varData.backtest_results.expected_exceptions}
              </div>
            </div>
            <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                {varData.backtest_results.kupiec_pvalue.toFixed(3)}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Kupiec Test</div>
              <div className="text-xs text-green-600 dark:text-green-400 mt-1">
                {varData.backtest_results.kupiec_pvalue > 0.05 ? 'PASS' : 'FAIL'}
              </div>
            </div>
            <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className={`inline-block px-4 py-2 rounded-full text-lg font-semibold ${
                varData.backtest_results.traffic_light === 'Green' ? 'bg-green-100 text-green-800' :
                varData.backtest_results.traffic_light === 'Yellow' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {varData.backtest_results.traffic_light}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400 mt-2">Traffic Light Zone</div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

function MetricCard({ title, value, subtitle, change, isPositive, icon, color = 'blue' }: any) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-start justify-between mb-4">
        <div className={`p-2 rounded-lg ${
          color === 'red' ? 'bg-red-100 text-red-600 dark:bg-red-900/20 dark:text-red-400' :
          'bg-blue-100 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400'
        }`}>
          {icon}
        </div>
        {change && (
          <span className={`text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {change}
          </span>
        )}
      </div>
      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">{title}</div>
      <div className="text-2xl font-bold text-gray-900 dark:text-white mb-1">{value}</div>
      {subtitle && <div className="text-xs text-gray-500 dark:text-gray-500">{subtitle}</div>}
    </div>
  )
}
