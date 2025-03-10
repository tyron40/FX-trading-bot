import os
import shutil
from datetime import datetime, timedelta
from livetrading.SmartAutoTrader import SmartAutoTrader
from livetrading.BollingerBandsLive import BollingerBandsLive
from livetrading.ContrarianLive import ContrarianLive
from livetrading.MLClassificationLive import MLClassificationLive
from livetrading.MomentumLive import MomentumLive
from livetrading.SMALive import SMALive

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
            account_type = "practice"
            
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
                account_type = "practice"
            else:
                shutil.copy2("config/oanda_live.cfg", "oanda.cfg")
                print("\nUsing LIVE account with safe settings")
                account_type = "live"
        else:
            print("Invalid choice!")
            return

        # Ask for trading mode
        print("\nWould you like to enable auto trading?")
        print("1: Yes - Let the bot trade automatically")
        print("2: No - I want to control trading manually")
        
        mode = input("\nEnter choice (1 or 2): ").strip()
        
        if mode == "1":
            # Auto trading mode with smart features
            if account_type == "live":
                print("\nStarting Smart Auto Trader with safe settings for $4 account...")
                trader = SmartAutoTrader(
                    cfg="oanda.cfg",
                    risk_per_trade=0.05,    # Risk 5% ($0.20) per trade
                    stop_loss_pct=0.25,     # Stop loss at 0.25%
                    take_profit_pct=0.5,    # Take profit at 0.5%
                    max_positions=2         # Maximum 2 positions at once
                )
            else:
                print("\nStarting Smart Auto Trader with practice settings...")
                trader = SmartAutoTrader(
                    cfg="oanda.cfg",
                    risk_per_trade=0.10,    # Risk 10% per trade
                    stop_loss_pct=0.5,      # Stop loss at 0.5%
                    take_profit_pct=1.0,    # Take profit at 1.0%
                    max_positions=3         # Maximum 3 positions at once
                )
            trader.run()
            
        elif mode == "2":
            # Manual trading mode
            from tpqoa import tpqoa
            oanda = tpqoa("oanda.cfg")
            
            # Get available instruments
            print("\nEnter an instrument to trade (index or pair name):")
            choices = []
            for index, instrument in enumerate(oanda.get_instruments()):
                temp = instrument[1]
                choices.append(temp)
                print(f"({index}: {temp})", end=", ")

            print("")
            choice = input("\n")
            while choice not in choices:
                try:
                    val = int(choice)
                    if val < len(choices) and val >= 0:
                        choice = choices[val]
                        break
                except:
                    pass
                choice = input("Please choose an instrument from the list above: ")

            instrument = choice
            print(f"\nSelected instrument: {instrument}")

            # Choose trading mode
            print("\nChoose trading mode:")
            print("1: Live Trading (continuous)")
            print("2: Week Trading (stops after 7 days)")
            print("3: Backtesting (recommended for testing)")
            
            trade_mode = input("\n")
            while trade_mode not in ["1", "2", "3"]:
                trade_mode = input("Please choose between 1, 2, or 3: ")

            # Set up stop datetime for week trading
            stop_datetime = None
            if trade_mode == "2":
                stop_datetime = datetime.now() + timedelta(days=7)
                print(f"\nTrading will stop at: {stop_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                trade_mode = "1"  # Treat week trading as live trading with stop datetime

            # Choose strategy
            print("\nChoose strategy:")
            strategies = ["sma", "bollinger_bands", "contrarian", "momentum", "ml_classification"]
            for strat in strategies:
                print(strat, end=", ")
            
            strategy = input("\n").lower()
            while strategy not in strategies:
                strategy = input("Please choose a strategy listed above: ").lower()

            print("\nEnter granularity (e.g., \"1hr\", \"1m\", \"30s\"):")
            granularity = input()

            print("\nEnter number of units to trade:")
            units = int(input())

            print("\nEnter stop profit dollars or \"n\" for none:")
            stop_profit = input()
            stop_profit = float(stop_profit) if stop_profit != "n" else None

            print("\nEnter stop loss dollars or \"n\" for none:")
            stop_loss = input()
            stop_loss = float(stop_loss) if stop_loss != "n" else None

            # Create trader based on strategy
            if strategy == "sma":
                print("\nEnter SMAS value (e.g., 5):")
                smas = int(input())
                print("\nEnter SMAL value (e.g., 15):")
                smal = int(input())
                while smal < smas:
                    smal = int(input("SMAL must be larger than SMAS: "))

                trader = SMALive(
                    cfg="oanda.cfg",
                    instrument=instrument,
                    bar_length=granularity,
                    smas=smas,
                    smal=smal,
                    units=units,
                    stop_loss=stop_loss,
                    stop_profit=stop_profit,
                    stop_datetime=stop_datetime
                )

            elif strategy == "bollinger_bands":
                print("\nEnter SMA value (e.g., 9):")
                sma = int(input())
                print("\nEnter deviation value (e.g., 2):")
                deviation = int(input())

                trader = BollingerBandsLive(
                    cfg="oanda.cfg",
                    instrument=instrument,
                    bar_length=granularity,
                    sma=sma,
                    deviation=deviation,
                    units=units,
                    stop_loss=stop_loss,
                    stop_profit=stop_profit,
                    stop_datetime=stop_datetime
                )

            elif strategy == "momentum":
                print("\nEnter window value (e.g., 3):")
                window = int(input())

                trader = MomentumLive(
                    cfg="oanda.cfg",
                    instrument=instrument,
                    bar_length=granularity,
                    window=window,
                    units=units,
                    stop_loss=stop_loss,
                    stop_profit=stop_profit,
                    stop_datetime=stop_datetime
                )

            elif strategy == "contrarian":
                print("\nEnter window value (e.g., 3):")
                window = int(input())

                trader = ContrarianLive(
                    cfg="oanda.cfg",
                    instrument=instrument,
                    bar_length=granularity,
                    window=window,
                    units=units,
                    stop_loss=stop_loss,
                    stop_profit=stop_profit,
                    stop_datetime=stop_datetime
                )

            elif strategy == "ml_classification":
                print("\nEnter number of lags (e.g., 6):")
                lags = int(input())

                trader = MLClassificationLive(
                    cfg="oanda.cfg",
                    instrument=instrument,
                    bar_length=granularity,
                    lags=lags,
                    units=units,
                    stop_loss=stop_loss,
                    stop_profit=stop_profit,
                    stop_datetime=stop_datetime
                )
            
            # Start trading
            print(f"\nStarting {strategy.upper()} trading...")
            print("Press Ctrl+C to stop")
            trader.run()
            
        else:
            print("Invalid choice!")
            return
            
    except KeyboardInterrupt:
        print("\nTrading stopped by user.")
    except EOFError:
        print("\nInput stream closed.")
    except Exception as e:
        print(f"\nError occurred: {str(e)}")

if __name__ == "__main__":
    main()
