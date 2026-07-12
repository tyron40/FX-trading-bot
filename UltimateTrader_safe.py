"""
Ultimate Trading Bot - SAFE VERSION with Conservative Parameters

This version uses practice account and conservative parameters for safer trading.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.gridspec as gridspec
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from tpqoa.tpqoa import tpqoa
from helpers.technical_analysis import TechnicalAnalysis
from helpers.market_analyzer import MarketAnalyzer
from helpers.enhanced_market_analyzer import EnhancedMarketAnalyzer
import requests
import feedparser

class UltimateTraderSafe(tpqoa):
    """
    Safe version of the Ultimate Trading Bot with conservative parameters
    """

    def __init__(self, cfg_path="config/oanda_practice.cfg"):
        """
        Initialize the Safe Ultimate Trading Bot
        """
        super().__init__(cfg_path)

        # SAFE configuration - conservative parameters for profitability
        self._instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD']
        self._risk_per_trade = 0.005  # Very conservative 0.5% per trade
        self._max_positions = 1  # Only 1 position at a time
        self._stop_loss_pct = 0.75  # Wide stop loss at 0.75%
        self._take_profit_pct = 1.5  # High take profit at 1.5% for 2:1 R:R ratio

        # Initialize analyzers
        self._technical_analyzer = TechnicalAnalysis()
        self._market_analyzer = MarketAnalyzer()
        self._enhanced_analyzer = EnhancedMarketAnalyzer()

        # Trading data storage
        self._positions = {}
        self._trade_history = []
        self._market_data = {}
        self._trend_analysis = {}
        self._performance_stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0
        }

        # Conservative strategy settings - focus on high-probability trades
        self._strategies = {
            'trend_following': {'enabled': True, 'weight': 0.5},
            'breakout': {'enabled': False, 'weight': 0.0},  # Disabled for safety
            'mean_reversion': {'enabled': True, 'weight': 0.3},
            'momentum': {'enabled': True, 'weight': 0.2},
            'sentiment': {'enabled': False, 'weight': 0.0}  # Disabled for safety
        }

        # News and sentiment (disabled for safety)
        self._news_sources = []
        self._market_sentiment = {}

        # GUI components
        self._gui = None
        self._charts = {}
        self._status_indicators = {}

        # Control flags
        self._trading_enabled = False
        self._analysis_running = False
        self._gui_running = False

        # Get account information
        self._initialize_account()

        print("\n" + "="*70)
        print("🛡️ SAFE ULTIMATE TRADING BOT INITIALIZED 🛡️")
        print("="*70)
        print(f"Account Balance: ${self._balance:.2f}")
        print(f"Instruments: {', '.join(self._instruments)}")
        print(f"Risk per Trade: {self._risk_per_trade*100}%")
        print(f"Max Positions: {self._max_positions}")
        print(f"Stop Loss: {self._stop_loss_pct}%")
        print(f"Take Profit: {self._take_profit_pct}%")
        print("\n🎯 Active Strategies:")
        for strategy, config in self._strategies.items():
            if config['enabled']:
                print(f"  ✅ {strategy.replace('_', ' ').title()} (Weight: {config['weight']})")
        print("\n🔒 Conservative settings for maximum safety!")
        print("="*70)

    def _initialize_account(self):
        """Initialize account information."""
        try:
            summary = self.get_account_summary()
            self._balance = float(summary.get('balance', 10000.0))
            self._currency = summary.get('currency', 'USD')
            self._margin_available = float(summary.get('marginAvailable', 0.0))
        except Exception as e:
            print(f"Warning: Could not get account summary: {str(e)}")
            self._balance = 10000.0
            self._currency = 'USD'
            self._margin_available = 0.0

    def start_gui(self):
        """Start the GUI interface."""
        if self._gui_running:
            return

        self._gui = UltimateTraderGUISafe(self)
        self._gui_running = True

        # Start GUI in separate thread
        gui_thread = threading.Thread(target=self._gui.run, daemon=True)
        gui_thread.start()

        # AUTO-START TRADING for safety testing
        print("\n🔄 Auto-starting trading in 3 seconds...")
        time.sleep(3)
        self.start_trading()

    def start_trading(self):
        """Start automated trading."""
        if self._trading_enabled:
            print("Trading already enabled!")
            return

        self._trading_enabled = True
        print("\n▶️ Starting SAFE Ultimate Trading Bot...")

        # Start trading thread
        trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
        trading_thread.start()

        # Start analysis thread
        analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        analysis_thread.start()

    def stop_trading(self):
        """Stop automated trading."""
        if not self._trading_enabled:
            return

        self._trading_enabled = False
        print("\n⏹️ Stopping SAFE Ultimate Trading Bot...")

        # Close all positions
        self._close_all_positions()

    def _trading_loop(self):
        """Main trading loop with conservative timing."""
        print("Safe trading loop started...")

        while self._trading_enabled:
            try:
                # Update market analysis
                self._update_market_analysis()

                # Manage existing positions
                self._manage_positions()

                # Look for new opportunities (only if no positions open)
                if len(self._positions) == 0:
                    opportunities = self._find_trading_opportunities()
                    if opportunities:
                        # Take only the best opportunity
                        opportunity = opportunities[0]
                        self._open_position(opportunity)

                # Update GUI
                self._update_gui()

                # Longer wait time for safer trading
                time.sleep(60)  # 60-second cycles for more analysis time

            except Exception as e:
                print(f"Error in safe trading loop: {str(e)}")
                time.sleep(30)

    def _analysis_loop(self):
        """Continuous market analysis loop."""
        print("Safe analysis loop started...")

        while self._trading_enabled:
            try:
                # Update performance stats
                self._update_performance_stats()

                time.sleep(120)  # Update every 2 minutes

            except Exception as e:
                print(f"Error in safe analysis loop: {str(e)}")
                time.sleep(60)
        
    def _update_market_analysis(self):
        """Update market analysis for all instruments."""
        for instrument in self._instruments:
            try:
                df = self._get_market_data(instrument)
                if df is None:
                    continue

                self._market_data[instrument] = df
                analysis = self._analyze_instrument(instrument, df)
                self._trend_analysis[instrument] = analysis

            except Exception as e:
                print(f"Error analyzing {instrument}: {str(e)}")

    def _get_market_data(self, instrument, count=100):
        """Get historical market data."""
        try:
            response = self.ctx.instrument.candles(
                instrument,
                granularity="M5",
                count=count,
                price="M"
            )

            if response.status != 200:
                return None

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

            if len(data) < 50:
                return None

            df = pd.DataFrame(data[-80:])
            df.set_index('time', inplace=True)
            return df

        except Exception as e:
            print(f"Error getting data for {instrument}: {str(e)}")
            return None

    def _analyze_instrument(self, instrument, df):
        """Perform conservative analysis."""
        analysis = {
            'instrument': instrument,
            'timestamp': datetime.now(),
            'strategies': {},
            'overall_score': 0.0,
            'recommendation': 'HOLD'
        }

        # Trend Following Strategy
        if self._strategies['trend_following']['enabled']:
            trend_score = self._analyze_trend_following(df)
            analysis['strategies']['trend_following'] = trend_score

        # Momentum Strategy
        if self._strategies['momentum']['enabled']:
            momentum_score = self._analyze_momentum(df)
            analysis['strategies']['momentum'] = momentum_score

        # Mean Reversion Strategy
        if self._strategies['mean_reversion']['enabled']:
            reversion_score = self._analyze_mean_reversion(df)
            analysis['strategies']['mean_reversion'] = reversion_score

        # Calculate overall score with conservative thresholds
        total_weight = sum(config['weight'] for config in self._strategies.values() if config['enabled'])
        weighted_score = 0.0

        for strategy, score in analysis['strategies'].items():
            weight = self._strategies[strategy]['weight']
            weighted_score += score * weight

        analysis['overall_score'] = weighted_score / total_weight if total_weight > 0 else 0.0

        # VERY conservative recommendation thresholds
        if analysis['overall_score'] > 0.8:
            analysis['recommendation'] = 'BUY'
        elif analysis['overall_score'] < -0.8:
            analysis['recommendation'] = 'SELL'
        else:
            analysis['recommendation'] = 'HOLD'

        return analysis

    def _analyze_trend_following(self, df):
        """Conservative trend analysis."""
        try:
            # Simple moving average crossover
            sma_short = df['close'].rolling(window=10).mean()
            sma_long = df['close'].rolling(window=30).mean()

            current_short = sma_short.iloc[-1]
            current_long = sma_long.iloc[-1]
            prev_short = sma_short.iloc[-2]
            prev_long = sma_long.iloc[-2]

            # Strong trend signals only
            if current_short > current_long and prev_short <= prev_long:
                return 0.9  # Strong buy signal
            elif current_short < current_long and prev_short >= prev_long:
                return -0.9  # Strong sell signal
            else:
                return 0.0

        except Exception as e:
            return 0.0

    def _analyze_momentum(self, df):
        """Conservative momentum analysis."""
        try:
            # RSI analysis
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            current_rsi = rsi.iloc[-1]

            # Very conservative RSI signals
            if current_rsi < 25:
                return 0.8  # Oversold
            elif current_rsi > 75:
                return -0.8  # Overbought
            else:
                return 0.0

        except Exception as e:
            return 0.0

    def _analyze_mean_reversion(self, df):
        """Conservative mean reversion analysis."""
        try:
            # Bollinger Bands
            sma = df['close'].rolling(window=20).mean()
            std = df['close'].rolling(window=20).std()
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)

            current_price = df['close'].iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]

            # Only extreme conditions
            if current_price < current_lower * 0.995:  # Very oversold
                return 0.7
            elif current_price > current_upper * 1.005:  # Very overbought
                return -0.7
            else:
                return 0.0

        except Exception as e:
            return 0.0

    def _find_trading_opportunities(self):
        """Find very conservative trading opportunities."""
        opportunities = []

        for instrument in self._instruments:
            analysis = self._trend_analysis.get(instrument)
            if not analysis:
                continue

            score = analysis['overall_score']
            recommendation = analysis['recommendation']

            # VERY strict criteria - only very strong signals
            if abs(score) > 0.7 and recommendation in ['BUY', 'SELL']:
                opportunities.append({
                    'instrument': instrument,
                    'score': score,
                    'recommendation': recommendation,
                    'analysis': analysis,
                    'direction': 1 if score > 0 else -1
                })

        # Sort by absolute score
        opportunities.sort(key=lambda x: abs(x['score']), reverse=True)
        return opportunities

    def _open_position(self, opportunity):
        """Open a position with conservative sizing."""
        instrument = opportunity['instrument']
        direction = opportunity['direction']

        try:
            units = self._calculate_position_size(instrument)

            if direction > 0:
                order = self.create_order(instrument, units, suppress=True, ret=True)
                position_type = 'long'
            else:
                order = self.create_order(instrument, -units, suppress=True, ret=True)
                position_type = 'short'

            if order:
                position = {
                    'type': position_type,
                    'units': units,
                    'entry_price': float(order['price']),
                    'entry_time': datetime.now(),
                    'instrument': instrument,
                    'opportunity': opportunity,
                    'current_price': float(order['price']),
                    'profit_pct': 0.0,
                    'status': 'active'
                }

                self._positions[instrument] = position

                print(f"\n🛡️ SAFE POSITION OPENED 🛡️")
                print(f"Instrument: {instrument}")
                print(f"Type: {position_type.upper()}")
                print(f"Units: {units}")
                print(f"Entry Price: ${float(order['price']):.5f}")
                print(f"Strategy Score: {opportunity['score']:.2f}")
                print(f"Stop Loss: {self._stop_loss_pct}% | Take Profit: {self._take_profit_pct}%")

        except Exception as e:
            print(f"Error opening safe position for {instrument}: {str(e)}")

    def _manage_positions(self):
        """Manage positions with conservative exits."""
        instruments_to_close = []

        for instrument, position in self._positions.items():
            try:
                time_val, bid, ask = self.get_prices(instrument)
                current_price = bid

                entry_price = position['entry_price']
                if position['type'] == 'long':
                    profit_pct = (current_price - entry_price) / entry_price * 100
                else:
                    profit_pct = (entry_price - current_price) / entry_price * 100

                position['current_price'] = current_price
                position['profit_pct'] = profit_pct

                should_close = False
                reason = ""

                if profit_pct <= -self._stop_loss_pct:
                    should_close = True
                    reason = "Stop Loss"
                elif profit_pct >= self._take_profit_pct:
                    should_close = True
                    reason = "Take Profit"

                if should_close:
                    instruments_to_close.append((instrument, reason, profit_pct))

            except Exception as e:
                print(f"Error managing safe position {instrument}: {str(e)}")

        for instrument, reason, profit_pct in instruments_to_close:
            self._close_position(instrument, reason, profit_pct)

    def _close_position(self, instrument, reason="Manual", profit_pct=0.0):
        """Close a position."""
        if instrument not in self._positions:
            return

        position = self._positions[instrument]

        try:
            units = position['units']

            if position['type'] == 'long':
                order = self.create_order(instrument, -units, suppress=True, ret=True)
            else:
                order = self.create_order(instrument, units, suppress=True, ret=True)

            if order:
                pnl = float(order['pl'])

                trade = {
                    'instrument': instrument,
                    'type': position['type'],
                    'entry_price': position['entry_price'],
                    'exit_price': position['current_price'],
                    'entry_time': position['entry_time'],
                    'exit_time': datetime.now(),
                    'pnl': pnl,
                    'profit_pct': profit_pct,
                    'reason': reason,
                    'strategy_score': position['opportunity']['score']
                }

                self._trade_history.append(trade)

                print(f"\n💰 SAFE POSITION CLOSED 💰")
                print(f"Instrument: {instrument}")
                print(f"P&L: ${pnl:.2f} ({profit_pct:.2f}%)")
                print(f"Reason: {reason}")

                del self._positions[instrument]

        except Exception as e:
            print(f"Error closing safe position {instrument}: {str(e)}")

    def _calculate_position_size(self, instrument):
        """Calculate conservative position size."""
        try:
            time_val, bid, ask = self.get_prices(instrument)
            price = bid

            risk_amount = self._balance * self._risk_per_trade
            stop_loss_price = price * self._stop_loss_pct / 100
            units = int(risk_amount / stop_loss_price)

            # Very conservative limits
            max_units = int(self._balance * 0.005 / price)  # Max 0.5% of balance
            units = min(units, max_units, 1000)

            return max(units, 10)

        except Exception as e:
            return 10

    def _update_performance_stats(self):
        """Update performance statistics."""
        if not self._trade_history:
            return

        trades = self._trade_history[-50:]  # Last 50 trades

        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] <= 0]

        self._performance_stats.update({
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'total_pnl': sum(t['pnl'] for t in trades),
            'win_rate': len(winning_trades) / len(trades) if trades else 0,
            'avg_win': np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0,
            'avg_loss': np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0,
        })

    def _close_all_positions(self):
        """Close all open positions."""
        instruments_to_close = list(self._positions.keys())
        for instrument in instruments_to_close:
            self._close_position(instrument, "Manual Close")

    def _update_gui(self):
        """Update GUI in a thread-safe manner."""
        if self._gui and self._gui.root:
            try:
                # Use after() to schedule GUI updates in the main thread
                self._gui.root.after(0, lambda: self._safe_gui_update())
            except Exception as e:
                print(f"Error scheduling safe GUI update: {str(e)}")

    def _safe_gui_update(self):
        """Thread-safe GUI update method."""
        try:
            if self._gui:
                self._gui.update_positions(self._positions)
                self._gui.update_analysis(self._trend_analysis)
                self._gui.update_performance(self._performance_stats)

                for instrument in self._instruments:
                    if instrument in self._market_data:
                        self._gui.update_chart(instrument, self._market_data[instrument])
        except Exception as e:
            print(f"Error in safe GUI update: {str(e)}")


class UltimateTraderGUISafe:
    """Simplified GUI for safe trading."""

    def __init__(self, trader):
        self.trader = trader
        self.root = None
                        
    def run(self):
        """Start the GUI."""
        self.root = tk.Tk()
        self.root.title("🛡️ Safe Ultimate Trading Bot 🛡️")
        self.root.geometry("1200x800")

        self._create_widgets()
        self.root.mainloop()

    def _create_widgets(self):
        """Create GUI widgets."""
        # Status frame
        status_frame = ttk.LabelFrame(self.root, text="🤖 Bot Status", padding=10)
        status_frame.pack(fill=tk.X, pady=10)

        self.status_label = ttk.Label(status_frame, text="🟢 Safe Trading Active", foreground="green", font=('Arial', 12, 'bold'))
        self.status_label.pack()

        ttk.Label(status_frame, text=f"Balance: ${self.trader._balance:.2f}", font=('Arial', 10)).pack()
        ttk.Label(status_frame, text=f"Risk per Trade: {self.trader._risk_per_trade*100}%", font=('Arial', 10)).pack()
        ttk.Label(status_frame, text=f"Stop Loss: {self.trader._stop_loss_pct}% | Take Profit: {self.trader._take_profit_pct}%", font=('Arial', 10)).pack()

        # Performance frame
        perf_frame = ttk.LabelFrame(self.root, text="📊 Performance", padding=10)
        perf_frame.pack(fill=tk.X, pady=10)

        self.perf_labels = {}
        metrics = ['Total Trades', 'Win Rate', 'Total P&L', 'Avg Win', 'Avg Loss']
        for i, metric in enumerate(metrics):
            ttk.Label(perf_frame, text=f"{metric}:").grid(row=i//3, column=(i%3)*2, sticky=tk.W, padx=5)
            self.perf_labels[metric] = ttk.Label(perf_frame, text="0.00")
            self.perf_labels[metric].grid(row=i//3, column=(i%3)*2+1, sticky=tk.W, padx=5)

        # Activity log
        log_frame = ttk.LabelFrame(self.root, text="📝 Activity Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.activity_log = scrolledtext.ScrolledText(log_frame, height=20, font=('Consolas', 9))
        self.activity_log.pack(fill=tk.BOTH, expand=True)

        # Log initial status
        self.log_activity("🛡️ Safe Ultimate Trading Bot started!")
        self.log_activity(f"Conservative settings: 0.5% risk, 1 position max, wide stops")
        self.log_activity("Only very strong signals will trigger trades")

    def update_positions(self, positions):
        """Update position display."""
        count = len(positions)
        status_text = f"🟢 Safe Trading Active - {count} position{'s' if count != 1 else ''} open"
        color = "green" if count <= 1 else "orange"
        self.status_label.config(text=status_text, foreground=color)

    def update_analysis(self, analysis):
        """Update analysis display."""
        # Could add more detailed analysis display here
        pass

    def update_performance(self, stats):
        """Update performance statistics."""
        self.perf_labels['Total Trades'].config(text=str(stats.get('total_trades', 0)))
        self.perf_labels['Win Rate'].config(text=f"{stats.get('win_rate', 0):.1%}")
        self.perf_labels['Total P&L'].config(text=f"${stats.get('total_pnl', 0):.2f}")
        self.perf_labels['Avg Win'].config(text=f"${stats.get('avg_win', 0):.2f}")
        self.perf_labels['Avg Loss'].config(text=f"${stats.get('avg_loss', 0):.2f}")

    def update_chart(self, instrument, df):
        """Chart updates not implemented in safe version."""
        pass

    def log_activity(self, message):
        """Log activity."""
        if hasattr(self, 'activity_log'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.activity_log.insert(tk.END, f"[{timestamp}] {message}\n")
            self.activity_log.see(tk.END)


# Main execution
if __name__ == "__main__":
    print("\n🛡️ Starting SAFE Ultimate Trading Bot 🛡️")

    # Initialize the safe bot
    bot = UltimateTraderSafe()

    # Start GUI (which auto-starts trading)
    bot.start_gui()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️ Shutting down Safe Ultimate Trading Bot...")
        bot.stop_trading()
