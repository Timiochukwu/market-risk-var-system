#!/usr/bin/env python3
"""
Run VaR backtesting from command line.
"""
import argparse
from src.data.data_collector import DataCollector
from src.data.preprocessor import DataPreprocessor
from src.models.var_calculator import VaRCalculator
from src.services.backtest_service import VaRBacktester

def main():
    parser = argparse.ArgumentParser(description='Run VaR Backtesting')
    parser.add_argument('ticker', help='Stock ticker symbol')
    parser.add_argument('--confidence', type=float, default=0.95, help='Confidence level')
    parser.add_argument('--position', type=float, default=1000000, help='Position value')
    parser.add_argument('--method', default='historical', choices=['historical', 'parametric'])

    args = parser.parse_args()

    print(f"Running backtest for {args.ticker}...")

    # Fetch data
    collector = DataCollector()
    data = collector.fetch_stock_data(args.ticker, period="2y")

    # Prepare returns
    preprocessor = DataPreprocessor()
    returns_data = preprocessor.prepare_returns_data(data)
    returns = returns_data['Returns'].dropna()

    # Split data
    train_size = int(len(returns) * 0.7)
    train_returns = returns.iloc[:train_size]
    test_returns = returns.iloc[train_size:]

    # Calculate VaR
    var_calc = VaRCalculator(confidence_level=args.confidence)
    if args.method == 'historical':
        var_result = var_calc.historical_var(train_returns, args.position)
    else:
        var_result = var_calc.parametric_var(train_returns, args.position)

    # Backtest
    import pandas as pd
    var_estimates = pd.Series(var_result['VaR'], index=test_returns.index)

    backtester = VaRBacktester(confidence_level=args.confidence)
    results = backtester.backtest_var_model(test_returns, var_estimates, args.position)

    # Print results
    print("\n" + "="*60)
    print(f"Backtest Results for {args.ticker}")
    print("="*60)
    print(f"Method: {args.method}")
    print(f"Confidence Level: {args.confidence:.0%}")
    print(f"Position Value: ${args.position:,.2f}")
    print(f"\nObservations: {results['num_observations']}")
    print(f"Exceptions: {results['num_exceptions']}")
    print(f"Exception Rate: {results['exception_rate']:.2%}")
    print(f"Expected Rate: {results['expected_rate']:.2%}")
    print(f"\nKupiec Test: {results['kupiec_test']['Result']}")
    print(f"Traffic Light Zone: {results['traffic_light_test']['Zone']}")
    print("="*60)

if __name__ == "__main__":
    main()
