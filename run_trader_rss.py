#!/usr/bin/env python3
"""
Auto-run FemtoTrader with RSS-based market analysis
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Run RSS-based FemtoTrader automatically"""
    try:
        from FemtoTrader_rss import FemtoTrader

        print("Starting RSS-Based FemtoTrader with practice account...")
        print("Enhanced features:")
        print("- RSS feeds from official sources (no API keys needed)")
        print("- Central bank news from ECB, Fed, BoE, etc.")
        print("- Financial news from CNBC, FT, Reuters")
        print("- Higher signal thresholds (0.7-0.8 minimum)")
        print("- Sentiment confirmation when RSS data available")
        print("- Reduced overtrading")

        # Initialize trader with practice config
        trader = FemtoTrader("config/oanda_practice.cfg")

        # Set up basic callbacks (no GUI)
        def price_callback(price):
            print(f"Price update: ${price:.5f}")

        def signal_callback(signal):
            print(f"Signal: {signal}")

        trader.set_gui_callbacks(
            price_callback=price_callback,
            signal_callback=signal_callback
        )

        print("Starting trading loop...")
        trader.run()

    except KeyboardInterrupt:
        print("\nTrader stopped by user")
    except Exception as e:
        print(f"Error running trader: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
