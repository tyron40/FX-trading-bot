from tpqoa import tpqoa
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from helpers.enhanced_market_analyzer import EnhancedMarketAnalyzer

class AutoTrader(tpqoa):
    def __init__(
        self,
        cfg,
        bar_length="1m",
        risk_per_trade=0.05,  # 5% of available balance per trade
        stop_loss_pct=0.25,   # 0.25% stop loss
        take_profit_pct=0.5,  # 0.5% take profit
        max_positions=3       # Maximum number of simultaneous positions
    ):
        """
        Fully automated trader that manages multiple instruments.
        """
        super().__init__(cfg)
        
        self._market_analyzer = EnhancedMarketAnalyzer()
        self._positions = {}  # Track open positions
        self._analyzed_pairs = {}  # Track analyzed pairs
        self._max_positions = max_positions
        self._risk_per_trade = risk_per_trade
        self._stop_loss_pct = stop_loss_pct
        self._take_profit_pct = take_profit_pct
        self._bar_length = pd.to_timedelta(bar_length)
        
        # Get account info
        try:
            response = self.ctx.account.summary(self.account_id)
            self._balance = float(response.account.balance)
        except Exception as e:
            print(f"Warning: Error getting account balance: {str(e)}")
            self._balance = 1000.0  # Default balance for practice
            
        print(f"\nAccount Balance: ${self._balance:.2f}")
        
        # Get all available instruments
        self._instruments = self.get_instruments()
        print(f"Available Instruments: {len(self._instruments)}")
        
        print("\nAuto Trading Features Enabled:")
        print("- Multi-instrument analysis")
        print("- Automatic position sizing")
        print("- Dynamic risk management")
        print("- Real-time market analysis")
        print(f"- Maximum {max_positions} simultaneous positions")
        print(f"- {risk_per_trade*100}% risk per trade")
        print(f"- {stop_loss_pct}% stop loss")
        print(f"- {take_profit_pct}% take profit")

    def _calculate_position_size(self, instrument):
        """Calculate safe position size based on account balance and risk."""
        try:
            # Get current price
            price = float(self.get_current_price(instrument)['bid'])
            
            # Calculate risk amount in dollars
            risk_amount = self._balance * self._risk_per_trade
            
            # Calculate stop loss in pips
            stop_loss_pips = price * self._stop_loss_pct / 100
            
            # Calculate position size
            units = int(risk_amount / stop_loss_pips)
            
            # Ensure minimum units
            return max(100, min(units, 100000))  # Between 100 and 100k units
            
        except Exception as e:
            print(f"Error calculating position size: {str(e)}")
            return 100  # Default to minimum size

    def analyze_instruments(self):
        """Analyze all available instruments for trading opportunities."""
        opportunities = []
        
        for instrument in self._instruments:
            pair = instrument[1]
            try:
                # Get technical analysis
                data = self._get_instrument_data(pair)
                signal = self._analyze_instrument(data)
                
                # Get market sentiment
                sentiment = self._market_analyzer.get_market_sentiment(pair)
                
                if signal != 0 and sentiment:  # If we have a signal and sentiment
                    strength = abs(sentiment['sentiment_score'])
                    if strength > 0.5:  # Strong sentiment
                        opportunities.append({
                            'pair': pair,
                            'signal': signal,
                            'strength': strength,
                            'sentiment': sentiment
                        })
                        
            except Exception as e:
                print(f"Error analyzing {pair}: {str(e)}")
                continue
                
        # Sort by strength
        opportunities.sort(key=lambda x: x['strength'], reverse=True)
        return opportunities

    def _get_instrument_data(self, instrument):
        """Get historical data for analysis."""
        now = datetime.utcnow()
        past = now - timedelta(days=1)
        
        df = self.get_history(
            instrument=instrument,
            start=past,
            end=now,
            granularity="M1",
            price="M"
        ).c.dropna().to_frame()
        
        df.rename(columns={"c": "mid_price"}, inplace=True)
        return df

    def _analyze_instrument(self, data):
        """Analyze instrument for trading signals."""
        # Calculate indicators
        data["sma5"] = data["mid_price"].rolling(5).mean()
        data["sma15"] = data["mid_price"].rolling(15).mean()
        data["momentum"] = data["mid_price"].diff(3).fillna(0)
        data["volatility"] = data["mid_price"].rolling(5).std()
        data["trend_strength"] = abs(data["sma5"] - data["sma15"]) / data["volatility"]
        
        # Generate signals
        if len(data) < 15:  # Need enough data
            return 0
            
        latest = data.iloc[-1]
        
        # Long signal
        if (latest["sma5"] > latest["sma15"] and  # Uptrend
            latest["momentum"] > 0 and            # Positive momentum
            latest["trend_strength"] > 1.0):      # Strong trend
            return 1
            
        # Short signal
        elif (latest["sma5"] < latest["sma15"] and  # Downtrend
              latest["momentum"] < 0 and            # Negative momentum
              latest["trend_strength"] > 1.0):      # Strong trend
            return -1
            
        return 0

    def manage_positions(self):
        """Manage open positions and look for new opportunities."""
        # First check existing positions
        for pair, position in list(self._positions.items()):
            current_price = float(self.get_current_price(pair)['bid'])
            entry_price = position['entry_price']
            
            # Calculate profit/loss
            if position['type'] == 'long':
                profit_pct = (current_price - entry_price) / entry_price * 100
            else:
                profit_pct = (entry_price - current_price) / entry_price * 100
                
            # Check stop loss
            if profit_pct <= -self._stop_loss_pct:
                print(f"\nClosing {pair} position at stop loss")
                self.close_position_for_pair(pair)
                continue
                
            # Check take profit
            if profit_pct >= self._take_profit_pct:
                print(f"\nClosing {pair} position at take profit")
                self.close_position_for_pair(pair)
                continue
                
            # Check if trend is still valid
            data = self._get_instrument_data(pair)
            signal = self._analyze_instrument(data)
            if signal != position['signal']:
                print(f"\nClosing {pair} position - trend changed")
                self.close_position_for_pair(pair)
                
        # Look for new opportunities if we have room
        if len(self._positions) < self._max_positions:
            opportunities = self.analyze_instruments()
            
            for opp in opportunities:
                if len(self._positions) >= self._max_positions:
                    break
                    
                if opp['pair'] not in self._positions:
                    print(f"\nOpening new position in {opp['pair']}")
                    self.open_position(opp)

    def open_position(self, opportunity):
        """Open a new position."""
        pair = opportunity['pair']
        signal = opportunity['signal']
        units = self._calculate_position_size(pair)
        
        if signal > 0:
            order = self.create_order(pair, units, suppress=True, ret=True)
            position_type = 'long'
        else:
            order = self.create_order(pair, -units, suppress=True, ret=True)
            position_type = 'short'
            
        if order:
            self._positions[pair] = {
                'type': position_type,
                'units': units,
                'entry_price': float(order['price']),
                'signal': signal,
                'time': order['time']
            }
            
            print(f"\n=== New Position Opened ===")
            print(f"Pair: {pair}")
            print(f"Type: {position_type}")
            print(f"Units: {units}")
            print(f"Entry Price: ${float(order['price'])}")
            
            sentiment = opportunity['sentiment']
            print(f"\nMarket Analysis:")
            print(f"Sentiment Score: {sentiment['sentiment_score']:.2f}")
            print(f"Recent News ({sentiment['news_count']} articles):")
            for item in sentiment['news_items'][:3]:
                print(f"- {item['title']} ({item['source']})")

    def close_position_for_pair(self, pair):
        """Close position for a specific pair."""
        if pair in self._positions:
            position = self._positions[pair]
            units = position['units']
            
            if position['type'] == 'long':
                order = self.create_order(pair, -units, suppress=True, ret=True)
            else:
                order = self.create_order(pair, units, suppress=True, ret=True)
                
            if order:
                profit = float(order['pl'])
                print(f"\n=== Position Closed ===")
                print(f"Pair: {pair}")
                print(f"Profit/Loss: ${profit:.2f}")
                del self._positions[pair]

    def run(self):
        """Main trading loop."""
        print("\nStarting Auto Trader...")
        print("Press Ctrl+C to stop")
        
        while True:
            try:
                self.manage_positions()
                
                # Wait before next check
                import time
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                print("\nStopping Auto Trader...")
                # Close all positions
                for pair in list(self._positions.keys()):
                    self.close_position_for_pair(pair)
                break
            except Exception as e:
                print(f"\nError in trading loop: {str(e)}")
                continue
