import os
import shutil
import sys
from datetime import datetime, timedelta
from FemtoTrader_new import FemtoTrader
from livetrading.BollingerBandsLive import BollingerBandsLive
from livetrading.ContrarianLive import ContrarianLive
from livetrading.MLClassificationLive import MLClassificationLive
from livetrading.MomentumLive import MomentumLive
from livetrading.SMALive import SMALive
from helpers.enhanced_market_analyzer import EnhancedMarketAnalyzer

def main():
    # Check for command line arguments for non-interactive mode
    if len(sys.argv) > 1:
        if sys.argv[1] == 'auto':
            # Auto mode: live account, auto trading, ongoing with GUI
            account_type = "live"
            mode = "auto"
            duration = "ongoing"
            # Set up live config
            if not os.path.exists("config/oanda_live.cfg"):
                print("Live config not found!")
                return
            shutil.copy2("config/oanda_live.cfg", "oanda.cfg")
            print("\nUsing LIVE account with safe settings")
            print("Launching GUI dashboard...")

            # Import and launch GUI
            from trading_gui import main as gui_main
            import threading

            # Start GUI in separate thread
            gui_thread = threading.Thread(target=gui_main, daemon=True)
            gui_thread.start()

            # Wait a moment for GUI to initialize
            import time
            time.sleep(2)

            # Start auto trader (GUI will handle the trader instance)
            print("Auto trading will be controlled through the GUI dashboard.")
            print("Use the GUI to start/stop trading.")
            print("Press Ctrl+C in terminal to exit.")

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nExiting...")
                return
        else:
            print("Usage: python main_final.py [auto]")
            return

    try:
        # Ensure config directory exists
        if not os.path.exists('config'):
            os.makedirs('config')
        
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

            # Fetch actual balance
            try:
                from tpqoa.tpqoa import tpqoa
                temp_oanda = tpqoa("config/oanda_live.cfg")
                summary = temp_oanda.get_account_summary()
                balance = float(summary.get('balance', 4.00))
                print(f"\n⚠️ WARNING: This will trade with real money! ⚠️")
                print(f"Current balance: ${balance:.2f}")
                confirm = input("Type 'yes' to confirm: ").strip().lower()
            except Exception as e:
                print(f"Error fetching balance: {e}")
                print("Current balance: $4.00 (fallback)")
                balance = 4.00
                confirm = input("Type 'yes' to confirm: ").strip().lower()
            
            if confirm != 'yes':
                print("Cancelled. Switching to practice account for safety.")
                shutil.copy2("config/oanda_practice.cfg", "oanda.cfg")
                account_type = "practice"
            else:
                shutil.copy2("config/oanda_live.cfg", "oanda.cfg")
                print(f"\nUsing LIVE account (${balance:.2f}) with safe settings")
                account_type = "live"
        else:
            print("Invalid choice!")
            return
                
        # Ask for trading mode
        print("\nWould you like to enable auto trading?")
        print("1: Yes - Let the bot trade automatically")
        print("2: No - I want to control trading manually")

        mode = input("\nEnter choice (1 or 2, or 'yes'/'no'): ").strip().lower()

        if mode in ["1", "yes"]:
            # Auto trading mode - choose duration
            print("\nChoose trading duration:")
            print("1: Ongoing (continuous trading)")
            print("2: Monthly (30 days)")
            print("3: Yearly (365 days)")

            duration_choice = input("\nEnter choice (1, 2, or 3): ").strip()

            stop_datetime = None
            if duration_choice == "2":
                stop_datetime = datetime.now() + timedelta(days=30)
                print(f"\nTrading will stop at: {stop_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            elif duration_choice == "3":
                stop_datetime = datetime.now() + timedelta(days=365)
                print(f"\nTrading will stop at: {stop_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            elif duration_choice != "1":
                print("Invalid choice! Defaulting to ongoing trading.")

            if account_type == "live":
                print("\nStarting Smart Auto Trader with safe settings for $4 account...")
                trader = FemtoTrader(
                    cfg="oanda.cfg",
                    risk_per_trade=0.05,    # Risk 5% ($0.20) per trade
                    stop_loss_pct=0.25,     # Stop loss at 0.25%
                    take_profit_pct=0.5,    # Take profit at 0.5%
                )
            else:
                print("\nStarting Smart Auto Trader with practice settings...")
                trader = FemtoTrader(
                    cfg="oanda.cfg",
                    risk_per_trade=0.10,    # Risk 10% per trade
                    stop_loss_pct=0.5,      # Stop loss at 0.5%
                    take_profit_pct=1.0,    # Take profit at 1.0%
                )

            # Modify trader to include stop_datetime if set
            if stop_datetime:
                trader._stop_datetime = stop_datetime

            trader.run()
                
        elif mode == "2":
            # Manual trading mode
            from tpqoa.tpqoa import tpqoa
            oanda = tpqoa("oanda.cfg")
            market_analyzer = EnhancedMarketAnalyzer()
            
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

            # Get market sentiment
            sentiment = market_analyzer.get_market_sentiment(instrument)
            if sentiment:
                print("\nCurrent Market Analysis:")
                print(f"Sentiment Score: {sentiment['sentiment_score']:.2f}")
                print(f"Recent News ({sentiment['news_count']} articles):")
                for item in sentiment['news_items'][:3]:
                    print(f"- {item['title']} ({item['source']})")

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

            if account_type == "live":
                print("\nRecommended safe settings for $4 account:")
                print("- Units: 100 (about $1 per trade)")
                print("- Stop loss: -$0.25")
                print("- Take profit: +$0.50")

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
        print("Please try again.")

if __name__ == "__main__":
    main()
