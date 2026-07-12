from backtesting.IterativeBase import IterativeBase


class IterativeBacktest(IterativeBase):

    """Class implementing strategy specific iterative testing functions"""
    def go_long(self, bar, units=None, amount=None):
        if self._position == -1:
            # if short, go neutral first
            self.buy(bar, units=-self._units)
        if units:
            self.buy(bar, units=units)
        elif amount:
            if amount == "all":
                amount = self._current_balance
            self.buy(bar, amount=amount)

    def go_short(self, bar, units=None, amount=None):
        if self._position == 1:
            self.sell(bar, units=self._units)
        if units:
            self.sell(bar, units=units)
        elif amount:
            if amount == "all":
                amount = self._current_balance
            self.sell(bar, amount=amount)

    def reset(self):
        # reset instrument attributes
        self._position = 0
        self._trades = 0
        self._current_balance = self._initial_balance
        self.acquire_data()

    # TODO: Make this inheritable by the strategy, make this file more abstract
    def test_sma(self, smas, smal):
        print(
            f"Testing SMA strategy on {self._instrument} with smas={smas} and smal={smal}"
        )
        self.reset()

        self._data["smas"] = self._data.bid_price.rolling(smas).mean()
        self._data["smal"] = self._data.bid_price.rolling(smal).mean()
        self._data.dropna(inplace=True)

        # sma crossover strategy
        for bar in range(len(self._data) - 1):
            if self._data["smas"].iloc[bar] > self._data["smal"].iloc[bar]:
                # go long
                if self._position in [0, -1]:
                    # go long with entire balance to switch position
                    self.go_long(bar, amount="all")
                    self._position = 1
            elif self._data["smas"].iloc[bar] < self._data["smal"].iloc[bar]:
                # go short
                if self._position in [0, 1]:
                    # go short with entire balance to switch position
                    self.go_short(bar, amount="all")
                    self._position = -1

        self.close_position(bar + 1)

    def test_contrarian(self, window=1):
    

        self.reset()
        # prepares the data
        self._data["rolling_returns"] = self._data["returns"].rolling(window).mean()
        self._data.dropna(inplace=True)

        for bar in range(len(self._data) - 1):
            if self._data["rolling_returns"].iloc[bar] <= 0:
                # go long
                if self._position in [0, -1]:
                    self.go_long(bar, amount="all")
                    self._position = 1
            else:
                # go short
                if self._position in [0, 1]:
                    self.go_short(bar, amount="all")
                    self._position = -1

        self.close_position(bar + 1)

    def test_momentum(self, window=1):
    
        self.reset()

        # prepares the data
        self._data["rolling_returns"] = self._data["returns"].rolling(window).mean()
        self._data.dropna(inplace=True)

        for bar in range(len(self._data) - 1):
            if self._data["rolling_returns"].iloc[bar] <= 0:
                # go short
                if self._position in [0, 1]:
                    self.go_short(bar, amount="all")
                    self._position = -1
            else:
                # go long
                if self._position in [0, -1]:
                    self.go_long(bar, amount="all")
                    self._position = 1

        self.close_position(bar + 1)

    def test_bollinger_bands(self, sma, std=2):
        print(
            f"Testing Bollinger Bands strategy on {self._instrument} with sma={sma}, std={std}"
        )
        self.reset()

        # prepares the data
        self._data["sma"] = self._data.bid_price.rolling(sma).mean()
        self._data["lower"] = self._data["sma"] - (
            self._data.bid_price.rolling(sma).std() * std
        )
        self._data["upper"] = self._data["sma"] + (
            self._data.bid_price.rolling(sma).std() * std
        )

        self._data.dropna(inplace=True)

        for bar in range(len(self._data) - 1):

            if self._position == 0:

                if self._data["bid_price"].iloc[bar] < self._data["lower"].iloc[bar]:
                    # if price is lower than lower band, indicates oversold, and to go long
                    self.go_long(bar, amount="all")
                    self._position = 1
                elif self._data["bid_price"].iloc[bar] > self._data["upper"].iloc[bar]:
                    # if price is higher than upper band, indicates overbought, and to go short
                    self.go_short(bar, amount="all")
                    self._position = -1

            elif self._position == 1:
                if self._data["bid_price"].iloc[bar] > self._data["sma"].iloc[bar]:

                    # if price crosses upper band, signal to go short
                    if (
                        self._data["bid_price"].iloc[bar]
                        > self._data["upper"].iloc[bar]
                    ):
                        self.go_short(bar, amount="all")
                        self._position = -1
                    else:
                        # if price is between sma and upper, just go neutral
                        self.sell(bar, units=self._units)
                        self._position = 0

            elif self._position == -1:
                if self._data["bid_price"].iloc[bar] < self._data["sma"].iloc[bar]:

                    # if price crosses lower band, signal to go long
                    if (
                        self._data["bid_price"].iloc[bar]
                        < self._data["lower"].iloc[bar]
                    ):
                        self.go_long(bar, amount="all")
                        self._position = 1
                    else:
                        # if price is between lower and sma, just go neutral
                        self.buy(bar, units=-self._units)
                        self._position = 0

        self.close_position(bar + 1)

    def test_bullish_rejection_blocks(self, lookback=20, wick_threshold=0.6):
        """
        Test strategy based on bullish rejection blocks (pin bars) and reversals.
        Bullish rejection block: candle with long upper wick, close near low, indicating rejection of higher prices.
        """
        print(f"Testing Bullish Rejection Blocks strategy on {self._instrument} with lookback={lookback}, wick_threshold={wick_threshold}")

        self.reset()

        # Calculate rejection block signals
        self._data['bullish_rejection'] = self._calculate_bullish_rejection_signals(lookback, wick_threshold)
        self._data.dropna(inplace=True)

        for bar in range(len(self._data) - 1):
            signal = self._data['bullish_rejection'].iloc[bar]

            if signal > 0.7:  # Strong bullish rejection signal
                if self._position in [0, -1]:
                    self.go_long(bar, amount="all")
                    self._position = 1
            elif signal < -0.7:  # Strong bearish rejection signal
                if self._position in [0, 1]:
                    self.go_short(bar, amount="all")
                    self._position = -1

        self.close_position(bar + 1)

    def _calculate_bullish_rejection_signals(self, lookback, wick_threshold):
        """Calculate bullish rejection block signals."""
        signals = []

        for i in range(len(self._data)):
            if i < lookback:
                signals.append(0.0)
                continue

            # Get recent candles
            recent_data = self._data.iloc[i-lookback:i+1]

            # Current candle
            current = recent_data.iloc[-1]
            high = current['bid_price']
            low = current['ask_price']  # Using ask as low for simplicity
            open_price = current['bid_price']  # Approximate
            close_price = current['ask_price']  # Approximate

            # Calculate wick lengths
            body_high = max(open_price, close_price)
            body_low = min(open_price, close_price)
            upper_wick = high - body_high
            lower_wick = body_low - low
            body_size = abs(close_price - open_price)

            # Bullish rejection block criteria
            total_range = high - low
            if total_range > 0:
                upper_wick_ratio = upper_wick / total_range
                lower_wick_ratio = lower_wick / total_range

                # Bullish rejection: long upper wick, close near low
                if upper_wick_ratio > wick_threshold and close_price <= (low + total_range * 0.3):
                    # Check trend context (look for downtrend)
                    recent_trend = recent_data['bid_price'].pct_change().mean()
                    if recent_trend < -0.0001:  # Downtrend
                        signals.append(0.8)  # Bullish signal
                    else:
                        signals.append(0.0)
                # Bearish rejection: long lower wick, close near high
                elif lower_wick_ratio > wick_threshold and close_price >= (high - total_range * 0.3):
                    # Check trend context (look for uptrend)
                    recent_trend = recent_data['bid_price'].pct_change().mean()
                    if recent_trend > 0.0001:  # Uptrend
                        signals.append(-0.8)  # Bearish signal
                    else:
                        signals.append(0.0)
                else:
                    signals.append(0.0)
            else:
                signals.append(0.0)

        return pd.Series(signals, index=self._data.index)
