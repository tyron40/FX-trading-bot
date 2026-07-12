from tpqoa.tpqoa import tpqoa
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from helpers.rss_market_analyzer import RSSMarketAnalyzer
from helpers.technical_analysis import TechnicalAnalysis

class FemtoTrader(tpqoa):
    def __init__(
        self,
        cfg,
        risk_per_trade=0.05,  # 5% of available balance per trade
        stop_loss_pct=0.25,   # 0.25% stop loss
        take_profit_pct=0.5,  # 0.5% take profit
    ):
        """
        Advanced auto trader with trendlines, candle patterns, and RSS analysis.
        """
        super().__init__(cfg)

        self._market_analyzer = RSSMarketAnalyzer()
        self._technical_analyzer = TechnicalAnalysis()
        self._position = None  # Current position
        self._risk_per_trade = risk_per_trade
        self._stop_loss_pct = stop_loss_pct
        self._take_profit_pct = take_profit_pct
        self._pair = 'EUR_USD'  # Focus on EUR/USD

        # Chart analysis data
        self._chart_data = []
        self._max_chart_points = 100  # Keep last 100 candles for analysis

        # Get account info
        try:
            summary = self.get_account_summary()
            self._balance = float(summary.get('balance', 1000.0))
        except Exception as e:
            print(f"Warning: Error getting account balance: {str(e)}")
            self._balance = 1000.0

        print(f"\nAccount Balance: ${self._balance:.2f}")
        print(f"\nTrading {self._pair} with Advanced Analysis:")
        print("\nTechnical Analysis Features:")
        print("- Dynamic Trendline Detection (swing points)")
        print("- Candle Pattern Recognition (engulfing, pin bars, stars, etc.)")
        print("- Breakout & Retest Confirmation")
        print("- Multi-timeframe Analysis")
        print("\nSentiment Analysis:")
        print("- RSS feeds from Central Banks (ECB, Fed, BoE)")
        print("- Financial News (CNBC, FT, Reuters)")
        print("- Global Institutions (IMF, World Bank, OECD)")
        print("\nTrading Features:")
        print("- Chart-based decision making")
        print("- Pattern confirmation trading")
        print("- Risk-aware position sizing")
        print("- Automatic trendline breakouts")
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
            'history': None,
            'chart': None  # New callback for chart overlays
        }

    def set_gui_callbacks(self, price_callback=None, signal_callback=None, news_callback=None,
                         technical_callback=None, position_callback=None, history_callback=None,
                         chart_callback=None):
        """Set GUI callback functions for thread-safe updates"""
        self._gui_callbacks['price'] = price_callback
        self._gui_callbacks['signal'] = signal_callback
        self._gui_callbacks['news'] = news_callback
        self._gui_callbacks['technical'] = technical_callback
        self._gui_callbacks['position'] = position_callback
        self._gui_callbacks['history'] = history_callback
        self._gui_callbacks['chart'] = chart_callback

    def _get_history_df(self):
        """Get historical data for analysis."""
        try:
            # Get more candles for better trendline analysis
            response = self.ctx.instrument.candles(
                self._pair,
                granularity="M1",
                count=50,  # More candles for trend analysis
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

            # Need at least 20 complete candles for analysis
            if len(data) < 20:
                print(f"Only {len(data)} complete candles available, need at least 20")
                return None

            df = pd.DataFrame(data[-30:])  # Use the last 30 complete candles
            df.set_index('time', inplace=True)

            # Store for chart analysis
            self._chart_data = df.copy()

            return df

        except Exception as e:
            print(f"Error getting history: {str(e)}")
            return None

    def _analyze_market(self):
        """Advanced market analysis combining technical, pattern, and sentiment analysis."""
        try:
            # Get price data
            df = self._get_history_df()
            if df is None or len(df) < 20:
                print("Insufficient price data for advanced analysis")
                return None

            # Perform complete chart analysis
            chart_analysis = self._technical_analyzer.analyze_chart(df)

            # Get trading signal from technical analysis
            technical_signal = self._technical_analyzer.get_trading_signal(chart_analysis)

            # Get market sentiment from RSS feeds
            sentiment = self._market_analyzer.get_market_sentiment(self._pair)
            sentiment_score = 0

            if sentiment and 'sentiment_score' in sentiment:
                sentiment_score = sentiment['sentiment_score']
                print(f"RSS sentiment: {sentiment_score:.2f} (from {sentiment.get('news_count', 0)} news + {sentiment.get('central_bank_news', 0)} CB items)")
            else:
                print("Using technical analysis only (RSS data unavailable)")

            # Combine signals
            final_signal = self._combine_signals(technical_signal, sentiment_score, chart_analysis)

            analysis_result = {
                'technical_signal': technical_signal,
                'sentiment_score': sentiment_score,
                'chart_analysis': chart_analysis,
                'final_signal': final_signal,
                'current_price': df['close'].iloc[-1]
            }

            # Print analysis summary
            if final_signal:
                print(f"Advanced Analysis: Strength={final_signal['strength']:.2f}, Direction={'Long' if final_signal['direction'] > 0 else 'Short'}")
                print(f"Reasons: {', '.join(final_signal['reasons'])}")
            else:
                print("No strong trading signal found")

            return analysis_result

        except Exception as e:
            print(f"Error in advanced market analysis: {str(e)}")
            return None

    def _combine_signals(self, technical_signal, sentiment_score, chart_analysis):
        """Combine technical and sentiment signals intelligently."""
        if not technical_signal:
            return None

        # Base signal from technical analysis
        direction = technical_signal['direction']
        strength = technical_signal['strength']
        reasons = technical_signal['reasons'].copy()

        # Sentiment confirmation boost
        sentiment_boost = 0
        if abs(sentiment_score) > 0.5:  # Strong sentiment
            if (sentiment_score > 0 and direction > 0) or (sentiment_score < 0 and direction < 0):
                sentiment_boost = 0.2  # 20% boost for confirmation
                reasons.append("Sentiment confirmation")
            elif (sentiment_score > 0 and direction < 0) or (sentiment_score < 0 and direction > 0):
                sentiment_boost = -0.3  # 30% reduction for conflict
                reasons.append("Sentiment conflict")

        # Pattern strength bonus
        pattern_bonus = 0
        strong_patterns = [p for p in chart_analysis['patterns'] if p['strength'] == 'Strong']
        if len(strong_patterns) > 0:
            pattern_bonus = 0.1 * len(strong_patterns)
            reasons.append(f"{len(strong_patterns)} strong pattern(s)")

        # Breakout bonus
        breakout_bonus = 0
        if chart_analysis['breakouts']:
            breakout_bonus = 0.15 * len(chart_analysis['breakouts'])
            reasons.append(f"{len(chart_analysis['breakouts'])} breakout(s)")

        # Calculate final strength
        final_strength = strength + sentiment_boost + pattern_bonus + breakout_bonus

        # Minimum threshold for trading
        if final_strength >= 0.6:  # Lower threshold due to advanced analysis
            return {
                'direction': direction,
                'strength': min(final_strength, 1.0),  # Cap at 1.0
                'reasons': reasons,
                'analysis': {
                    'technical': technical_signal,
                    'sentiment': sentiment_score,
                    'patterns': len(chart_analysis['patterns']),
                    'breakouts': len(chart_analysis['breakouts']),
                    'retests': len(chart_analysis['retests'])
                }
            }

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

                # Check if trendlines are broken against position
                if self._chart_data is not None and len(self._chart_data) > 0:
                    chart_analysis = self._technical_analyzer.analyze_chart(self._chart_data)

                    # Check for breakouts against position
                    breakouts = chart_analysis['breakouts']
                    for breakout in breakouts:
                        if ((self._position['type'] == 'long' and breakout['direction'] < 0) or
                            (self._position['type'] == 'short' and breakout['direction'] > 0)):
                            if breakout['strength'] >= 3:  # Strong trendline
                                print(f"\nClosing position - strong trendline breakout against position")
                                self.close_position()
                                return

            else:
                # Look for new opportunity
                analysis = self._analyze_market()
                if analysis and analysis['final_signal']:
                    signal = analysis['final_signal']

                    # Additional confirmation: require minimum strength
                    if signal['strength'] >= 0.7:  # Higher threshold for advanced analysis
                        print(f"\nFound advanced trading opportunity")
                        print(f"Strength: {signal['strength']:.2f}")
                        print(f"Direction: {'Long' if signal['direction'] > 0 else 'Short'}")
                        print(f"Current Price: ${analysis['current_price']:.5f}")

                        print("\nSignal Components:")
                        for reason in signal['reasons']:
                            print(f"- {reason}")

                        # Show chart analysis details
                        chart = analysis['chart_analysis']
                        if chart['patterns']:
                            print(f"\nCandle Patterns: {len(chart['patterns'])} detected")
                        if chart['breakouts']:
                            print(f"Trendline Breakouts: {len(chart['breakouts'])} detected")
                        if chart['retests']:
                            print(f"Trendline Retests: {len(chart['retests'])} detected")

                        self.open_position(analysis)
                    else:
                        print(f"Signal too weak ({signal['strength']:.2f}), need at least 0.7 with advanced analysis")

        except Exception as e:
            print(f"Error managing trades: {str(e)}")

    def open_position(self, analysis):
        """Open a new position based on advanced analysis."""
        try:
            direction = analysis['final_signal']['direction']
            units = self._calculate_position_size(0.001)  # Default volatility

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
                    'time': order['time'],
                    'signal': analysis['final_signal']
                }

                print(f"\n=== New Position Opened (Advanced Analysis) ===")
                print(f"Type: {position_type}")
                print(f"Units: {units}")
                print(f"Entry Price: ${float(order['price'])}")
                print(f"Signal Strength: {analysis['final_signal']['strength']:.2f}")

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
                    print(f"Entry Signal: {self._position.get('signal', {}).get('strength', 'N/A')}")
                    self._position = None

        except Exception as e:
            print(f"Error closing position: {str(e)}")

    def run(self):
        """Main trading loop with advanced analysis."""
        print("\nStarting Advanced Auto Trader with Trendlines & Patterns...")
        print("Press Ctrl+C to stop")

        while True:
            try:
                self.manage_trades()

                # Wait before next check
                import time
                time.sleep(60)  # Check every minute

            except KeyboardInterrupt:
                print("\nStopping Advanced Auto Trader...")
                if self._position:
                    self.close_position()
                break
            except Exception as e:
                print(f"\nError in trading loop: {str(e)}")
                continue
