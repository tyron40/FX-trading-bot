"""
🚀 LIVE Trading Bot Launcher
⚠️ WARNING: This uses REAL MONEY!
"""

import tkinter as tk
from tkinter import messagebox
import subprocess
import sys

def show_warning():
    """Show safety warning before launching"""
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    warning_message = """
⚠️  LIVE TRADING WARNING ⚠️

You are about to launch the trading bot with your LIVE account.

IMPORTANT INFORMATION:
• Account Balance: $10.34 (REAL MONEY)
• Risk per trade: ~$0.10 (1% of balance)
• Position size: 100 units (very small)
• Bot will trade automatically when signals are strong

SAFETY FEATURES:
✅ Conservative trading (only strong signals)
✅ Small position sizes
✅ Stop button to halt trading anytime
✅ Real-time monitoring

RISKS:
⚠️ You can lose money
⚠️ Market conditions can change rapidly
⚠️ Past performance doesn't guarantee future results

Do you want to proceed with LIVE trading?
"""
    
    response = messagebox.askyesno(
        "⚠️ LIVE Trading Confirmation",
        warning_message,
        icon='warning'
    )
    
    root.destroy()
    return response

def main():
    """Main launcher"""
    print("\n" + "="*60)
    print("🚀 FX TRADING BOT - LIVE ACCOUNT LAUNCHER")
    print("="*60)
    print("\n⚠️  This will use your LIVE OANDA account")
    print("💰 Balance: $10.34 (REAL MONEY)")
    print("📊 Risk: ~$0.10 per trade")
    print("\n" + "="*60)
    
    # Show GUI warning
    if show_warning():
        print("\n✅ User confirmed - Launching LIVE trading bot...")
        print("⚠️  Remember to monitor carefully!")
        print("⚠️  Use the STOP button to halt trading anytime\n")
        
        # Launch the Perfect interface
        print("\n🚀 Launching Perfect Trading Interface...")
        print("✅ FULL trading mode (BUY & SELL)")
        print("✅ Monthly timeframe support")
        print("✅ Stop loss & take profit on every trade")
        print("✅ Complete information display\n")
        subprocess.run([sys.executable, "UltimateTradingInterface_Perfect.py"])
    else:
        print("\n❌ Cancelled by user")
        print("💡 To practice safely, use demo account instead")
        print("   (Select 'Demo' in the interface)\n")

if __name__ == "__main__":
    main()
