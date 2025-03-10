import numpy as np
from livetrading.LiveTrader import LiveTrader
from helpers.enhanced_market_analyzer import EnhancedMarketAnalyzer

class EnhancedSMALive(LiveTrader):
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
        Enhanced SMA strategy with real-time news analysis.
        """
        self._smas = smas
        self._smal = smal
        self._position = 0
        self._market_analyzer = EnhancedMarketAnalyzer()
        
        print("\nEnhanced Trading Features Enabled:")
        print("- Real-time news analysis")
        print("- Multi-source sentiment tracking")
        print("- Technical signal confirmation")
        print("- Market trend analysis")
        
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
        """Enhanced SMA strategy with market sentiment."""
        data = self._raw_data.copy()

        # Calculate SMAs
        data["smas"] = data["mid_price"].rolling(self._smas).mean()
        data["smal"] = data["mid_price"].rolling(self._smal).mean()
        
        # Calculate additional indicators
        data["momentum"] = data["mid_price"].diff(3).fillna(0)
        data["volatility"] = data["mid_price"].rolling(5).std()
        data["trend_strength"] = abs(data["smas"] - data["smal"]) / data["volatility"]

        # Get base technical signal
        conditions_long = (
            (data["smas"] > data["smal"]) &  # Uptrend
            (data["momentum"] > 0) &  # Positive momentum
            (data["trend_strength"] > 1.0)  # Strong trend
        )
        
        conditions_short = (
            (data["smas"] < data["smal"]) &  # Downtrend
            (data["momentum"] < 0) &  # Negative momentum
            (data["trend_strength"] > 1.0)  # Strong trend
        )

        # Generate base signals
        data["position"] = np.where(
            conditions_long, 1,
            np.where(conditions_short, -1, 0)
        )

        # Get market sentiment and adjust signal
        if len(data) > 0:
            technical_signal = data["position"].iloc[-1]
            sentiment = self._market_analyzer.get_trading_signal(
                self._instrument,
                technical_signal
            )
            data.at[data.index[-1], "position"] = sentiment

        # Print analysis
        latest = data.iloc[-1]
        print(f"\nMarket Analysis:")
        print(f"Current Price: {latest['mid_price']:.3f}")
        print(f"Fast SMA: {latest['smas']:.3f}")
        print(f"Slow SMA: {latest['smal']:.3f}")
        print(f"Momentum: {latest['momentum']:.5f}")
        print(f"Trend Strength: {latest['trend_strength']:.2f}")
        print(f"Position Signal: {latest['position']}")

        self._data = data.copy()

    def trade_report(self, order, position):
        """Enhanced trade reporting with market analysis."""
        time = order["time"]
        units = order["units"]
        price = order["price"]
        profit = float(order["pl"])
        self._profits.append(profit)
        cum_profits = sum(self._profits)
        self._profit = cum_profits

        # Get current market analysis
        sentiment = self._market_analyzer.get_market_sentiment(self._instrument)
        
        print("\n=== Trade Report ===")
        print(f"Time: {time}")
        print(f"Position: {position}")
        print(f"Units: {units}")
        print(f"Price: ${price}")
        print(f"Profit: ${profit:.4f}")
        print(f"Cumulative Profit: ${cum_profits:.4f}")
        
        if sentiment:
            print("\nMarket Analysis:")
            print(f"Sentiment Score: {sentiment['sentiment_score']:.2f}")
            print(f"Recent News ({sentiment['news_count']} articles):")
            for item in sentiment['news_items']:
                print(f"- {item['title']} ({item['source']})")
            
            if 'technical_analysis' in sentiment:
                print("\nTechnical Signals:")
                for signal in sentiment['technical_analysis']:
                    print(f"- {signal['indicator']}: {signal['signal']} ({signal['strength']})")
