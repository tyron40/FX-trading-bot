#!/usr/bin/env python3
"""
Auto-run FemtoTrader with practice account and auto trading enabled
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Run FemtoTrader automatically"""
    try:
        from FemtoTrader_new import FemtoTrader

        print("Starting FemtoTrader with practice account...")

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
