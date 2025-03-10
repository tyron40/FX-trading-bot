from tpqoa import tpqoa
from datetime import datetime, timedelta

from livetrading.BollingerBandsLive import BollingerBandsLive
from livetrading.ContrarianLive import ContrarianLive
from livetrading.MLClassificationLive import MLClassificationLive
from livetrading.MomentumLive import MomentumLive
from livetrading.SMALive import SMALive

from backtesting.ContrarianBacktest import ContrarianBacktest
from backtesting.BollingerBandsBacktest import BollingerBandsBacktest
from backtesting.MomentumBacktest import MomentumBacktest
from backtesting.SMABacktest import SMABacktest
from backtesting.MLClassificationBacktest import MLClassificationBacktest


if __name__ == "__main__":
    while True:
        # step 1 ensure they have this
        cfg = "oanda.cfg"

        # step 1.5 open oanda connection
        oanda = tpqoa("oanda.cfg")

        # step 2 decide instrument
        print("Enter an instrument to trade (index or pair name): \n")
        choices = []
        
        for index, instrument in enumerate(oanda.get_instruments()):
            temp = instrument[1]
            choices.append(temp)
            print(f"({index}: {temp})", end=", ")

        print("")
        choice = input("\n")
        
        while True:
            if choice not in choices:
                try:
                    val = int(choice)
                    if val < len(choices) and val >= 0:
                        choice = choices[val]
                        break
                except:
                    pass
                choice = input("Please choose an instrument from the list above: ")
            else:
                break

        instrument = choice
        print(f"Instrument: {instrument}")

        # step 3 decide trading mode
        print("\nChoose trading mode:")
        print("1: Live Trading (continuous)")
        print("2: Week Trading (stops after 7 days)")
        print("3: Backtesting")
        
        mode = input("\n")
        while mode not in ["1", "2", "3"]:
            mode = input("Please choose between 1, 2, or 3: ")

        # Set up stop datetime for week trading
        stop_datetime = None
        if mode == "2":
            stop_datetime = datetime.now() + timedelta(days=7)
            print(f"\nTrading will stop at: {stop_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            mode = "1"  # Treat week trading as live trading with stop datetime

        # step 4 choose strategy
        if mode == "1":  # Live Trading
            live_strategies = ["sma", "bollinger_bands", "contrarian", "momentum", "ml_classification"]
            print("\nPlease choose the strategy you would like to utilize:")
            for strategy in live_strategies:
                print(strategy, end=", ")
            
            strategy = input("\n").lower()
            while strategy not in live_strategies:
                strategy = input("Please choose a strategy listed above: ").lower()

            print("\nPlease enter the granularity for your session (e.g., \"1hr\", \"1m\", \"30s\"):")
            granularity = input()

            print("\nPlease enter the number of units to trade with (e.g., 1907 for ~$20):")
            units = int(input())

            print("\nEnter stop profit dollars (e.g., 25) or \"n\" for none:")
            stop_profit = input()
            stop_profit = float(stop_profit) if stop_profit != "n" else None

            print("\nEnter stop loss dollars (e.g., -5) or \"n\" for none:")
            stop_loss = input()
            stop_loss = float(stop_loss) if stop_loss != "n" else None

            if strategy == "sma":
                print("\nEnter SMAS value (e.g., 5):")
                smas = int(input())
                print("\nEnter SMAL value (e.g., 15):")
                smal = int(input())
                while smal < smas:
                    smal = int(input("SMAL must be larger than SMAS: "))

                trader = SMALive(
                    cfg=cfg,
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
                    cfg=cfg,
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
                    cfg=cfg,
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
                    cfg=cfg,
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
                    cfg=cfg,
                    instrument=instrument,
                    bar_length=granularity,
                    lags=lags,
                    units=units,
                    stop_loss=stop_loss,
                    stop_profit=stop_profit,
                    stop_datetime=stop_datetime
                )

        else:  # Backtesting
            backtesting_strategies = ["sma", "bollinger_bands", "contrarian", "momentum", "ml_classification", "ml_regression"]
            print("\nPlease choose the strategy to backtest:")
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

                trader = SMABacktest(instrument, start, end, smas, smal, granularity, trading_cost)
                trader.test()
                trader.optimize()
                trader.plot_results()

            elif strategy == "bollinger_bands":
                print("\nEnter SMA value:")
                sma = int(input())
                print("\nEnter deviation value:")
                deviation = int(input())

                trader = BollingerBandsBacktest(instrument, start, end, sma, deviation, granularity, trading_cost)
                trader.test()
                trader.optimize()
                trader.plot_results()

            elif strategy == "momentum":
                print("\nEnter window value:")
                window = int(input())

                trader = MomentumBacktest(instrument, start, end, window, granularity, trading_cost)
                trader.test()
                trader.optimize()
                trader.plot_results()

            elif strategy == "contrarian":
                print("\nEnter window value:")
                window = int(input())

                trader = ContrarianBacktest(instrument, start, end, window, granularity, trading_cost)
                trader.test()
                trader.optimize()
                trader.plot_results()

            elif strategy == "ml_classification":
                trader = MLClassificationBacktest(instrument, start, end, granularity, trading_cost)
                trader.test()
                trader.plot_results()
