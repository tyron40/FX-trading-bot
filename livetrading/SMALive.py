import numpy as np
from helpers.market_analyzer import MarketAnalyzer
from livetrading.LiveTrader import LiveTrader


class SMALive(LiveTrader):
    def __init__(
        self,
        cfg,
        instrument,
        bar_length,
        smas,
        smal,
        units,
        stop_datetime=None,
        stop_loss=None,
        stop_profit=None,
    ):
        """
        Initializes the SMALive object.

        Args:
            cfg (object): An object representing the OANDA connection
            instrument (string): A string holding the ticker instrument of instrument to be tested
            bar_length (string): Length of each candlestick for the respective instrument
            smas (int): A value for the # of days the Simple Moving Average lags (Shorter) should consider
            smal (int): A value for the # of days the Simple Moving Average lags (Longer) should consider
            stop_datetime (object) <DEFAULT = None>: A datetime object that when passed stops trading
            stop_loss (float) <DEFAULT = None>: A stop loss that when profit goes below stops trading
            stop_profit (float) <DEFAULT = None>: A stop profit that when profit goes above stops trading
        """
        # these should be in terms of minutes
        self._smas = smas
        self._smal = smal

        self._position = 0  # Initialize position
        self._market_analyzer = MarketAnalyzer()  # Initialize market analyzer
        super().__init__(
            cfg,
            instrument,
            bar_length,
            units,
            stop_datetime=stop_datetime,
            stop_loss=stop_loss,
            stop_profit=stop_profit,
        )

    def define_strategy(self):
        data = self._raw_data.copy()
        data["smas"] = data["mid_price"].rolling(self._smas).mean()
        data["smal"] = data["mid_price"].rolling(self._smal).mean()
        # Calculate additional indicators for more accuracy
        data["momentum"] = data["mid_price"].diff(3).fillna(0)  # Short-term momentum
        data["volatility"] = data["mid_price"].rolling(5).std()  # Short-term volatility
        
        # Calculate trend strength
        data["trend_strength"] = abs(data["smas"] - data["smal"]) / data["volatility"]
        
        # Get base technical signal
        technical_signal = np.where(
            # Strong uptrend conditions
            (data["smas"] > data["smal"]) &  # Short MA above Long MA
            (data["mid_price"] > data["smal"]) &  # Price above Long MA
            (data["momentum"] > 0) &  # Positive momentum
            (data["trend_strength"] > 1.0),  # Strong trend
            1,  # Go long
            np.where(
                # Strong downtrend conditions
                (data["smas"] < data["smal"]) &  # Short MA below Long MA
                (data["mid_price"] < data["smal"]) &  # Price below Long MA
                (data["momentum"] < 0) &  # Negative momentum
                (data["trend_strength"] > 1.0),  # Strong trend
                -1,  # Go short
                0  # Stay neutral
            )
        )

        # Combine technical signal with market sentiment
        data["position"] = self._market_analyzer.get_trading_signal(
            self._instrument,
            technical_signal
        )
        
        self._data = data.dropna().copy()
