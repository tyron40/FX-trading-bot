import os
import shutil
from livetrading.BasicTrader import BasicTrader

def main():
    # Ensure config directory exists
    if not os.path.exists('config'):
        os.makedirs('config')
    
    try:
        # Get account type
        print("\nChoose account type:")
        print("1: Practice Account (recommended for testing)")
        print("2: Live Account (real money trading)")
        
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        # Set up configuration
        if choice == "1":
            if not os.path.exists("config/oanda_practice.cfg"):
                print("Practice config not found!")
                return
            shutil.copy2("config/oanda_practice.cfg", "oanda.cfg")
            print("\nUsing PRACTICE account (no real money risk)")
            
            # Create practice trader
            trader = BasicTrader(
                cfg="oanda.cfg",
                risk_per_trade=0.10,    # Risk 10% per trade
                stop_loss_pct=0.5,      # Stop loss at 0.5%
                take_profit_pct=1.0,    # Take profit at 1.0%
            )
            
        elif choice == "2":
            if not os.path.exists("config/oanda_live.cfg"):
                print("Live config not found!")
                return
                
            print("\n⚠️ WARNING: This will trade with real money! ⚠️")
            print("Current balance: $4.00")
            confirm = input("Type 'yes' to confirm: ").strip().lower()
            
            if confirm != 'yes':
                print("Cancelled. Switching to practice account for safety.")
                shutil.copy2("config/oanda_practice.cfg", "oanda.cfg")
                
                # Create practice trader
                trader = BasicTrader(
                    cfg="oanda.cfg",
                    risk_per_trade=0.10,
                    stop_loss_pct=0.5,
                    take_profit_pct=1.0,
                )
            else:
                shutil.copy2("config/oanda_live.cfg", "oanda.cfg")
                print("\nUsing LIVE account with safe settings")
                
                # Create live trader with conservative settings
                trader = BasicTrader(
                    cfg="oanda.cfg",
                    risk_per_trade=0.05,    # Risk 5% ($0.20) per trade
                    stop_loss_pct=0.25,     # Stop loss at 0.25%
                    take_profit_pct=0.5,    # Take profit at 0.5%
                )
        else:
            print("Invalid choice!")
            return
            
        # Start trading
        trader.run()
        
    except KeyboardInterrupt:
        print("\nTrading stopped by user.")
    except EOFError:
        print("\nInput stream closed.")
    except Exception as e:
        print(f"\nError occurred: {str(e)}")

if __name__ == "__main__":
    main()
