#!/usr/bin/env python3
"""
Runner script for the Ultimate Trading Interface

This script launches the complete FX trading interface with:
- Account toggle (Demo/Live)
- Integrated backtesting
- Advanced bullish rejection blocks trading
- Real-time charts and analysis
- Comprehensive GUI controls
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from UltimateTradingInterface import main

    if __name__ == "__main__":
        print("🚀 Launching Ultimate FX Trading Interface...")
        print("Features:")
        print("  • Toggle between Demo and Live accounts")
        print("  • Advanced bullish rejection blocks strategy")
        print("  • Integrated backtesting engine")
        print("  • Real-time charts and analysis")
        print("  • Comprehensive trading controls")
        print("\nStarting GUI...")

        main()

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required dependencies are installed:")
    print("  pip install tkinter matplotlib pandas numpy tpqoa")
    sys.exit(1)

except Exception as e:
    print(f"❌ Error launching interface: {e}")
    sys.exit(1)
