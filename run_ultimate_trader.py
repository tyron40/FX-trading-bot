#!/usr/bin/env python3
"""
Ultimate Trading Bot Runner

This script starts the Ultimate Trading Bot with GUI interface.
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from UltimateTrader import UltimateTrader

def main():
    """Main function to run the Ultimate Trading Bot."""
    print("\n🚀 Starting Ultimate Trading Bot 🚀")
    print("=" * 50)

    try:
        # Initialize the bot
        bot = UltimateTrader()

        # Start GUI
        print("Starting GUI interface...")
        bot.start_gui()

        # Keep the main thread alive
        import time
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ Shutting down Ultimate Trading Bot...")
            bot.stop_trading()

    except Exception as e:
        print(f"Error starting Ultimate Trading Bot: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
