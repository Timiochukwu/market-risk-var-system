/**
 * Custom hook for backtesting operations
 */
import { useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { BacktestResult } from '@/lib/types';

interface BacktestRequest {
  ticker: string;
  confidence_level: number;
  position_value: number;
  method: 'historical' | 'parametric';
  train_ratio: number;
}

export function useBacktest() {
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const runBacktest = async (request: BacktestRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await apiClient.post<BacktestResult>('/backtest/var', request);
      setResult(data);
      return data;
    } catch (err) {
      const error = err as Error;
      setError(error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    result,
    isLoading,
    error,
    runBacktest,
  };
}
