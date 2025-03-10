from tpqoa import tpqoa
import pandas as pd
import numpy as np
from datetime import datetime
from helpers.enhanced_market_analyzer import EnhancedMarketAnalyzer

class SmartAutoTrader(tpqoa):
    def __init__(
        self,
        cfg,
        risk_per_trade=0.05,  # 5% of available balance per trade
        stop_loss_pct=0.25,   # 0.25% stop loss
        take_profit_pct=0.5,  # 0.5% take profit
        max_positions=3       # Maximum number of simultaneous positions
    ):
        """
        Smart auto trader that analyzes all instruments and news.
        """
        super().__init__(cfg)
        
        self._market_analyzer = EnhancedMarketAnalyzer()
        self._positions = {}  # Current positions
        self._risk_per_trade = risk_per_trade
        self._stop_loss_pct = stop_loss_pct
        self._take_profit_pct = take_profit_pct
        self._max_positions = max_positions
        
        # Get account info
        try:
            summary = self.get_account_summary()
            self._balance = float(summary.get('balance', 1000.0))
        except Exception as e:
            print(f"Warning: Error getting account balance: {str(e)}")
            self._balance = 1000.0
            
        # Get all available instruments
        self._instruments = [inst[1] for inst in self.get_instruments()]
        
        print(f"\nAccount Balance: ${self._balance:.2f}")
        print(f"\nAnalyzing {len(self._instruments)} instruments")
        print("\nTrading Features:")
        print("- Real-time market analysis")
        print("- News-based trading decisions")
        print("- Multi-instrument analysis")
        print("- Dynamic position sizing")
        print("- Automatic risk management")
        print(f"- Maximum {max_positions} simultaneous positions")
        print(f"- {risk_per_trade*100}% risk per trade")
        print(f"- {stop_loss_pct}% stop loss")
        print(f"- {take_profit_pct}% take profit")

    def _analyze_instrument(self, instrument):
        """Analyze an instrument using price and news data."""
        try:
            # Get price data
            candles = self.get_history(
                instrument=instrument,
                count=15,
                granularity="M1",
                price="M"
            )
            
            if candles is None or len(candles) < 15:
                return None
                
            # Calculate technical indicators
            prices = candles.c.values
            sma5 = np.mean(prices[-5:])
            sma15 = np.mean(prices[-15:])
            momentum = prices[-1] - prices[-3]
            volatility = np.std(prices[-5:])
            
            # Get market sentiment
            sentiment = self._market_analyzer.get_market_sentiment(instrument)
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
                'instrument': instrument,
                'strength': abs(strength),
                'direction': 1 if strength > 0 else -1,
                'volatility': volatility,
                'sentiment': sentiment
            }
            
        except Exception as e:
            print(f"Error analyzing {instrument}: {str(e)}")
            return None

    def find_opportunities(self):
        """Find the best trading opportunities across all instruments."""
        opportunities = []
        
        for instrument in self._instruments:
            # Skip if we already have a position
            if instrument in self._positions:
                continue
                
            analysis = self._analyze_instrument(instrument)
            if analysis and analysis['strength'] > 0.5:  # Only strong signals
                opportunities.append(analysis)
                
        # Sort by strength
        opportunities.sort(key=lambda x: x['strength'], reverse=True)
        return opportunities

    def _calculate_position_size(self, instrument, volatility):
        """Calculate safe position size based on volatility."""
        try:
            # Get current price
            price_info = self.get_current_price(instrument)
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

    def manage_positions(self):
        """Manage existing positions and find new opportunities."""
        try:
            # Check existing positions
            for instrument, position in list(self._positions.items()):
                try:
                    # Get current price
                    price_info = self.get_current_price(instrument)
                    if not price_info or 'bid' not in price_info:
                        continue
                        
                    current_price = float(price_info['bid'])
                    entry_price = position['entry_price']
                    
                    # Calculate profit/loss
                    if position['type'] == 'long':
                        profit_pct = (current_price - entry_price) / entry_price * 100
                    else:
                        profit_pct = (entry_price - current_price) / entry_price * 100
                        
                    # Check stop loss
                    if profit_pct <= -self._stop_loss_pct:
                        print(f"\nClosing {instrument} position at stop loss")
                        self.close_position(instrument)
                        continue
                        
                    # Check take profit
                    if profit_pct >= self._take_profit_pct:
                        print(f"\nClosing {instrument} position at take profit")
                        self.close_position(instrument)
                        continue
                        
                    # Check if conditions changed
                    analysis = self._analyze_instrument(instrument)
                    if analysis:
                        if (position['type'] == 'long' and analysis['direction'] < 0) or \
                           (position['type'] == 'short' and analysis['direction'] > 0):
                            print(f"\nClosing {instrument} position - conditions changed")
                            self.close_position(instrument)
                            
                except Exception as e:
                    print(f"Error managing {instrument} position: {str(e)}")
                    
            # Look for new opportunities
            if len(self._positions) < self._max_positions:
                opportunities = self.find_opportunities()
                
                for opp in opportunities[:self._max_positions - len(self._positions)]:
                    print(f"\nFound opportunity in {opp['instrument']}")
                    print(f"Strength: {opp['strength']:.2f}")
                    print(f"Direction: {'Long' if opp['direction'] > 0 else 'Short'}")
                    
                    sentiment = opp['sentiment']
                    print("\nMarket Analysis:")
                    print(f"Sentiment Score: {sentiment['sentiment_score']:.2f}")
                    print(f"Recent News ({sentiment['news_count']} articles):")
                    for item in sentiment['news_items'][:3]:
                        print(f"- {item['title']} ({item['source']})")
                        
                    self.open_position(opp)
                    
        except Exception as e:
            print(f"Error managing trades: {str(e)}")

    def open_position(self, opportunity):
        """Open a new position."""
        try:
            instrument = opportunity['instrument']
            direction = opportunity['direction']
            units = self._calculate_position_size(instrument, opportunity['volatility'])
            
            if direction > 0:
                order = self.create_order(instrument, units, suppress=True, ret=True)
                position_type = 'long'
            else:
                order = self.create_order(instrument, -units, suppress=True, ret=True)
                position_type = 'short'
                
            if order:
                self._positions[instrument] = {
                    'type': position_type,
                    'units': units,
                    'entry_price': float(order['price']),
                    'time': order['time']
                }
                
                print(f"\n=== New Position Opened ===")
                print(f"Instrument: {instrument}")
                print(f"Type: {position_type}")
                print(f"Units: {units}")
                print(f"Entry Price: ${float(order['price'])}")
                
        except Exception as e:
            print(f"Error opening position: {str(e)}")

    def close_position(self, instrument):
        """Close a position."""
        try:
            if instrument in self._positions:
                position = self._positions[instrument]
                units = position['units']
                
                if position['type'] == 'long':
                    order = self.create_order(instrument, -units, suppress=True, ret=True)
                else:
                    order = self.create_order(instrument, units, suppress=True, ret=True)
                    
                if order:
                    profit = float(order['pl'])
                    print(f"\n=== Position Closed ===")
                    print(f"Instrument: {instrument}")
                    print(f"Profit/Loss: ${profit:.2f}")
                    del self._positions[instrument]
                    
        except Exception as e:
            print(f"Error closing position: {str(e)}")

    def run(self):
        """Main trading loop."""
        print("\nStarting Smart Auto Trader...")
        print("Press Ctrl+C to stop")
        
        while True:
            try:
                self.manage_positions()
                
                # Wait before next check
                import time
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                print("\nStopping Smart Auto Trader...")
                # Close all positions
                for instrument in list(self._positions.keys()):
                    self.close_position(instrument)
                break
            except Exception as e:
                print(f"\nError in trading loop: {str(e)}")
                continue
