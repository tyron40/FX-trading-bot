#!/usr/bin/env python3
"""
Auto-run improved FemtoTrader with better analysis logic
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Run improved FemtoTrader automatically"""
    try:
        from FemtoTrader_improved import FemtoTrader

        print("Starting Improved FemtoTrader with practice account...")
        print("Enhanced features:")
        print("- Higher signal thresholds (0.7-0.8 minimum)")
        print("- Sentiment data confirmation when available")
        print("- Reduced position reversals")
        print("- Better risk management")

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
