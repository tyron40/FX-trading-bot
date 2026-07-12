#!/usr/bin/env python3
"""
Safe Ultimate Trading Bot Runner

This script starts the Safe Ultimate Trading Bot with conservative parameters.
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from UltimateTrader_safe import UltimateTraderSafe

def main():
    """Main function to run the Safe Ultimate Trading Bot."""
    print("\n🛡️ Starting SAFE Ultimate Trading Bot 🛡️")
    print("=" * 60)

    try:
        # Initialize the safe bot
        bot = UltimateTraderSafe()

        # Start GUI (which auto-starts trading)
        print("Starting safe GUI interface...")
        bot.start_gui()

        # Keep the main thread alive
        import time
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ Shutting down Safe Ultimate Trading Bot...")
            bot.stop_trading()

    except Exception as e:
        print(f"Error starting Safe Ultimate Trading Bot: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
