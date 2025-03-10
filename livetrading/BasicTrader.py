from tpqoa import tpqoa
import pandas as pd
from datetime import datetime

class BasicTrader(tpqoa):
    def __init__(
        self,
        cfg,
        risk_per_trade=0.05,  # 5% of available balance per trade
        stop_loss_pct=0.25,   # 0.25% stop loss
        take_profit_pct=0.5,  # 0.5% take profit
    ):
        """
        Basic trader focusing on EUR/USD with simple trend following.
        """
        super().__init__(cfg)
        
        self._position = None  # Current position
        self._risk_per_trade = risk_per_trade
        self._stop_loss_pct = stop_loss_pct
        self._take_profit_pct = take_profit_pct
        self._pair = 'EUR_USD'  # Focus on EUR/USD only
        
        # Get account info
        try:
            summary = self.get_account_summary()
            self._balance = float(summary.get('balance', 1000.0))
        except:
            self._balance = 1000.0  # Default balance for practice
            
        print(f"\nAccount Balance: ${self._balance:.2f}")
        print(f"\nTrading {self._pair} with:")
        print(f"- {risk_per_trade*100}% risk per trade")
        print(f"- {stop_loss_pct}% stop loss")
        print(f"- {take_profit_pct}% take profit")

    def _get_signal(self):
        """Simple trend following signal."""
        try:
            # Get last 5 prices
            df = self.get_history(
                instrument=self._pair,
                count=5,
                granularity="M1",
                price="M"
            )
            
            if df is None or len(df) < 5:
                return 0
                
            # Simple trend following
            prices = df.c.values
            trend = prices[-1] - prices[0]
            
            if trend > 0:
                return 1  # Buy signal
            elif trend < 0:
                return -1  # Sell signal
                
            return 0
            
        except:
            return 0

    def _calculate_position_size(self):
        """Calculate safe position size."""
        try:
            # Get current price
            price_info = self.get_current_price(self._pair)
            price = float(price_info['bid'])
            
            # Calculate risk amount in dollars
            risk_amount = self._balance * self._risk_per_trade
            
            # Calculate stop loss in pips
            stop_loss_pips = price * self._stop_loss_pct / 100
            
            # Calculate position size
            units = int(risk_amount / stop_loss_pips)
            
            # Ensure minimum units
            return max(100, min(units, 100000))  # Between 100 and 100k units
            
        except:
            return 100  # Default to minimum size

    def manage_trades(self):
        """Check current position and look for new opportunities."""
        try:
            if self._position:
                # Check existing position
                price_info = self.get_current_price(self._pair)
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
                    
                # Check if trend changed
                signal = self._get_signal()
                if signal != self._position['signal']:
                    print(f"\nClosing position - trend changed")
                    self.close_position()
                    return
                    
            else:
                # Look for new opportunity
                signal = self._get_signal()
                if signal != 0:
                    self.open_position(signal)
                    
        except Exception as e:
            print(f"Error managing trades: {str(e)}")

    def open_position(self, signal):
        """Open a new position."""
        try:
            units = self._calculate_position_size()
            
            if signal > 0:
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
                    'signal': signal,
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
        print("\nStarting Basic Trader...")
        print("Press Ctrl+C to stop")
        
        while True:
            try:
                self.manage_trades()
                
                # Wait before next check
                import time
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                print("\nStopping Basic Trader...")
                if self._position:
                    self.close_position()
                break
            except Exception as e:
                print(f"\nError in trading loop: {str(e)}")
                continue
