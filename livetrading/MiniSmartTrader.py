from tpqoa import tpqoa
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from helpers.enhanced_market_analyzer import EnhancedMarketAnalyzer

class MiniSmartTrader(tpqoa):
    def __init__(
        self,
        cfg,
        risk_per_trade=0.05,  # 5% of available balance per trade
        stop_loss_pct=0.25,   # 0.25% stop loss
        take_profit_pct=0.5,  # 0.5% take profit
    ):
        """
        Smart auto trader focusing on EUR/USD.
        """
        super().__init__(cfg)
        
        self._market_analyzer = EnhancedMarketAnalyzer()
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
        print("- Real-time market analysis")
        print("- News-based trading decisions")
        print("- Dynamic position sizing")
        print("- Automatic risk management")
        print(f"- {risk_per_trade*100}% risk per trade")
        print(f"- {stop_loss_pct}% stop loss")
        print(f"- {take_profit_pct}% take profit")

    def _get_history_df(self):
        """Get historical data for analysis."""
        try:
            # Get last 15 minutes of data
            now = datetime.utcnow()
            past = now - timedelta(minutes=15)
            
            df = self.get_history(
                instrument=self._pair,
                start=past,
                end=now,
                granularity="M1",
                price="M"
            )
            
            return df
            
        except Exception as e:
            print(f"Error getting history: {str(e)}")
            return None

    def _analyze_market(self):
        """Analyze market using price and news data."""
        try:
            # Get price data
            df = self._get_history_df()
            if df is None or len(df) < 15:
                return None
                
            # Calculate technical indicators
            prices = df.c.values
            sma5 = np.mean(prices[-5:])
            sma15 = np.mean(prices[-15:])
            momentum = prices[-1] - prices[-3]
            volatility = np.std(prices[-5:])
            
            # Get market sentiment
            sentiment = self._market_analyzer.get_market_sentiment(self._pair)
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
                'sentiment': sentiment
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
                    print(f"\nClosing position at stop loss")
                    self.close_position()
                    return
                    
                # Check take profit
                if profit_pct >= self._take_profit_pct:
                    print(f"\nClosing position at take profit")
                    self.close_position()
                    return
                    
                # Check if conditions changed
                analysis = self._analyze_market()
                if analysis:
                    if (self._position['type'] == 'long' and analysis['direction'] < 0) or \
                       (self._position['type'] == 'short' and analysis['direction'] > 0):
                        print(f"\nClosing position - conditions changed")
                        self.close_position()
                        return
                        
            else:
                # Look for new opportunity
                analysis = self._analyze_market()
                if analysis and analysis['strength'] > 0.5:  # Only strong signals
                    print(f"\nFound trading opportunity")
                    print(f"Strength: {analysis['strength']:.2f}")
                    print(f"Direction: {'Long' if analysis['direction'] > 0 else 'Short'}")
                    
                    sentiment = analysis['sentiment']
                    print("\nMarket Analysis:")
                    print(f"Sentiment Score: {sentiment['sentiment_score']:.2f}")
                    print(f"Recent News ({sentiment['news_count']} articles):")
                    for item in sentiment['news_items'][:3]:
                        print(f"- {item['title']} ({item['source']})")
                        
                    self.open_position(analysis)
                    
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
        print("\nStarting Smart Auto Trader...")
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
