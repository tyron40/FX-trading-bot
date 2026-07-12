#!/usr/bin/env python3
"""
Auto-run Trend-Following FemtoTrader with multi-instrument support
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Run Trend-Following FemtoTrader automatically"""
    try:
        from FemtoTrader_trendlines import FemtoTrader

        print("Starting Multi-Instrument Trend-Following Trader...")
        print("Enhanced features:")
        print("- Trend-following bias (no counter-trend trades)")
        print("- Multi-instrument diversification (EUR_USD, GBP_USD, USD_JPY, USD_CHF, AUD_USD)")
        print("- Dynamic trendline analysis per instrument")
        print("- Swing point detection for trend direction")
        print("- Breakout trading with trend confirmation")
        print("- Reduced risk per trade (2% per instrument)")
        print("- 30-second analysis cycle for trend following")

        # Initialize trader with multiple instruments
        instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD']
        trader = FemtoTrader("config/oanda_practice.cfg", instruments=instruments)

        # Set up basic callbacks
        def price_callback(price):
            print(f"Price update: ${price:.5f}")

        def trend_callback(trend_data):
            print(f"Trend analysis updated for {len(trend_data)} instruments")

        def position_callback(positions):
            if positions:
                print(f"Active positions: {len(positions)} instruments")
            else:
                print("No active positions")

        trader.set_gui_callbacks(
            price_callback=price_callback,
            trend_callback=trend_callback,
            position_callback=position_callback
        )

        print("Starting trend-following trading loop...")
        trader.run()

    except KeyboardInterrupt:
        print("\nTrend-following trader stopped by user")
    except Exception as e:
        print(f"Error running trend-following trader: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
