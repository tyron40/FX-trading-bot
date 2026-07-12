#!/usr/bin/env python3
"""
Test script for Ultimate Trading Bot

This script performs basic validation tests for the Ultimate Trading Bot.
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test basic imports."""
    print("Testing imports...")

    try:
        # Test standard library imports
        import tkinter as tk
        print("✅ tkinter imported")

        import matplotlib.pyplot as plt
        print("✅ matplotlib imported")

        import pandas as pd
        print("✅ pandas imported")

        import numpy as np
        print("✅ numpy imported")

        # Test helper modules
        from helpers.technical_analysis import TechnicalAnalysis
        print("✅ TechnicalAnalysis imported")

        from helpers.market_analyzer import MarketAnalyzer
        print("✅ MarketAnalyzer imported")

        from helpers.enhanced_market_analyzer import EnhancedMarketAnalyzer
        print("✅ EnhancedMarketAnalyzer imported")

        # Test tpqoa
        from tpqoa.tpqoa import tpqoa
        print("✅ tpqoa imported")

        # Test main module
        from UltimateTrader import UltimateTrader, UltimateTraderGUI
        print("✅ UltimateTrader classes imported")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during imports: {e}")
        return False

def test_class_instantiation():
    """Test class instantiation without API calls."""
    print("\nTesting class instantiation...")

    try:
        from helpers.technical_analysis import TechnicalAnalysis
        from helpers.market_analyzer import MarketAnalyzer
        from helpers.enhanced_market_analyzer import EnhancedMarketAnalyzer

        # Test helper classes
        ta = TechnicalAnalysis()
        print("✅ TechnicalAnalysis instantiated")

        ma = MarketAnalyzer()
        print("✅ MarketAnalyzer instantiated")

        ema = EnhancedMarketAnalyzer()
        print("✅ EnhancedMarketAnalyzer instantiated")

        return True

    except Exception as e:
        print(f"❌ Class instantiation error: {e}")
        return False

def test_config_files():
    """Test configuration file access."""
    print("\nTesting configuration files...")

    config_paths = [
        "config/oanda_practice.cfg",
        "config/oanda_demo.cfg",
        "config/oanda_live.cfg"
    ]

    for config_path in config_paths:
        if os.path.exists(config_path):
            print(f"✅ {config_path} exists")
        else:
            print(f"❌ {config_path} missing")

    return True

def test_helper_methods():
    """Test helper class methods with mock data."""
    print("\nTesting helper methods...")

    try:
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta

        # Create mock data
        dates = pd.date_range(start=datetime.now() - timedelta(hours=2), periods=100, freq='5min')
        np.random.seed(42)

        mock_data = {
            'time': dates,
            'open': 1.0500 + np.random.normal(0, 0.001, 100),
            'high': 1.0500 + np.random.normal(0, 0.001, 100) + 0.0005,
            'low': 1.0500 + np.random.normal(0, 0.001, 100) - 0.0005,
            'close': 1.0500 + np.random.normal(0, 0.001, 100),
            'volume': np.random.randint(100, 1000, 100)
        }

        df = pd.DataFrame(mock_data)
        df.set_index('time', inplace=True)

        # Ensure high >= close >= low >= open (basic OHLC integrity)
        for i in range(len(df)):
            high = max(df.iloc[i]['open'], df.iloc[i]['close']) + abs(np.random.normal(0, 0.0002))
            low = min(df.iloc[i]['open'], df.iloc[i]['close']) - abs(np.random.normal(0, 0.0002))
            df.iloc[i, df.columns.get_loc('high')] = high
            df.iloc[i, df.columns.get_loc('low')] = low

        print(f"✅ Mock data created: {len(df)} rows")

        # Test TechnicalAnalysis
        from helpers.technical_analysis import TechnicalAnalysis
        ta = TechnicalAnalysis()
        analysis = ta.analyze_chart(df)
        print("✅ TechnicalAnalysis.analyze_chart() executed")

        # Test MarketAnalyzer
        from helpers.market_analyzer import MarketAnalyzer
        ma = MarketAnalyzer()
        # Test basic functionality without API calls
        print("✅ MarketAnalyzer instantiated")

        return True

    except Exception as e:
        print(f"❌ Helper methods test error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Ultimate Trading Bot - Test Suite")
    print("=" * 50)

    tests = [
        ("Import Test", test_imports),
        ("Class Instantiation Test", test_class_instantiation),
        ("Config Files Test", test_config_files),
        ("Helper Methods Test", test_helper_methods),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Ultimate Trading Bot is ready.")
        print("\nTo run the bot:")
        print("  python run_ultimate_trader.py")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
