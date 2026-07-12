from tpqoa.tpqoa import tpqoa
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from helpers.rss_market_analyzer import RSSMarketAnalyzer

class FemtoTrader(tpqoa):
    def __init__(
        self,
        cfg,
        risk_per_trade=0.05,  # 5% of available balance per trade
        stop_loss_pct=0.25,   # 0.25% stop loss
        take_profit_pct=0.5,  # 0.5% take profit
    ):
        """
        Smart auto trader with RSS-based market analysis.
        """
        super().__init__(cfg)

        self._market_analyzer = RSSMarketAnalyzer()
        self._position = None  # Current position
        self._risk_per_trade = risk_per_trade
        self._stop_loss_pct = stop_loss_pct
        self._take_profit_pct = take_profit_pct
        self._pair = 'EUR_USD'  # Focus on EUR/USD

        # Get account info
        try:
            summary = self.get_account_summary()
            self._balance = float(summary.get('balance', 1000.0))
        except Exception as e:
            print(f"Warning: Error getting account balance: {str(e)}")
            self._balance = 1000.0

        print(f"\nAccount Balance: ${self._balance:.2f}")
        print(f"\nTrading {self._pair} with:")
        print("\nRSS-Based Analysis Sources:")
        print("- ECB (European Central Bank)")
        print("- Federal Reserve (Fed)")
        print("- Bank of England (BoE)")
        print("- IMF, World Bank, OECD")
        print("- CNBC, Financial Times, Reuters")
        print("- Bank of Canada, RBA Australia, SNB Swiss")
        print("\nTrading Features:")
        print("- Real-time RSS market analysis")
        print("- Multi-source sentiment analysis")
        print("- Central bank policy tracking")
        print("- Dynamic position sizing")
        print("- Automatic risk management")
        print(f"- {risk_per_trade*100}% risk per trade")
        print(f"- {stop_loss_pct}% stop loss")
        print(f"- {take_profit_pct}% take profit")

        # GUI callbacks for thread-safe updates
        self._gui_callbacks = {
            'price': None,
            'signal': None,
            'news': None,
            'technical': None,
            'position': None,
            'history': None
        }

    def set_gui_callbacks(self, price_callback=None, signal_callback=None, news_callback=None,
                         technical_callback=None, position_callback=None, history_callback=None):
        """Set GUI callback functions for thread-safe updates"""
        self._gui_callbacks['price'] = price_callback
        self._gui_callbacks['signal'] = signal_callback
        self._gui_callbacks['news'] = news_callback
        self._gui_callbacks['technical'] = technical_callback
        self._gui_callbacks['position'] = position_callback
        self._gui_callbacks['history'] = history_callback

    def _get_history_df(self):
        """Get historical data for analysis."""
        try:
            # Get candles from API - try more candles to ensure we have enough complete ones
            response = self.ctx.instrument.candles(
                self._pair,
                granularity="M1",
                count=30,  # Get more candles to ensure we have enough complete ones
                price="M"
            )

            if response.status != 200:
                print(f"Error getting candles: {response.body}")
                return None

            # Extract candle data
            data = []
            for candle in response.body.get('candles', []):
                if candle.complete:  # Only use complete candles
                    data.append({
                        'time': pd.to_datetime(candle.time),
                        'open': float(candle.mid.o),
                        'high': float(candle.mid.h),
                        'low': float(candle.mid.l),
                        'close': float(candle.mid.c),
                        'volume': int(candle.volume)
                    })

            # Need at least 5 complete candles for analysis
            if len(data) < 5:
                print(f"Only {len(data)} complete candles available, need at least 5")
                return None

            df = pd.DataFrame(data[-10:])  # Use the last 10 complete candles
            df.set_index('time', inplace=True)
            return df

        except Exception as e:
            print(f"Error getting history: {str(e)}")
            return None

    def _analyze_market(self):
        """Analyze market using RSS-based data sources."""
        try:
            # Get price data
            df = self._get_history_df()
            if df is None or len(df) < 5:  # Reduced requirement to 5 candles minimum
                print("Insufficient price data for analysis")
                return None

            # Calculate technical indicators
            prices = df.close.values
            sma5 = np.mean(prices[-5:])
            sma10 = np.mean(prices[-10:]) if len(prices) >= 10 else sma5
            momentum = prices[-1] - prices[-3] if len(prices) >= 3 else 0
            volatility = np.std(prices[-5:])

            # Calculate technical score first (always available)
            technical_score = 0
            if sma5 > sma10 and momentum > 0:
                technical_score = 1
            elif sma5 < sma10 and momentum < 0:
                technical_score = -1

            # Try to get market sentiment from RSS feeds
            sentiment = self._market_analyzer.get_market_sentiment(self._pair)
            sentiment_score = 0  # Default neutral sentiment

            if sentiment and 'sentiment_score' in sentiment:
                sentiment_score = sentiment['sentiment_score']
                print(f"RSS sentiment: {sentiment_score:.2f} (from {sentiment.get('news_count', 0)} news + {sentiment.get('central_bank_news', 0)} CB items)")
            else:
                print("Using technical analysis only (RSS data unavailable)")
                # Use technical score as primary signal when RSS fails
                sentiment_score = technical_score * 0.5  # Reduce confidence

            # Combine technical and sentiment scores
            # Weight: 60% technical, 40% sentiment (when available)
            if sentiment and sentiment_score != 0:
                strength = (technical_score * 0.6) + (sentiment_score * 0.4)
            else:
                strength = technical_score * 0.8  # Technical only, slightly reduced confidence

            analysis_result = {
                'strength': abs(strength),
                'direction': 1 if strength > 0 else -1,
                'volatility': volatility,
                'sentiment': sentiment or {'sentiment_score': 0, 'news_count': 0, 'news_items': []},
                'current_price': prices[-1],
                'technical_score': technical_score
            }

            print(f"Analysis: Strength={analysis_result['strength']:.2f}, Direction={'Long' if analysis_result['direction'] > 0 else 'Short'}")
            return analysis_result

        except Exception as e:
            print(f"Error analyzing market: {str(e)}")
            return None

    def _calculate_position_size(self, volatility):
        """Calculate safe position size based on volatility."""
        try:
            # Get current price
            time, bid, ask = self.get_prices(self._pair)
            price = bid

            # Calculate risk amount
            risk_amount = self._balance * self._risk_per_trade

            # Adjust position size based on volatility
            volatility_factor = 1 / (1 + volatility)
            adjusted_risk = risk_amount * volatility_factor

            # Calculate stop loss in pips
            stop_loss_pips = price * self._stop_loss_pct / 100

            # Calculate position size
            units = int(adjusted_risk / stop_loss_pips)

            # Ensure minimum/maximum units
            return max(100, min(units, 100000))

        except Exception as e:
            print(f"Error calculating position size: {str(e)}")
            return 100

    def manage_trades(self):
        """Manage existing position and look for new opportunities."""
        try:
            if self._position:
                # Check existing position
                time, bid, ask = self.get_prices(self._pair)
                current_price = bid
                entry_price = self._position['entry_price']

                # Calculate profit/loss
                if self._position['type'] == 'long':
                    profit_pct = (current_price - entry_price) / entry_price * 100
                else:
                    profit_pct = (entry_price - current_price) / entry_price * 100

                # Check stop loss
                if profit_pct <= -self._stop_loss_pct:
                    print(f"\nClosing position at stop loss")
                    self.close_position()
                    return

                # Check take profit
                if profit_pct >= self._take_profit_pct:
                    print(f"\nClosing position at take profit")
                    self.close_position()
                    return

                # Check if conditions changed significantly
                analysis = self._analyze_market()
                if analysis:
                    current_signal = analysis['direction'] * analysis['strength']
                    # Only close if signal reverses strongly (opposite direction with strength > 0.8)
                    if (self._position['type'] == 'long' and current_signal < -0.8) or \
                       (self._position['type'] == 'short' and current_signal > 0.8):
                        print(f"\nClosing position - strong signal reversal")
                        self.close_position()
                        return

            else:
                # Look for new opportunity
                analysis = self._analyze_market()
                if analysis and analysis['strength'] > 0.7:  # Increased threshold from 0.3 to 0.7
                    # Additional confirmation: require sentiment data if available
                    sentiment = analysis['sentiment']
                    has_sentiment_data = sentiment and sentiment.get('news_count', 0) > 0

                    # If we have sentiment data, require stronger technical signal
                    min_strength = 0.8 if has_sentiment_data else 0.7

                    if analysis['strength'] >= min_strength:
                        print(f"\nFound trading opportunity")
                        print(f"Strength: {analysis['strength']:.2f}")
                        print(f"Direction: {'Long' if analysis['direction'] > 0 else 'Short'}")
                        print(f"Current Price: ${analysis['current_price']:.5f}")

                        print("\nMarket Analysis:")
                        print(f"Sentiment Score: {sentiment['sentiment_score']:.2f}")

                        if sentiment['news_items']:
                            print(f"\nLatest News ({sentiment['news_count']} articles):")
                            for item in sentiment['news_items'][:3]:
                                print(f"- {item['title']} ({item['source']})")

                        if sentiment.get('central_bank_updates'):
                            print("\nCentral Bank News:")
                            for update in sentiment['central_bank_updates']:
                                print(f"- {update['title']} ({update['source']})")

                        self.open_position(analysis)
                    else:
                        print(f"Signal too weak ({analysis['strength']:.2f}), need at least {min_strength:.1f} with sentiment data")

        except Exception as e:
            print(f"Error managing trades: {str(e)}")

    def open_position(self, analysis):
        """Open a new position."""
        try:
            direction = analysis['direction']
            units = self._calculate_position_size(analysis['volatility'])

            if direction > 0:
                order = self.create_order(self._pair, units, suppress=True, ret=True)
                position_type = 'long'
            else:
                order = self.create_order(self._pair, -units, suppress=True, ret=True)
                position_type = 'short'

            if order:
                self._position = {
                    'type': position_type,
                    'units': units,
                    'entry_price': float(order['price']),
                    'time': order['time']
                }

                print(f"\n=== New Position Opened ===")
                print(f"Type: {position_type}")
                print(f"Units: {units}")
                print(f"Entry Price: ${float(order['price'])}")

        except Exception as e:
            print(f"Error opening position: {str(e)}")

    def close_position(self):
        """Close current position."""
        try:
            if self._position:
                units = self._position['units']

                if self._position['type'] == 'long':
                    order = self.create_order(self._pair, -units, suppress=True, ret=True)
                else:
                    order = self.create_order(self._pair, units, suppress=True, ret=True)

                if order:
                    profit = float(order['pl'])
                    print(f"\n=== Position Closed ===")
                    print(f"Profit/Loss: ${profit:.2f}")
                    self._position = None

        except Exception as e:
            print(f"Error closing position: {str(e)}")

    def run(self):
        """Main trading loop."""
        print("\nStarting Smart Auto Trader with RSS Analysis...")
        print("Press Ctrl+C to stop")

        while True:
            try:
                self.manage_trades()

                # Wait before next check
                import time
                time.sleep(60)  # Check every minute

            except KeyboardInterrupt:
                print("\nStopping Smart Auto Trader...")
                if self._position:
                    self.close_position()
                break
            except Exception as e:
                print(f"\nError in trading loop: {str(e)}")
                continue
