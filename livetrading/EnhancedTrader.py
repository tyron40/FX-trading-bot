from livetrading.LiveTrader import LiveTrader
from helpers.enhanced_market_analyzer import EnhancedMarketAnalyzer

class EnhancedTrader(LiveTrader):
    def __init__(self, *args, **kwargs):
        """Initialize with enhanced market analysis capabilities."""
        super().__init__(*args, **kwargs)
        self._market_analyzer = EnhancedMarketAnalyzer()
        print("\nEnhanced Market Analysis Enabled:")
        print("- Real-time news analysis")
        print("- Multiple source sentiment")
        print("- Technical signal confirmation")
        
    def on_success(self, time, bid, ask):
        """Process new tick data with enhanced market analysis."""
        print(time, bid, ask)

        recent_tick = pd.to_datetime(time)
        stopped = False

        # Check stop conditions
        if self._stop_datetime and recent_tick >= self._stop_datetime:
            self.stop_stream = True
            self.close_position()
            stopped = True

        if self._stop_loss and self._profit < self._stop_loss:
            self.stop_stream = True
            self.close_position()
            stopped = True

        if self._stop_profit and self._profit > self._stop_profit:
            self.stop_stream = True
            self.close_position()
            stopped = True

        if stopped:
            print("Stop triggered, ending stream.")
            return

        # Process tick data
        df = pd.DataFrame(
            {
                "bid_price": bid,
                "ask_price": ask,
                "mid_price": (ask + bid) / 2,
                "spread": ask - bid,
            },
            index=[recent_tick],
        )
        self._tick_data = pd.concat([self._tick_data, df])

        # Update data when bar completes
        if (recent_tick - self._last_tick) >= self._bar_length:
            self._raw_data = pd.concat([
                self._raw_data,
                self._tick_data.resample(self._bar_length, label="right")
                .last()
                .ffill()
                .iloc[:-1]
            ])

            self._tick_data = self._tick_data.iloc[-1:]
            self._last_tick = self._raw_data.index[-1]

            # Get strategy signal
            self.define_strategy()
            
            # Get market sentiment and combine with strategy
            if hasattr(self, '_data') and len(self._data) > 0:
                technical_signal = self._data["position"].iloc[-1]
                final_signal = self._market_analyzer.get_trading_signal(
                    self._instrument,
                    technical_signal
                )
                self._data.at[self._data.index[-1], "position"] = final_signal
                
            self.trade()

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
