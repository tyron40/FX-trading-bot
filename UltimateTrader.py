"""
Ultimate Trading Bot - Complete Multi-Strategy, Multi-Instrument Auto Trader

Features:
- Multi-instrument trend following (5 major pairs)
- Advanced technical analysis with trendlines
- Multiple trading strategies (trend, breakout, reversal)
- Real-time GUI with live charts and positions
- Risk management with dynamic position sizing
- Performance tracking and analytics
- Market sentiment analysis
- News and RSS integration
- Automated trade execution and management
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

class UltimateTrader(tpqoa):
    """
    The Ultimate Trading Bot combining all strategies and features
    """

    def __init__(self, cfg_path="config/oanda_practice.cfg"):
        """
        Initialize the Ultimate Trading Bot
        """
        super().__init__(cfg_path)

        # Core configuration - optimized for profitability
        self._instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD']
        self._risk_per_trade = 0.02  # 2% per trade for better returns
        self._max_positions = 7  # Maximum concurrent positions (increased for more opportunities)
        self._stop_loss_pct = 0.15  # 0.15% stop loss (slightly wider)
        self._take_profit_pct = 0.35  # 0.35% take profit (higher target)

        # Initialize analyzers
        self._technical_analyzer = TechnicalAnalysis()
        self._market_analyzer = MarketAnalyzer()
        self._enhanced_analyzer = EnhancedMarketAnalyzer()

        # Trading data storage
        self._positions = {}  # Active positions
        self._trade_history = []  # Completed trades
        self._market_data = {}  # Historical data per instrument
        self._trend_analysis = {}  # Trend analysis per instrument
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

        # Strategy settings - optimized for profitability (increased aggressive strategy weights)
        self._strategies = {
            'trend_following': {'enabled': True, 'weight': 0.4},
            'breakout': {'enabled': True, 'weight': 0.4},
            'mean_reversion': {'enabled': True, 'weight': 0.15},
            'momentum': {'enabled': True, 'weight': 0.5},
            'sentiment': {'enabled': True, 'weight': 0.1}
        }

        # News and sentiment
        self._news_sources = [
            'https://www.investing.com/rss/news.rss',
            'https://www.forexnews.com/feed/',
            'https://www.dailyfx.com/feeds/all'
        ]
        self._market_sentiment = {}

        # GUI components (will be initialized later)
        self._gui = None
        self._charts = {}
        self._status_indicators = {}

        # Control flags
        self._trading_enabled = False
        self._analysis_running = False
        self._gui_running = False

        # Get account information
        self._initialize_account()

        print("\n" + "="*60)
        print("🚀 ULTIMATE TRADING BOT INITIALIZED 🚀")
        print("="*60)
        print(f"Account Balance: ${self._balance:.2f}")
        print(f"Instruments: {', '.join(self._instruments)}")
        print(f"Risk per Trade: {self._risk_per_trade*100}%")
        print(f"Max Positions: {self._max_positions}")
        print("\n🎯 Active Strategies:")
        for strategy, config in self._strategies.items():
            if config['enabled']:
                print(f"  ✅ {strategy.replace('_', ' ').title()} (Weight: {config['weight']})")
        print("\n🔥 Ready for automated trading!")
        print("="*60)

    def _initialize_account(self):
        """Initialize account information and settings."""
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

        self._gui = UltimateTraderGUI(self)
        self._gui_running = True

        # Start GUI in separate thread
        gui_thread = threading.Thread(target=self._gui.run, daemon=True)
        gui_thread.start()

    def start_trading(self):
        """Start automated trading."""
        if self._trading_enabled:
            print("Trading already enabled!")
            return

        self._trading_enabled = True
        print("\n▶️ Starting Ultimate Trading Bot...")

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
        print("\n⏹️ Stopping Ultimate Trading Bot...")

        # Close all positions
        self._close_all_positions()

    def _trading_loop(self):
        """Main trading loop."""
        print("Trading loop started...")

        while self._trading_enabled:
            try:
                # Update market analysis
                self._update_market_analysis()

                # Manage existing positions
                self._manage_positions()

                # Look for new opportunities
                if len(self._positions) < self._max_positions:
                    opportunities = self._find_trading_opportunities()
                    for opportunity in opportunities:
                        if len(self._positions) >= self._max_positions:
                            break
                        if opportunity['instrument'] not in self._positions:
                            self._open_position(opportunity)

                # Update GUI
                self._update_gui()

                # Wait before next cycle
                time.sleep(15)  # 15-second cycles

            except Exception as e:
                print(f"Error in trading loop: {str(e)}")
                time.sleep(5)

    def _analysis_loop(self):
        """Continuous market analysis loop."""
        print("Analysis loop started...")

        while self._trading_enabled:
            try:
                # Update news and sentiment
                self._update_news_sentiment()

                # Update technical analysis
                self._update_technical_analysis()

                # Update performance stats
                self._update_performance_stats()

                time.sleep(60)  # Update every minute

            except Exception as e:
                print(f"Error in analysis loop: {str(e)}")
                time.sleep(30)

    def _update_market_analysis(self):
        """Update comprehensive market analysis for all instruments."""
        for instrument in self._instruments:
            try:
                # Get latest market data
                df = self._get_market_data(instrument)
                if df is None:
                    continue

                self._market_data[instrument] = df

                # Perform multi-strategy analysis
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
        """Perform comprehensive analysis on an instrument."""
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

        # Breakout Strategy
        if self._strategies['breakout']['enabled']:
            breakout_score = self._analyze_breakout(df)
            analysis['strategies']['breakout'] = breakout_score

        # Momentum Strategy
        if self._strategies['momentum']['enabled']:
            momentum_score = self._analyze_momentum(df)
            analysis['strategies']['momentum'] = momentum_score

        # Mean Reversion Strategy
        if self._strategies['mean_reversion']['enabled']:
            reversion_score = self._analyze_mean_reversion(df)
            analysis['strategies']['mean_reversion'] = reversion_score

        # Sentiment Analysis
        if self._strategies['sentiment']['enabled']:
            sentiment_score = self._market_sentiment.get(instrument, 0.0)
            analysis['strategies']['sentiment'] = sentiment_score

        # Calculate overall score
        total_weight = sum(config['weight'] for config in self._strategies.values() if config['enabled'])
        weighted_score = 0.0

        for strategy, score in analysis['strategies'].items():
            weight = self._strategies[strategy]['weight']
            weighted_score += score * weight

        analysis['overall_score'] = weighted_score / total_weight if total_weight > 0 else 0.0

        # Generate recommendation - lowered thresholds for more aggressive trading
        if analysis['overall_score'] > 0.5:
            analysis['recommendation'] = 'STRONG_BUY'
        elif analysis['overall_score'] > 0.2:
            analysis['recommendation'] = 'BUY'
        elif analysis['overall_score'] < -0.5:
            analysis['recommendation'] = 'STRONG_SELL'
        elif analysis['overall_score'] < -0.2:
            analysis['recommendation'] = 'SELL'
        else:
            analysis['recommendation'] = 'HOLD'

        return analysis
            
    def _analyze_trend_following(self, df):
        try:
            # Use technical analyzer for trendlines
            analysis = self._technical_analyzer.analyze_chart(df)

            # Calculate trend strength
            trendlines = analysis.get('trendlines', [])
            if not trendlines:
                return 0.0

            # Average trendline strength
            avg_strength = np.mean([line['strength'] for line in trendlines])

            # Price position relative to trendlines
            current_price = df['close'].iloc[-1]
            bullish_signals = 0
            bearish_signals = 0

            for line in trendlines:
                line_value = line['slope'] * len(df) + line['intercept']
                if line['type'] == 'support' and current_price > line_value:
                    bullish_signals += 1
                elif line['type'] == 'resistance' and current_price < line_value:
                    bearish_signals += 1

            # Calculate score (-1 to 1)
            trend_score = (bullish_signals - bearish_signals) / max(1, bullish_signals + bearish_signals)
            strength_multiplier = min(avg_strength / 5, 1.0)

            return trend_score * strength_multiplier

        except Exception as e:
            print(f"Error in trend analysis: {str(e)}")
            return 0.0

    def _analyze_breakout(self, df):
        """Analyze breakout signals."""
        try:
            analysis = self._technical_analyzer.analyze_chart(df)
            breakouts = analysis.get('breakouts', [])

            if not breakouts:
                return 0.0

            # Calculate breakout strength
            total_strength = sum(breakout['strength'] for breakout in breakouts)
            avg_strength = total_strength / len(breakouts)

            # Direction bias
            bullish_breakouts = sum(1 for b in breakouts if b['direction'] > 0)
            bearish_breakouts = sum(1 for b in breakouts if b['direction'] < 0)

            direction_score = (bullish_breakouts - bearish_breakouts) / max(1, len(breakouts))

            return direction_score * min(avg_strength / 5, 1.0)

        except Exception as e:
            print(f"Error in breakout analysis: {str(e)}")
            return 0.0

    def _analyze_momentum(self, df):
        """Analyze momentum signals."""
        try:
            # RSI analysis
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            current_rsi = rsi.iloc[-1]

            # MACD analysis
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            macd_histogram = macd - signal

            current_macd = macd_histogram.iloc[-1]

            # Combine signals
            rsi_score = (current_rsi - 50) / 50  # -1 to 1
            macd_score = np.tanh(current_macd * 100)  # Normalize

            momentum_score = (rsi_score + macd_score) / 2
            return momentum_score

        except Exception as e:
            print(f"Error in momentum analysis: {str(e)}")
            return 0.0

    def _analyze_mean_reversion(self, df):
        """Analyze mean reversion signals."""
        try:
            # Bollinger Bands
            sma = df['close'].rolling(window=20).mean()
            std = df['close'].rolling(window=20).std()
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)

            current_price = df['close'].iloc[-1]
            current_sma = sma.iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]

            # Position relative to bands
            if current_price > current_upper:
                # Overbought - potential sell
                distance = (current_price - current_upper) / (current_upper - current_sma)
                return -min(distance, 1.0)
            elif current_price < current_lower:
                # Oversold - potential buy
                distance = (current_lower - current_price) / (current_sma - current_lower)
                return min(distance, 1.0)
            else:
                # Within bands - neutral
                return 0.0

        except Exception as e:
            print(f"Error in mean reversion analysis: {str(e)}")
            return 0.0
                    
    def _find_trading_opportunities(self):
        """Find all valid trading opportunities."""
        opportunities = []

        for instrument in self._instruments:
            if instrument in self._positions:
                continue

            analysis = self._trend_analysis.get(instrument)
            if not analysis:
                continue

            score = analysis['overall_score']
            recommendation = analysis['recommendation']

            # Only trade strong signals - lowered threshold for more trades
            if abs(score) > 0.3:
                opportunities.append({
                    'instrument': instrument,
                    'score': score,
                    'recommendation': recommendation,
                    'analysis': analysis,
                    'direction': 1 if score > 0 else -1
                })

        # Sort by absolute score (best opportunities first)
        opportunities.sort(key=lambda x: abs(x['score']), reverse=True)

        return opportunities

    def _open_position(self, opportunity):
        """Open a new position."""
        instrument = opportunity['instrument']
        direction = opportunity['direction']

        try:
            # Calculate position size
            units = self._calculate_position_size(instrument)

            # Open position
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

                print(f"\n🎯 NEW POSITION OPENED 🎯")
                print(f"Instrument: {instrument}")
                print(f"Type: {position_type.upper()}")
                print(f"Units: {units}")
                print(f"Entry Price: ${float(order['price']):.5f}")
                print(f"Strategy Score: {opportunity['score']:.2f}")
                print(f"Recommendation: {opportunity['recommendation']}")

        except Exception as e:
            print(f"Error opening position for {instrument}: {str(e)}")

    def _manage_positions(self):
        """Manage existing positions."""
        instruments_to_close = []

        for instrument, position in self._positions.items():
            try:
                # Get current price
                time_val, bid, ask = self.get_prices(instrument)
                current_price = bid

                # Calculate P&L
                entry_price = position['entry_price']
                if position['type'] == 'long':
                    profit_pct = (current_price - entry_price) / entry_price * 100
                else:
                    profit_pct = (entry_price - current_price) / entry_price * 100

                # Update position
                position['current_price'] = current_price
                position['profit_pct'] = profit_pct

                # Check exit conditions
                should_close = False
                reason = ""

                # Stop loss
                if profit_pct <= -self._stop_loss_pct:
                    should_close = True
                    reason = "Stop Loss"

                # Take profit
                elif profit_pct >= self._take_profit_pct:
                    should_close = True
                    reason = "Take Profit"

                # Strategy-based exit
                elif self._should_exit_position(position):
                    should_close = True
                    reason = "Strategy Exit"

                if should_close:
                    instruments_to_close.append((instrument, reason, profit_pct))

            except Exception as e:
                print(f"Error managing position {instrument}: {str(e)}")

        # Close positions
        for instrument, reason, profit_pct in instruments_to_close:
            self._close_position(instrument, reason, profit_pct)

    def _should_exit_position(self, position):
        """Determine if position should be exited based on strategy."""
        instrument = position['instrument']
        analysis = self._trend_analysis.get(instrument)

        if not analysis:
            return False

        current_score = analysis['overall_score']
        entry_score = position['opportunity']['score']

        # Exit if strategy has reversed significantly
        if position['type'] == 'long' and current_score < -0.3:
            return True
        elif position['type'] == 'short' and current_score > 0.3:
            return True

        # Exit if momentum has weakened significantly
        if abs(current_score) < abs(entry_score) * 0.5:
            return True

        return False

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

                # Record trade
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

                print(f"\n💰 POSITION CLOSED 💰")
                print(f"Instrument: {instrument}")
                print(f"P&L: ${pnl:.2f} ({profit_pct:.2f}%)")
                print(f"Reason: {reason}")
                print(f"Entry: ${position['entry_price']:.5f}")
                print(f"Exit: ${position['current_price']:.5f}")

                del self._positions[instrument]

        except Exception as e:
            print(f"Error closing position {instrument}: {str(e)}")

    def _close_all_positions(self):
        """Close all open positions."""
        for instrument in list(self._positions.keys()):
            self._close_position(instrument, "System Shutdown")

    def _calculate_position_size(self, instrument):
        """Calculate position size based on risk management."""
        try:
            # Get current price
            time_val, bid, ask = self.get_prices(instrument)
            price = bid

            # Risk amount per position
            risk_amount = self._balance * self._risk_per_trade

            # Stop loss in price terms
            stop_loss_price = price * self._stop_loss_pct / 100

            # Calculate units
            units = int(risk_amount / stop_loss_price)

            # Apply limits
            max_units = int(self._balance * 0.1 / price)  # Max 10% of balance
            units = min(units, max_units, 50000)

            return max(units, 100)

        except Exception as e:
            print(f"Error calculating position size for {instrument}: {str(e)}")
            return 100

    def _update_news_sentiment(self):
        """Update news and market sentiment."""
        try:
            sentiment_scores = {}

            for url in self._news_sources:
                try:
                    feed = feedparser.parse(url)
                    for entry in feed.entries[:5]:  # Last 5 articles
                        title = entry.title.lower()

                        # Simple sentiment analysis
                        positive_words = ['bullish', 'rally', 'gains', 'surge', 'rise', 'up', 'strong']
                        negative_words = ['bearish', 'fall', 'drop', 'decline', 'weak', 'down', 'crash']

                        pos_score = sum(1 for word in positive_words if word in title)
                        neg_score = sum(1 for word in negative_words if word in title)

                        # Map to instruments
                        for instrument in self._instruments:
                            if instrument.replace('_', '').lower() in title:
                                if instrument not in sentiment_scores:
                                    sentiment_scores[instrument] = 0.0
                                sentiment_scores[instrument] += (pos_score - neg_score) * 0.1

                except Exception as e:
                    continue

            # Normalize sentiment scores
            for instrument in sentiment_scores:
                sentiment_scores[instrument] = np.tanh(sentiment_scores[instrument])

            self._market_sentiment = sentiment_scores

        except Exception as e:
            print(f"Error updating news sentiment: {str(e)}")

    def _update_technical_analysis(self):
        """Update technical analysis for all instruments."""
        # This is handled in _update_market_analysis
        pass

    def _update_performance_stats(self):
        """Update performance statistics."""
        if not self._trade_history:
            return

        trades = self._trade_history[-100:]  # Last 100 trades

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

        # Calculate Sharpe ratio (simplified)
        if len(trades) > 1:
            returns = [t['pnl'] for t in trades]
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            self._performance_stats['sharpe_ratio'] = avg_return / std_return if std_return > 0 else 0

    def _update_gui(self):
        """Update GUI with current status."""
        if self._gui:
            try:
                # Update positions
                self._gui.update_positions(self._positions)

                # Update analysis
                self._gui.update_analysis(self._trend_analysis)

                # Update performance
                self._gui.update_performance(self._performance_stats)

                # Update charts
                for instrument in self._instruments:
                    if instrument in self._market_data:
                        self._gui.update_chart(instrument, self._market_data[instrument])

            except Exception as e:
                print(f"Error updating GUI: {str(e)}")

    def get_status(self):
        """Get current bot status."""
        return {
            'trading_enabled': self._trading_enabled,
            'active_positions': len(self._positions),
            'total_trades': len(self._trade_history),
            'current_balance': self._balance,
            'performance': self._performance_stats
        }


class UltimateTraderGUI:
    """
    Comprehensive GUI for the Ultimate Trading Bot
    """

    def __init__(self, trader):
        self.trader = trader
        self.root = None
        self.charts = {}
        self.indicators = {}

    def run(self):
        """Start the GUI."""
        self.root = tk.Tk()
        self.root.title("🚀 Ultimate Trading Bot 🚀")
        self.root.geometry("1800x1200")
        self.root.configure(bg='#1e1e1e')

        self._create_widgets()
        self.root.mainloop()

    def _create_widgets(self):
        """Create all GUI widgets."""
        # Main container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Controls and Status
        left_panel = ttk.Frame(main_container)
        main_container.add(left_panel, weight=1)

        # Control panel
        control_frame = ttk.LabelFrame(left_panel, text="🤖 Bot Control", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # Status indicators
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill=tk.X)

        ttk.Label(status_frame, text="Status:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W)
        self.status_label = ttk.Label(status_frame, text="Initializing...", foreground="orange", font=('Arial', 10))
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 20))

        ttk.Label(status_frame, text="Balance:", font=('Arial', 10, 'bold')).grid(row=0, column=2, sticky=tk.W)
        self.balance_label = ttk.Label(status_frame, text="$0.00", font=('Arial', 10))
        self.balance_label.grid(row=0, column=3, sticky=tk.W, padx=(5, 20))

        ttk.Label(status_frame, text="Active Positions:", font=('Arial', 10, 'bold')).grid(row=0, column=4, sticky=tk.W)
        self.positions_label = ttk.Label(status_frame, text="0", font=('Arial', 10))
        self.positions_label.grid(row=0, column=5, sticky=tk.W, padx=(5, 20))

        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        self.start_button = ttk.Button(button_frame, text="▶️ Start Trading", command=self.start_trading)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_button = ttk.Button(button_frame, text="⏹️ Stop Trading", command=self.stop_trading, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))

        self.close_all_button = ttk.Button(button_frame, text="💰 Close All", command=self.close_all_positions, state=tk.DISABLED)
        self.close_all_button.pack(side=tk.LEFT, padx=(0, 10))

        # Performance panel
        perf_frame = ttk.LabelFrame(left_panel, text="📊 Performance", padding=10)
        perf_frame.pack(fill=tk.X, pady=(0, 10))

        self.perf_labels = {}
        perf_metrics = ['Total Trades', 'Win Rate', 'Total P&L', 'Avg Win', 'Avg Loss', 'Sharpe Ratio']
        for i, metric in enumerate(perf_metrics):
            ttk.Label(perf_frame, text=f"{metric}:").grid(row=i, column=0, sticky=tk.W)
            self.perf_labels[metric] = ttk.Label(perf_frame, text="0.00")
            self.perf_labels[metric].grid(row=i, column=1, sticky=tk.W, padx=(10, 0))

        # Instruments status
        instruments_frame = ttk.LabelFrame(left_panel, text="📈 Instruments", padding=10)
        instruments_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.instrument_frames = {}
        instruments = self.trader._instruments

        for i, instrument in enumerate(instruments):
            frame = ttk.Frame(instruments_frame)
            frame.pack(fill=tk.X, pady=2)

            ttk.Label(frame, text=f"{instrument}:", font=('Arial', 9, 'bold'), width=10).pack(side=tk.LEFT)

            # Trend indicator
            trend_label = ttk.Label(frame, text="Analyzing...", width=12, anchor=tk.CENTER)
            trend_label.pack(side=tk.LEFT, padx=(5, 0))
            self.instrument_frames[instrument] = {
                'trend': trend_label,
                'position': ttk.Label(frame, text="No position", width=15, anchor=tk.CENTER),
                'pnl': ttk.Label(frame, text="$0.00", width=10, anchor=tk.E),
                'score': ttk.Label(frame, text="0.00", width=8, anchor=tk.E)
            }
            self.instrument_frames[instrument]['position'].pack(side=tk.LEFT, padx=(5, 0))
            self.instrument_frames[instrument]['pnl'].pack(side=tk.RIGHT, padx=(5, 0))
            self.instrument_frames[instrument]['score'].pack(side=tk.RIGHT)

        # Activity log
        log_frame = ttk.LabelFrame(left_panel, text="📝 Activity Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.activity_log = scrolledtext.ScrolledText(log_frame, height=15, width=60, font=('Consolas', 9))
        self.activity_log.pack(fill=tk.BOTH, expand=True)

        # Right panel - Charts
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel, weight=2)

        # Charts container
        charts_frame = ttk.LabelFrame(right_panel, text="📊 Live Charts", padding=10)
        charts_frame.pack(fill=tk.BOTH, expand=True)

        # Create chart grid
        self.charts_container = ttk.Frame(charts_frame)
        self.charts_container.pack(fill=tk.BOTH, expand=True)

        # Initialize charts
        self._init_charts()

    def _init_charts(self):
        """Initialize charts for all instruments."""
        instruments = self.trader._instruments

        for i, instrument in enumerate(instruments):
            row = i // 3
            col = i % 3

            # Create frame for this instrument
            frame = ttk.LabelFrame(self.charts_container, text=instrument, padding=5)
            frame.grid(row=row, column=col, sticky=tk.NSEW, padx=2, pady=2)

            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=(5, 4))
            fig.patch.set_facecolor('#2d2d2d')
            ax.set_facecolor('#1e1e1e')
            ax.tick_params(colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('white')

            # Initial empty plot
            ax.plot([], [], 'b-', linewidth=1)
            ax.set_title(f"{instrument} - Live", fontsize=10, color='white')
            ax.grid(True, alpha=0.3)

            # Create canvas
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            self.charts[instrument] = {
                'fig': fig,
                'ax': ax,
                'canvas': canvas
            }

        # Configure grid weights
        for i in range(2):
            self.charts_container.grid_rowconfigure(i, weight=1)
        for i in range(3):
            self.charts_container.grid_columnconfigure(i, weight=1)

    def start_trading(self):
        """Start automated trading."""
        self.trader.start_trading()
        self.status_label.config(text="🟢 Trading Active", foreground="green")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.close_all_button.config(state=tk.NORMAL)
        self.log_activity("▶️ Ultimate Trading Bot started!")

    def stop_trading(self):
        """Stop automated trading."""
        self.trader.stop_trading()
        self.status_label.config(text="🔴 Trading Stopped", foreground="red")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.close_all_button.config(state=tk.DISABLED)
        self.log_activity("⏹️ Ultimate Trading Bot stopped!")

    def close_all_positions(self):
        """Close all open positions."""
        self.trader._close_all_positions()
        self.log_activity("💰 All positions closed!")

    def update_positions(self, positions):
        """Update position information."""
        self.positions_label.config(text=str(len(positions)))

        # Reset all displays
        for instrument in self.instrument_frames:
            self.instrument_frames[instrument]['position'].config(text="No position", foreground="gray")
            self.instrument_frames[instrument]['pnl'].config(text="$0.00", foreground="gray")

        # Update active positions
        for instrument, position in positions.items():
            if instrument in self.instrument_frames:
                position_type = position['type'].upper()
                profit_pct = position.get('profit_pct', 0)

                self.instrument_frames[instrument]['position'].config(
                    text=f"{position_type} ({position['units']}u)",
                    foreground="green" if position_type == "LONG" else "red"
                )

                pnl_color = "green" if profit_pct > 0 else "red" if profit_pct < 0 else "gray"
                self.instrument_frames[instrument]['pnl'].config(
                    text=f"{profit_pct:+.2f}%",
                    foreground=pnl_color
                )

    def update_analysis(self, analysis):
        """Update analysis information."""
        for instrument, data in analysis.items():
            if instrument in self.instrument_frames:
                score = data.get('overall_score', 0)
                recommendation = data.get('recommendation', 'HOLD')

                # Color code based on recommendation
                if recommendation == 'STRONG_BUY':
                    color = 'green'
                elif recommendation == 'BUY':
                    color = 'lightgreen'
                elif recommendation == 'STRONG_SELL':
                    color = 'red'
                elif recommendation == 'SELL':
                    color = 'orange'
                else:
                    color = 'gray'

                self.instrument_frames[instrument]['trend'].config(
                    text=f"{recommendation}",
                    foreground=color
                )

                self.instrument_frames[instrument]['score'].config(
                    text=f"{score:.2f}",
                    foreground=color
                )

    def update_performance(self, stats):
        """Update performance statistics."""
        self.perf_labels['Total Trades'].config(text=str(stats.get('total_trades', 0)))
        self.perf_labels['Win Rate'].config(text=f"{stats.get('win_rate', 0):.1%}")
        self.perf_labels['Total P&L'].config(text=f"${stats.get('total_pnl', 0):.2f}")
        self.perf_labels['Avg Win'].config(text=f"${stats.get('avg_win', 0):.2f}")
        self.perf_labels['Avg Loss'].config(text=f"${stats.get('avg_loss', 0):.2f}")
        self.perf_labels['Sharpe Ratio'].config(text=f"{stats.get('sharpe_ratio', 0):.2f}")

        # Update balance
        if hasattr(self.trader, '_balance'):
            self.balance_label.config(text=f"${self.trader._balance:.2f}")

    def update_chart(self, instrument, df):
        """Update chart for an instrument."""
        if instrument not in self.charts or df is None or df.empty:
            return

        try:
            fig = self.charts[instrument]['fig']
            ax = self.charts[instrument]['ax']

            # Clear previous plot
            ax.clear()

            # Plot price data
            ax.plot(df.index, df['close'], 'b-', linewidth=1.5, label='Close')

            # Add moving averages
            if len(df) > 20:
                sma20 = df['close'].rolling(window=20).mean()
                ax.plot(df.index, sma20, 'r--', linewidth=1, label='SMA20', alpha=0.7)

            if len(df) > 50:
                sma50 = df['close'].rolling(window=50).mean()
                ax.plot(df.index, sma50, 'g--', linewidth=1, label='SMA50', alpha=0.7)

            # Style the chart
            ax.set_title(f"{instrument} - Live", fontsize=10, color='white')
            ax.set_facecolor('#1e1e1e')
            ax.grid(True, alpha=0.3)
            ax.tick_params(colors='white', labelsize=8)
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')

            # Format x-axis for time
            import matplotlib.dates as mdates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            plt.setp(ax.get_xticklabels(), rotation=45)

            # Add legend
            ax.legend(loc='upper left', fontsize=8)

            # Redraw canvas
            self.charts[instrument]['canvas'].draw()

        except Exception as e:
            print(f"Error updating chart for {instrument}: {str(e)}")

    def log_activity(self, message):
        """Log activity to the activity log."""
        if hasattr(self, 'activity_log'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.activity_log.insert(tk.END, f"[{timestamp}] {message}\n")
            self.activity_log.see(tk.END)


# Main execution
if __name__ == "__main__":
    print("\n🚀 Starting Ultimate Trading Bot 🚀")

    # Initialize the bot
    bot = UltimateTrader()

    # Start GUI
    bot.start_gui()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️ Shutting down Ultimate Trading Bot...")
        bot.stop_trading()
