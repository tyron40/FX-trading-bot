from tpqoa import tpqoa
from datetime import datetime, timedelta
import os
import shutil
from livetrading.MiniTrader import MiniTrader

if __name__ == "__main__":
    # First ensure config directory exists
    if not os.path.exists('config'):
        os.makedirs('config')
        
    while True:
        try:
            # Switch between practice and live accounts
            print("\nChoose account type:")
            print("1: Practice Account (recommended for testing)")
            print("2: Live Account (real money trading)")
            
            account_choice = input("\nEnter choice (1 or 2): ").strip()
            if account_choice not in ["1", "2"]:
                print("Invalid choice. Please try again.")
                continue

            # Set configuration file based on choice
            if account_choice == "1":
                if os.path.exists("config/oanda_practice.cfg"):
                    shutil.copy2("config/oanda_practice.cfg", "oanda.cfg")
                    print("\nSwitched to PRACTICE account (no real money risk)")
                    account_type = "practice"
                else:
                    print("Practice config not found!")
                    continue
            else:
                if os.path.exists("config/oanda_live.cfg"):
                    print("\n⚠️ WARNING: Switching to LIVE account - Real money will be traded! ⚠️")
                    print("Current balance: $4.00")
                    confirm = input("Type 'yes' to confirm you want to trade with real money: ").strip().lower()
                    if confirm == 'yes':
                        shutil.copy2("config/oanda_live.cfg", "oanda.cfg")
                        print("Switched to LIVE account")
                        account_type = "live"
                    else:
                        print("Staying on practice account for safety")
                        shutil.copy2("config/oanda_practice.cfg", "oanda.cfg")
                        account_type = "practice"
                else:
                    print("Live config not found!")
                    continue
            
            # Create trader with safe settings
            if account_type == "live":
                print("\nStarting Mini Trader with safe settings for $4 account...")
                trader = MiniTrader(
                    cfg="oanda.cfg",
                    risk_per_trade=0.05,    # Risk 5% ($0.20) per trade
                    stop_loss_pct=0.25,     # Stop loss at 0.25%
                    take_profit_pct=0.5,    # Take profit at 0.5%
                )
            else:
                print("\nStarting Mini Trader with practice settings...")
                trader = MiniTrader(
                    cfg="oanda.cfg",
                    risk_per_trade=0.10,    # Risk 10% per trade
                    stop_loss_pct=0.5,      # Stop loss at 0.5%
                    take_profit_pct=1.0,    # Take profit at 1.0%
                )
            
            # Start trading
            trader.run()
            
        except KeyboardInterrupt:
            print("\nTrading stopped by user.")
            break
        except Exception as e:
            print(f"\nError occurred: {str(e)}")
            print("Please try again.")
            continue
