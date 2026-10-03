#!/usr/bin/env python3
"""Launch the hardened Elite FX trading interface."""

import sys

try:
    from UltimateTradingInterface_Elite import EliteTradingGUI
    import tkinter as tk

    if __name__ == "__main__":
        print("Launching Elite FX Trading Interface...")
        print("Use an OANDA practice account until the strategy and execution are validated.")
        root = tk.Tk()
        EliteTradingGUI(root, smoke_test=False)
        root.mainloop()
except ImportError as e:
    print(f"Import error: {e}")
    print("Install project dependencies with: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error launching Elite interface: {e}")
    sys.exit(1)
