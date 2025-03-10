from tpqoa import tpqoa
from datetime import datetime, timedelta
import os
import shutil

def copy_config(src, dst):
    shutil.copy2(src, dst)

def switch_account():
    print("\nChoose account type:")
    print("1: Practice Account (recommended for testing)")
    print("2: Live Account (real money trading)")
    
    while True:
        choice = input("\nEnter choice (1 or 2): ")
        if choice == "1":
            if os.path.exists("config/oanda_practice.cfg"):
                copy_config("config/oanda_practice.cfg", "oanda.cfg")
                print("\nSwitched to PRACTICE account (no real money risk)")
                return "practice"
            else:
                print("Practice config not found!")
        elif choice == "2":
            if os.path.exists("config/oanda_live.cfg"):
                print("\n⚠️ WARNING: Switching to LIVE account - Real money will be traded! ⚠️")
                print("Current balance: $4.00")
                confirm = input("Type 'yes' to confirm you want to trade with real money: ")
                if confirm.lower() == 'yes':
                    copy_config("config/oanda_live.cfg", "oanda.cfg")
                    print("Switched to LIVE account")
                    return "live"
                else:
                    print("Staying on practice account for safety")
                    copy_config("config/oanda_practice.cfg", "oanda.cfg")
                    return "practice"
            else:
                print("Live config not found!")
        
        print("Invalid choice, please try again")

if __name__ == "__main__":
    while True:
        # First ensure config directory exists
        if not os.path.exists('config'):
            os.makedirs('config')
            
        # Switch between practice and live accounts
        account_type = switch_account()
        
        try:
            # Connect to OANDA
            oanda = tpqoa("oanda.cfg")
            
            # Get available instruments
            print("\nEnter an instrument to trade (index or pair name):")
            choices = []
            for index, instrument in enumerate(oanda.get_instruments()):
                temp = instrument[1]
                choices.append(temp)
                print(f"({index}: {temp})", end=", ")

            # Get instrument choice
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
            
            mode = input("\n")
            while mode not in ["1", "2", "3"]:
                mode = input("Please choose between 1, 2, or 3: ")

            # Set up stop datetime for week trading
            stop_datetime = None
            if mode == "2":
                stop_datetime = datetime.now() + timedelta(days=7)
                print(f"\nTrading will stop at: {stop_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                mode = "1"  # Treat week trading as live trading with stop datetime

            # Choose strategy and parameters
            if mode == "1":  # Live Trading
                live_strategies = ["sma", "bollinger_bands", "contrarian", "momentum", "ml_classification"]
                print("\nChoose strategy:")
                for strategy in live_strategies:
                    print(strategy, end=", ")
                
                strategy = input("\n").lower()
                while strategy not in live_strategies:
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

                if strategy == "sma":
                    print("\nEnter SMAS value (e.g., 5):")
                    smas = int(input())
                    print("\nEnter SMAL value (e.g., 15):")
                    smal = int(input())
                    while smal < smas:
                        smal = int(input("SMAL must be larger than SMAS: "))

                    from livetrading.SMALive import SMALive
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

                    from livetrading.BollingerBandsLive import BollingerBandsLive
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

                    from livetrading.MomentumLive import MomentumLive
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

                    from livetrading.ContrarianLive import ContrarianLive
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

                    from livetrading.MLClassificationLive import MLClassificationLive
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

            else:  # Backtesting
                backtesting_strategies = ["sma", "bollinger_bands", "contrarian", "momentum", "ml_classification"]
                print("\nChoose strategy to backtest:")
                for strategy in backtesting_strategies:
                    print(strategy, end=", ")

                strategy = input("\n").lower()
                while strategy not in backtesting_strategies:
                    strategy = input("Please choose a strategy listed above: ").lower()

                print("\nEnter start date (YYYY-MM-DD):")
                start = input()

                print("\nEnter end date (YYYY-MM-DD):")
                end = input()
                while datetime.strptime(start, '%Y-%m-%d') > datetime.strptime(end, '%Y-%m-%d'):
                    end = input("End date must be after start date: ")

                print("\nEnter trading cost (e.g., 0.0007):")
                trading_cost = float(input())

                print("\nEnter granularity (e.g., \"S30\", \"M1\", \"H1\"):")
                granularity = input()

                if strategy == "sma":
                    print("\nEnter SMAS value:")
                    smas = int(input())
                    print("\nEnter SMAL value:")
                    smal = int(input())
                    while smal < smas:
                        smal = int(input("SMAL must be larger than SMAS: "))

                    from backtesting.SMABacktest import SMABacktest
                    trader = SMABacktest(instrument, start, end, smas, smal, granularity, trading_cost)
                    trader.test()
                    trader.optimize()
                    trader.plot_results()

                elif strategy == "bollinger_bands":
                    print("\nEnter SMA value:")
                    sma = int(input())
                    print("\nEnter deviation value:")
                    deviation = int(input())

                    from backtesting.BollingerBandsBacktest import BollingerBandsBacktest
                    trader = BollingerBandsBacktest(instrument, start, end, sma, deviation, granularity, trading_cost)
                    trader.test()
                    trader.optimize()
                    trader.plot_results()

                elif strategy == "momentum":
                    print("\nEnter window value:")
                    window = int(input())

                    from backtesting.MomentumBacktest import MomentumBacktest
                    trader = MomentumBacktest(instrument, start, end, window, granularity, trading_cost)
                    trader.test()
                    trader.optimize()
                    trader.plot_results()

                elif strategy == "contrarian":
                    print("\nEnter window value:")
                    window = int(input())

                    from backtesting.ContrarianBacktest import ContrarianBacktest
                    trader = ContrarianBacktest(instrument, start, end, window, granularity, trading_cost)
                    trader.test()
                    trader.optimize()
                    trader.plot_results()

                elif strategy == "ml_classification":
                    from backtesting.MLClassificationBacktest import MLClassificationBacktest
                    trader = MLClassificationBacktest(instrument, start, end, granularity, trading_cost)
                    trader.test()
                    trader.plot_results()

        except Exception as e:
            print(f"\nError occurred: {str(e)}")
            print("Please try again.")
