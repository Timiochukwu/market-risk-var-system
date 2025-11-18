/**
 * Custom hook for VaR data fetching
 */
import useSWR from 'swr';
import { apiClient } from '@/lib/api-client';
import { VaRCalculation, VaRRequest } from '@/lib/types';

export function useVarData(request: VaRRequest | null) {
  const { data, error, isLoading, mutate } = useSWR<VaRCalculation>(
    request ? ['/var/calculate', request] : null,
    ([url, req]) => apiClient.post(url, req),
    {
      revalidateOnFocus: false,
      shouldRetryOnError: false,
    }
  );

  return {
    varData: data,
    error,
    isLoading,
    refetch: mutate,
  };
}

export function useCompareVarMethods(ticker: string | null) {
  const { data, error, isLoading } = useSWR(
    ticker
      ? `/var/compare`
      : null,
    () =>
      apiClient.post('/var/compare', {
        ticker,
        confidence_level: 0.95,
        position_value: 1000000,
        include_garch: true,
      }),
    {
      revalidateOnFocus: false,
    }
  );

  return {
    comparison: data,
    error,
    isLoading,
  };
}
