from tpqoa.tpqoa import tpqoa
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from helpers.super_market_analyzer import SuperMarketAnalyzer

class FemtoTrader(tpqoa):
    def __init__(
        self,
        cfg,
        risk_per_trade=0.05,  # 5% of available balance per trade
        stop_loss_pct=0.25,   # 0.25% stop loss
        take_profit_pct=0.5,  # 0.5% take profit
        gui_callback=None,    # Callback for GUI updates
        auto_select=True,     # Auto-select best pair or use manual
        manual_pair=None,     # Manual pair if auto_select=False
    ):
        """
        Smart auto trader with enhanced market analysis.
        """
        super().__init__(cfg)

        self._market_analyzer = SuperMarketAnalyzer()
        self._position = None  # Current position
        self._risk_per_trade = risk_per_trade
        self._stop_loss_pct = stop_loss_pct
        self._take_profit_pct = take_profit_pct
        self._pair = manual_pair if not auto_select and manual_pair else None  # Set manual pair if specified
        self._instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD', 'USD_CHF']  # Major pairs to analyze
        self._gui_callback = gui_callback  # GUI callback function
        self._auto_select = auto_select

        # Get account info
        try:
            summary = self.get_account_summary()
            self._balance = float(summary.get('balance', 0.0))
            if self._balance == 0.0:
                raise ValueError("Could not retrieve account balance")
        except Exception as e:
            print(f"Error: Could not get account balance: {str(e)}")
            print("Please check your Oanda API credentials and connection")
            raise

        if self._gui_callback:
            self._gui_callback('log', f"Account Balance: ${self._balance:.2f}")
            self._gui_callback('log', f"Scanning {len(self._instruments)} instruments for best trading opportunities")
            self._gui_callback('balance', self._balance)
        else:
            print(f"\nAccount Balance: ${self._balance:.2f}")
            print(f"\nScanning {len(self._instruments)} instruments with:")
            print("\nEnhanced Analysis Sources:")
            print("- Financial News (Reuters, Bloomberg, etc.)")
            print("- Technical Analysis (TradingView, etc.)")
            print("- Economic Data (Forex Factory, etc.)")
            print("- Central Bank News (Fed, ECB, etc.)")
            print("\nTrading Features:")
            print("- Real-time market analysis")
            print("- Multi-source sentiment analysis")
            print("- Economic calendar monitoring")
            print("- Central bank policy tracking")
            print("- Dynamic position sizing")
            print("- Automatic risk management")
            print(f"- {risk_per_trade*100}% risk per trade")
            print(f"- {stop_loss_pct}% stop loss")
            print(f"- {take_profit_pct}% take profit")

    def _get_history_df(self, pair):
        """Get historical data for analysis."""
        try:
            # Get candles from API
            response = self.ctx.instrument.candles(
                pair,
                granularity="M1",
                count=15,
                price="M"
            )

            if response.status != 200:
                print(f"Error getting candles: {response.body}")
                return None

            # Extract candle data
            data = []
            for candle in response.body.get('candles', []):
                if candle.complete:
                    data.append({
                        'time': pd.to_datetime(candle.time),
                        'open': float(candle.mid.o),
                        'high': float(candle.mid.h),
                        'low': float(candle.mid.l),
                        'close': float(candle.mid.c),
                        'volume': int(candle.volume)
                    })

            if not data:
                return None

            df = pd.DataFrame(data)
            df.set_index('time', inplace=True)
            return df

        except Exception as e:
            print(f"Error getting history: {str(e)}")
            return None

    def _analyze_market(self, pair):
        """Analyze market using enhanced data sources."""
        try:
            # Get price data
            df = self._get_history_df(pair)
            if df is None or len(df) < 15:
                return None

            # Calculate technical indicators
            prices = df.close.values
            sma5 = np.mean(prices[-5:])
            sma15 = np.mean(prices[-15:])
            momentum = prices[-1] - prices[-3]
            volatility = np.std(prices[-5:])

            # Get comprehensive market sentiment
            sentiment = self._market_analyzer.get_market_sentiment(pair)
            if not sentiment:
                return None

            sentiment_score = sentiment['sentiment_score']

            # Calculate strength score
            technical_score = 0
            if sma5 > sma15 and momentum > 0:
                technical_score = 1
            elif sma5 < sma15 and momentum < 0:
                technical_score = -1

            # Combine technical and sentiment scores
            strength = (technical_score + sentiment_score) / 2

            return {
                'strength': abs(strength),
                'direction': 1 if strength > 0 else -1,
                'volatility': volatility,
                'sentiment': sentiment,
                'current_price': prices[-1]
            }

        except Exception as e:
            print(f"Error analyzing market: {str(e)}")
            return None

    def _calculate_position_size(self, volatility):
        """Calculate safe position size based on volatility."""
        try:
            # Get current price
            price_info = self.get_current_price(self._pair)
            if not price_info or 'bid' not in price_info:
                return 100

            price = float(price_info['bid'])

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
                price_info = self.get_current_price(self._pair)
                if not price_info or 'bid' not in price_info:
                    return

                current_price = float(price_info['bid'])
                entry_price = self._position['entry_price']

                # Calculate profit/loss
                if self._position['type'] == 'long':
                    profit_pct = (current_price - entry_price) / entry_price * 100
                else:
                    profit_pct = (entry_price - current_price) / entry_price * 100

                # Check stop loss
                if profit_pct <= -self._stop_loss_pct:
                    if self._gui_callback:
                        self._gui_callback('log', "Closing position at stop loss")
                    else:
                        print(f"\nClosing position at stop loss")
                    self.close_position()
                    return

                # Check take profit
                if profit_pct >= self._take_profit_pct:
                    if self._gui_callback:
                        self._gui_callback('log', "Closing position at take profit")
                    else:
                        print(f"\nClosing position at take profit")
                    self.close_position()
                    return

                # Check if conditions changed
                analysis = self._analyze_market(self._pair)
                if analysis:
                    if (self._position['type'] == 'long' and analysis['direction'] < 0) or \
                       (self._position['type'] == 'short' and analysis['direction'] > 0):
                        if self._gui_callback:
                            self._gui_callback('log', "Closing position - conditions changed")
                        else:
                            print(f"\nClosing position - conditions changed")
                        self.close_position()
                        return

            else:
                if not self._auto_select and self._pair:
                    # Manual pair selection
                    analysis = self._analyze_market(self._pair)
                    if analysis and analysis['strength'] > 0.3:  # Lower threshold for manual
                        if self._gui_callback:
                            self._gui_callback('log', f"Manual pair {self._pair} selected (strength: {analysis['strength']:.2f})")
                        else:
                            print(f"\nManual pair {self._pair} selected (strength: {analysis['strength']:.2f})")
                        best_analysis = analysis
                        best_pair = self._pair
                    else:
                        if self._gui_callback:
                            self._gui_callback('log', f"Manual pair {self._pair} not suitable for trading")
                        return
                else:
                    # Auto selection
                    best_pair = None
                    best_strength = 0
                    best_analysis = None

                    for pair in self._instruments:
                        analysis = self._analyze_market(pair)
                        if analysis and analysis['strength'] > best_strength:
                            best_strength = analysis['strength']
                            best_pair = pair
                            best_analysis = analysis

                    if not (best_pair and best_strength > 0.5):  # Only strong signals
                        return

                    self._pair = best_pair
                    if self._gui_callback:
                        self._gui_callback('log', f"Selected {best_pair} for trading (strength: {best_strength:.2f})")
                    else:
                        print(f"\nSelected {best_pair} for trading (strength: {best_strength:.2f})")

                # Send analysis data to GUI
                if self._gui_callback and best_analysis:
                    sentiment = best_analysis['sentiment']
                    self._gui_callback('price', {'pair': best_pair, 'bid': best_analysis['current_price']})
                    self._gui_callback('signal', {'strength': best_analysis['strength'], 'direction': best_analysis['direction']})
                    if sentiment['news_items']:
                        self._gui_callback('news', sentiment['news_items'][:5])
                    if sentiment['technical_analysis']:
                        self._gui_callback('technical', sentiment['technical_analysis'][:3])

                print(f"\nFound trading opportunity")
                print(f"Strength: {best_analysis['strength']:.2f}")
                print(f"Direction: {'Long' if best_analysis['direction'] > 0 else 'Short'}")
                print(f"Current Price: ${best_analysis['current_price']:.5f}")

                sentiment = best_analysis['sentiment']
                print("\nMarket Analysis:")
                print(f"Sentiment Score: {sentiment['sentiment_score']:.2f}")

                if sentiment['news_items']:
                    print(f"\nLatest News ({sentiment['news_count']} articles):")
                    for item in sentiment['news_items'][:3]:
                        print(f"- {item['title']} ({item['source']})")

                if sentiment['technical_analysis']:
                    print("\nTechnical Signals:")
                    for signal in sentiment['technical_analysis']:
                        print(f"- {signal['indicator']}: {signal['signal']} ({signal['strength']})")

                if sentiment['economic_calendar']:
                    print("\nEconomic Events:")
                    for event in sentiment['economic_calendar']:
                        print(f"- {event['event']} (Impact: {event['impact']})")

                if sentiment['central_bank_updates']:
                    print("\nCentral Bank News:")
                    for update in sentiment['central_bank_updates']:
                        print(f"- {update['title']} ({update['source']})")

                self.open_position(best_analysis)

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
                    'time': order['time'],
                    'pair': self._pair
                }
                if self._gui_callback:
                    self._gui_callback('log', f"=== New Position Opened ===")
                    self._gui_callback('log', f"Type: {position_type}")
                    self._gui_callback('log', f"Units: {units}")
                    self._gui_callback('log', f"Entry Price: ${float(order['price'])}")
                    self._gui_callback('position', self._position)
                else:
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
                    self._balance += profit  # Update balance
                    if self._gui_callback:
                        self._gui_callback('log', "=== Position Closed ===")
                        self._gui_callback('log', f"Profit/Loss: ${profit:.2f}")
                        self._gui_callback('balance', self._balance)
                        self._gui_callback('position', None)
                        self._gui_callback('history', {
                            'pair': self._position['pair'],
                            'type': self._position['type'],
                            'entry_price': self._position['entry_price'],
                            'exit_price': float(order['price']),
                            'profit': profit,
                            'time': datetime.now().isoformat()
                        })
                    else:
                        print(f"\n=== Position Closed ===")
                        print(f"Profit/Loss: ${profit:.2f}")
                    self._position = None

        except Exception as e:
            if self._gui_callback:
                self._gui_callback('log', f"Error closing position: {str(e)}")
            else:
                print(f"Error closing position: {str(e)}")

    def run(self):
        """Main trading loop."""
        print("\nStarting Smart Auto Trader...")
        print("Press Ctrl+C to stop")

        while True:
            try:
                # Check if stop datetime has been reached
                if hasattr(self, '_stop_datetime') and self._stop_datetime:
                    if datetime.now() >= self._stop_datetime:
                        print(f"\nStop datetime reached: {self._stop_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                        if self._position:
                            self.close_position()
                        break

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
