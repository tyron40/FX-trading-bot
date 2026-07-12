#!/usr/bin/env python3
"""
Test script to run FemtoTrader with practice account
"""

import sys
import os
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_trader():
    """Test FemtoTrader with practice account"""
    try:
        from FemtoTrader_new import FemtoTrader

        print("Testing FemtoTrader with practice account...")

        # Use practice config
        trader = FemtoTrader("config/oanda_practice.cfg")

        print("✓ FemtoTrader initialized successfully")

        # Test getting account summary
        try:
            summary = trader.get_account_summary()
            print(f"✓ Account summary retrieved: Balance = ${summary.get('balance', 'N/A')}")
        except Exception as e:
            print(f"✗ Failed to get account summary: {e}")

        # Test getting current price
        try:
            time_val, bid, ask = trader.get_prices('EUR_USD')
            print(f"✓ Current EUR/USD price: {bid}")
        except Exception as e:
            print(f"✗ Failed to get current price: {e}")

        # Test market analysis (this might take time due to web scraping)
        print("Testing market analysis...")
        try:
            analysis = trader._analyze_market()
            if analysis:
                print(f"✓ Market analysis successful: Direction={analysis['direction']}, Strength={analysis['strength']:.2f}")
            else:
                print("✗ Market analysis returned None")
        except Exception as e:
            print(f"✗ Market analysis failed: {e}")

        print("Test completed successfully!")
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_trader()
    sys.exit(0 if success else 1)
