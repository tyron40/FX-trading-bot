#!/usr/bin/env python3
"""
Test script for UltimateTrader analysis methods

This script tests the fixed analysis methods to ensure they work correctly.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_mock_data():
    """Create mock OHLC data for testing."""
    dates = pd.date_range(start=datetime.now() - timedelta(hours=2), periods=100, freq='5min')
    np.random.seed(42)

    # Create realistic price data with trend
    base_price = 1.0500
    trend = np.linspace(0, 0.005, 100)  # Slight upward trend
    noise = np.random.normal(0, 0.001, 100)

    close_prices = base_price + trend + noise

    # Create OHLC from close prices
    high_prices = close_prices + abs(np.random.normal(0, 0.0005, 100))
    low_prices = close_prices - abs(np.random.normal(0, 0.0005, 100))
    open_prices = close_prices + np.random.normal(0, 0.0002, 100)

    # Ensure OHLC integrity
    for i in range(len(close_prices)):
        high_prices[i] = max(high_prices[i], open_prices[i], close_prices[i])
        low_prices[i] = min(low_prices[i], open_prices[i], close_prices[i])

    mock_data = {
        'time': dates,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': np.random.randint(100, 1000, 100)
    }

    df = pd.DataFrame(mock_data)
    df.set_index('time', inplace=True)
    return df

def test_analysis_methods():
    """Test all analysis methods."""
    print("Testing UltimateTrader analysis methods...")

    try:
        from UltimateTrader import UltimateTrader

        # Create mock trader instance (without API connection)
        trader = UltimateTrader.__new__(UltimateTrader)  # Create without __init__

        # Initialize required attributes
        from helpers.technical_analysis import TechnicalAnalysis
        trader._technical_analyzer = TechnicalAnalysis()

        # Create mock data
        df = create_mock_data()
        print(f"✅ Mock data created: {len(df)} rows")

        # Test each analysis method
        methods_to_test = [
            ('_analyze_trend_following', trader._analyze_trend_following),
            ('_analyze_breakout', trader._analyze_breakout),
            ('_analyze_momentum', trader._analyze_momentum),
            ('_analyze_mean_reversion', trader._analyze_mean_reversion),
        ]

        results = {}

        for method_name, method_func in methods_to_test:
            try:
                print(f"Testing {method_name}...")
                score = method_func(df)
                results[method_name] = score
                print(f"✅ {method_name} returned score: {score:.4f}")

                # Validate score is in expected range (-1 to 1)
                if not (-1.1 <= score <= 1.1):
                    print(f"⚠️  {method_name} score {score} is outside expected range [-1, 1]")
                else:
                    print(f"✅ {method_name} score is within valid range")

            except Exception as e:
                print(f"❌ {method_name} failed: {e}")
                results[method_name] = None

        # Summary
        print("\n" + "="*50)
        print("Analysis Methods Test Results:")
        print("="*50)

        all_passed = True
        for method_name, score in results.items():
            status = "✅ PASSED" if score is not None else "❌ FAILED"
            score_str = f"{score:.4f}" if score is not None else "N/A"
            print(f"{method_name:<25} {status} (Score: {score_str})")
            if score is None:
                all_passed = False

        if all_passed:
            print("\n🎉 All analysis methods passed testing!")
            return True
        else:
            print("\n⚠️  Some analysis methods failed. Check errors above.")
            return False

    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False

def main():
    """Run analysis methods test."""
    print("🚀 UltimateTrader Analysis Methods Test")
    print("=" * 50)

    success = test_analysis_methods()

    if success:
        print("\n✅ Analysis methods are working correctly!")
        print("The UltimateTrader bot should now function properly.")
    else:
        print("\n❌ Analysis methods have issues that need fixing.")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
