#!/usr/bin/env python3
"""
Auto-run Advanced FemtoTrader with trendlines, candle patterns, and RSS analysis
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Run Advanced FemtoTrader automatically"""
    try:
        from FemtoTrader_advanced import FemtoTrader

        print("Starting Advanced FemtoTrader with Trendlines & Patterns...")
        print("Enhanced features:")
        print("- Dynamic Trendline Detection from swing points")
        print("- Candle Pattern Recognition (engulfing, pin bars, morning/evening stars)")
        print("- Breakout & Retest Confirmation")
        print("- RSS sentiment from central banks and news")
        print("- Higher signal thresholds (0.7-0.8 minimum)")
        print("- Pattern confirmation trading")
        print("- Reduced overtrading through advanced analysis")

        # Initialize trader with practice config
        trader = FemtoTrader("config/oanda_practice.cfg")

        # Set up basic callbacks (no GUI)
        def price_callback(price):
            print(f"Price update: ${price:.5f}")

        def signal_callback(signal):
            print(f"Signal: {signal}")

        def chart_callback(chart_data):
            print(f"Chart analysis: {len(chart_data.get('trendlines', []))} trendlines, {len(chart_data.get('patterns', []))} patterns")

        trader.set_gui_callbacks(
            price_callback=price_callback,
            signal_callback=signal_callback,
            chart_callback=chart_callback
        )

        print("Starting advanced trading loop...")
        trader.run()

    except KeyboardInterrupt:
        print("\nAdvanced trader stopped by user")
    except Exception as e:
        print(f"Error running advanced trader: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
