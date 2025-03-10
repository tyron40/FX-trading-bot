from livetrading.AutoTrader import AutoTrader
import os
import shutil

def switch_account():
    print("\nChoose account type:")
    print("1: Practice Account (recommended for testing)")
    print("2: Live Account (real money trading)")
    
    while True:
        choice = input("\nEnter choice (1 or 2): ")
        if choice == "1":
            if os.path.exists("config/oanda_practice.cfg"):
                shutil.copy2("config/oanda_practice.cfg", "oanda.cfg")
                print("\nSwitched to PRACTICE account (no real money risk)")
                return "practice"
            else:
                print("Practice config not found!")
        elif choice == "2":
            if os.path.exists("config/oanda_live.cfg"):
                print("\n⚠️ WARNING: Switching to LIVE account - Real money will be traded! ⚠️")
                print("The bot will:")
                print("- Analyze all currency pairs")
                print("- Trade only the strongest opportunities")
                print("- Use strict risk management")
                print("- Automatically close losing trades")
                confirm = input("\nType 'yes' to confirm you want to auto-trade with real money: ")
                if confirm.lower() == 'yes':
                    shutil.copy2("config/oanda_live.cfg", "oanda.cfg")
                    print("Switched to LIVE account")
                    return "live"
                else:
                    print("Staying on practice account for safety")
                    shutil.copy2("config/oanda_practice.cfg", "oanda.cfg")
                    return "practice"
            else:
                print("Live config not found!")
        
        print("Invalid choice, please try again")

if __name__ == "__main__":
    # First ensure config directory exists
    if not os.path.exists('config'):
        os.makedirs('config')
        
    # Switch between practice and live accounts
    account_type = switch_account()
    
    # Safe settings for $4 account
    if account_type == "live":
        trader = AutoTrader(
            cfg="oanda.cfg",
            bar_length="1m",
            risk_per_trade=0.05,    # Risk 5% ($0.20) per trade
            stop_loss_pct=0.25,     # Stop loss at 0.25%
            take_profit_pct=0.5,    # Take profit at 0.5%
            max_positions=2         # Maximum 2 positions at once
        )
    else:
        # Practice account - can use slightly more aggressive settings
        trader = AutoTrader(
            cfg="oanda.cfg",
            bar_length="1m",
            risk_per_trade=0.10,    # Risk 10% per trade
            stop_loss_pct=0.5,      # Stop loss at 0.5%
            take_profit_pct=1.0,    # Take profit at 1.0%
            max_positions=3         # Maximum 3 positions at once
        )
    
    # Start auto trading
    trader.run()
