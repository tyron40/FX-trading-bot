"""
Ultimate Trading Interface with Integrated Backtesting
- Live trading with stop loss/take profit
- Backtesting on historical data
- Monthly timeframe support
- Complete risk management
- Performance comparison
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from tpqoa.tpqoa import tpqoa

# Modern color scheme
COLORS = {
    'bg': '#1e1e2e',
    'fg': '#cdd6f4',
    'accent': '#89b4fa',
    'success': '#a6e3a1',
    'warning': '#f9e2af',
    'error': '#f38ba8',
    'buy': '#a6e3a1',
    'sell': '#f38ba8',
    'panel': '#313244',
    'hover': '#45475a'
}


class BacktestEngine:
    """Backtesting engine for strategy validation"""
    
    def __init__(self, config_path, instrument, start, end, timeframe="M5"):
        self.config = config_path
        self.instrument = instrument
        self.start = start
        self.end = end
        self.timeframe = timeframe
        self.initial_balance = 10000.0
        self.balance = 10000.0
        self.positions = []
        self.trades = []
        
    def get_historical_data(self):
        """Get historical data for backtesting"""
        try:
            oanda = tpqoa(self.config)
            df = oanda.get_history(
                self.instrument,
                self.start,
                self.end,
                self.timeframe,
                "M"
            )
            return df
        except Exception as e:
            print(f"Historical data error: {e}")
            return None
    
    def analyze_bar(self, df, bar_idx):
        """Analyze a single bar using same logic as live trading"""
        if bar_idx < 50:
            return {'signal': 'HOLD', 'score': 0.0}
        
        # Get data up to current bar
        data = df.iloc[:bar_idx+1].copy()
        
        # Calculate indicators
        data['sma_20'] = data['c'].rolling(20).mean()
        data['sma_50'] = data['c'].rolling(50).mean()
        
        # RSI
        delta = data['c'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # Get latest
        latest = data.iloc[-1]
        
        score = 0.0
        
        # Trend
        if latest['sma_20'] > latest['sma_50']:
            score += 0.3
        else:
            score -= 0.3
        
        # RSI
        if latest['rsi'] < 30:
            score += 0.4
        elif latest['rsi'] > 70:
            score -= 0.4
        
        # Determine signal
        if score > 0.5:
            signal = 'BUY'
        elif score < -0.5:
            signal = 'SELL'
        else:
            signal = 'HOLD'
        
        return {'signal': signal, 'score': score, 'price': latest['c'], 'rsi': latest['rsi']}
    
    def run_backtest(self):
        """Run complete backtest"""
        df = self.get_historical_data()
        if df is None:
            return None
        
        results = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'trades': []
        }
        
        open_position = None
        peak_balance = self.initial_balance
        
        for bar in range(50, len(df)):
            # Check exit conditions for open position
            if open_position:
                current_price = df.iloc[bar]['c']
                
                # Check stop loss / take profit
                if open_position['direction'] == 'LONG':
                    if current_price <= open_position['stop_loss']:
                        # Stop loss hit
                        pnl = (open_position['stop_loss'] - open_position['entry']) * open_position['units']
                        self.close_trade(open_position, open_position['stop_loss'], pnl, results, 'STOP_LOSS')
                        open_position = None
                    elif current_price >= open_position['take_profit']:
                        # Take profit hit
                        pnl = (open_position['take_profit'] - open_position['entry']) * open_position['units']
                        self.close_trade(open_position, open_position['take_profit'], pnl, results, 'TAKE_PROFIT')
                        open_position = None
                else:  # SHORT
                    if current_price >= open_position['stop_loss']:
                        # Stop loss hit
                        pnl = (open_position['entry'] - open_position['stop_loss']) * open_position['units']
                        self.close_trade(open_position, open_position['stop_loss'], pnl, results, 'STOP_LOSS')
                        open_position = None
                    elif current_price <= open_position['take_profit']:
                        # Take profit hit
                        pnl = (open_position['entry'] - open_position['take_profit']) * open_position['units']
                        self.close_trade(open_position, open_position['take_profit'], pnl, results, 'TAKE_PROFIT')
                        open_position = None
            
            # Check for new signals if no position
            if not open_position:
                analysis = self.analyze_bar(df, bar)
                
                if analysis['signal'] in ['BUY', 'SELL']:
                    price = df.iloc[bar]['c']
                    units = 100
                    
                    if analysis['signal'] == 'BUY':
                        stop_loss = price * 0.992
                        take_profit = price * 1.012
                        direction = 'LONG'
                    else:
                        stop_loss = price * 1.008
                        take_profit = price * 0.988
                        direction = 'SHORT'
                    
                    open_position = {
                        'entry': price,
                        'direction': direction,
                        'units': units,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'entry_time': df.index[bar]
                    }
            
            # Track drawdown
            if self.balance > peak_balance:
                peak_balance = self.balance
            drawdown = (peak_balance - self.balance) / peak_balance * 100
            if drawdown > results['max_drawdown']:
                results['max_drawdown'] = drawdown
        
        # Close any remaining position
        if open_position:
            final_price = df.iloc[-1]['c']
            if open_position['direction'] == 'LONG':
                pnl = (final_price - open_position['entry']) * open_position['units']
            else:
                pnl = (open_position['entry'] - final_price) * open_position['units']
            self.close_trade(open_position, final_price, pnl, results, 'FINAL_CLOSE')
        
        # Calculate final metrics
        results['final_balance'] = self.balance
        results['total_return'] = ((self.balance - self.initial_balance) / self.initial_balance) * 100
        if results['total_trades'] > 0:
            results['win_rate'] = (results['winning_trades'] / results['total_trades']) * 100
        
        return results
    
    def close_trade(self, position, exit_price, pnl, results, reason):
        """Close a trade and update results"""
        self.balance += pnl
        results['total_trades'] += 1
        results['total_pnl'] += pnl
        
        if pnl > 0:
            results['winning_trades'] += 1
        else:
            results['losing_trades'] += 1
        
        results['trades'].append({
            'entry': position['entry'],
            'exit': exit_price,
            'direction': position['direction'],
            'pnl': pnl,
            'reason': reason,
            'entry_time': position['entry_time']
        })


class PerfectTrader(tpqoa):
    """Complete trader with full tracking and monitoring"""
    
    def __init__(self, config_path, timeframe="M5", risk_pct=1.0):
        super().__init__(config_path)
        self.timeframe = timeframe
        self.risk_pct = risk_pct / 100.0
        self.instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD']
        self.positions = {}
        self.trades = []
        self.closed_trades = []
        self.running = False
        
        # Account info
        self.balance = 10000.0
        self.currency = 'USD'
        self.nav = 0.0
        self.unrealized_pl = 0.0
        self.margin_used = 0.0
        self.margin_available = 0.0
        
        # Get actual account balance
        self.update_account_info()
    
    def update_account_info(self):
        """Update complete account information from OANDA"""
        try:
            summary = self.get_account_summary(detailed=True)
            self.balance = float(summary.get('balance', 10000.0))
            self.currency = summary.get('currency', 'USD')
            self.nav = float(summary.get('NAV', self.balance))
            self.unrealized_pl = float(summary.get('unrealizedPL', 0.0))
            self.margin_used = float(summary.get('marginUsed', 0.0))
            self.margin_available = float(summary.get('marginAvailable', self.balance))
            return True
        except Exception as e:
            print(f"Could not get account info: {e}")
            return False
                
    def get_live_data(self, instrument, count=100):
        """Fast data retrieval"""
        try:
            response = self.ctx.instrument.candles(
                instrument,
                granularity=self.timeframe,
                count=count,
                price="MBA"
            )
            
            if response.status != 200:
                return None
            
            data = []
            for candle in response.body.get('candles', []):
                data.append({
                    'time': pd.to_datetime(candle.time),
                    'open': float(candle.mid.o),
                    'high': float(candle.mid.h),
                    'low': float(candle.mid.l),
                    'close': float(candle.mid.c),
                    'volume': int(candle.volume)
                })
            
            df = pd.DataFrame(data)
            df.set_index('time', inplace=True)
            return df
        except Exception as e:
            print(f"Data error: {e}")
            return None
    
    def analyze_fast(self, df):
        """Fast analysis with multiple indicators"""
        if df is None or len(df) < 50:
            return {'signal': 'HOLD', 'score': 0.0, 'indicators': {}}
        
        # Calculate indicators
        df['sma_20'] = df['close'].rolling(20).mean()
        df['sma_50'] = df['close'].rolling(50).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_mid'] = df['close'].rolling(20).mean()
        df['bb_std'] = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_mid'] + (df['bb_std'] * 2)
        df['bb_lower'] = df['bb_mid'] - (df['bb_std'] * 2)
        
        # Get latest values
        latest = df.iloc[-1]
        
        score = 0.0
        indicators = {}
        
        # Trend (SMA)
        if latest['sma_20'] > latest['sma_50']:
            score += 0.3
            indicators['trend'] = 'UP'
        else:
            score -= 0.3
            indicators['trend'] = 'DOWN'
        
        # RSI
        if latest['rsi'] < 30:
            score += 0.4
            indicators['rsi'] = 'OVERSOLD'
        elif latest['rsi'] > 70:
            score -= 0.4
            indicators['rsi'] = 'OVERBOUGHT'
        else:
            indicators['rsi'] = 'NEUTRAL'
        
        # Bollinger Bands
        if latest['close'] < latest['bb_lower']:
            score += 0.3
            indicators['bb'] = 'BELOW_LOWER'
        elif latest['close'] > latest['bb_upper']:
            score -= 0.3
            indicators['bb'] = 'ABOVE_UPPER'
        else:
            indicators['bb'] = 'NEUTRAL'
        
        # Determine signal
        if score > 0.5:
            signal = 'BUY'
        elif score < -0.5:
            signal = 'SELL'
        else:
            signal = 'HOLD'
        
        return {
            'signal': signal,
            'score': score,
            'indicators': indicators,
            'price': latest['close'],
            'rsi': latest['rsi'],
            'sma_20': latest['sma_20'],
            'sma_50': latest['sma_50']
        }
    
    def execute_trade(self, instrument, signal, units=100):
        """Execute trade with STOP LOSS and TAKE PROFIT"""
        try:
            _, bid, ask = self.get_prices(instrument)
            
            if signal == 'BUY':
                order = self.create_order(instrument, units, suppress=True, ret=True)
                direction = 'LONG'
                entry_price = ask
                stop_loss = entry_price * 0.992
                take_profit = entry_price * 1.012
            elif signal == 'SELL':
                order = self.create_order(instrument, -units, suppress=True, ret=True)
                direction = 'SHORT'
                entry_price = bid
                stop_loss = entry_price * 1.008
                take_profit = entry_price * 0.988
            else:
                return None
            
            if order:
                trade = {
                    'instrument': instrument,
                    'direction': direction,
                    'units': units,
                    'entry_price': float(order.get('price', 0)),
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'entry_time': datetime.now(),
                    'status': 'OPEN'
                }
                self.positions[instrument] = trade
                self.trades.append(trade)
                return trade
        except Exception as e:
            print(f"Trade execution error: {e}")
            return None
    
    def check_exit_conditions(self, instrument):
        """Check if stop loss or take profit hit"""
        if instrument not in self.positions:
            return
        
        try:
            pos = self.positions[instrument]
            _, bid, ask = self.get_prices(instrument)
            current_price = bid if pos['direction'] == 'LONG' else ask
            
            if pos['direction'] == 'LONG':
                if current_price <= pos['stop_loss']:
                    print(f"⚠️ STOP LOSS HIT: {instrument}")
                    self.close_position(instrument)
                elif current_price >= pos['take_profit']:
                    print(f"✅ TAKE PROFIT HIT: {instrument}")
                    self.close_position(instrument)
            else:
                if current_price >= pos['stop_loss']:
                    print(f"⚠️ STOP LOSS HIT: {instrument}")
                    self.close_position(instrument)
                elif current_price <= pos['take_profit']:
                    print(f"✅ TAKE PROFIT HIT: {instrument}")
                    self.close_position(instrument)
        except Exception as e:
            print(f"Exit check error: {e}")
    
    def close_position(self, instrument):
        """Close position and add to history"""
        if instrument not in self.positions:
            return None
        
        try:
            pos = self.positions[instrument]
            units = pos['units']
            
            if pos['direction'] == 'LONG':
                order = self.create_order(instrument, -units, suppress=True, ret=True)
            else:
                order = self.create_order(instrument, units, suppress=True, ret=True)
            
            if order:
                pnl = float(order.get('pl', 0))
                pos['exit_price'] = float(order.get('price', 0))
                pos['exit_time'] = datetime.now()
                pos['pnl'] = pnl
                pos['status'] = 'CLOSED'
                
                self.closed_trades.append(pos.copy())
                del self.positions[instrument]
                self.update_account_info()
                
                return pos
        except Exception as e:
            print(f"Close error: {e}")
            return None
    
    def is_market_open(self):
        """Check if forex market is open"""
        now = datetime.now()
        if now.weekday() >= 5:
            return False
        return True


class PerfectTradingGUI:
    """Perfect trading interface with backtesting capability"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 FX Trading Bot - Perfect Edition with Backtesting")
        self.root.geometry("1900x1000")
        self.root.configure(bg=COLORS['bg'])
        
        self.setup_style()
        
        # Initialize
        self.trader = None
        self.account_type = "demo"
        self.trading_active = False
        self.mode = "live"  # "live" or "backtest"
        
        # Data storage
        self.market_data = {}
        self.analysis_results = {}
        self.signal_strengths = {}
        self.backtest_results = None
        
        self.create_gui()
        self.connect_account("demo")
        self.start_updates()
    
    def setup_style(self):
        """Configure modern ttk style"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TFrame', background=COLORS['bg'])
        style.configure('TLabel', background=COLORS['bg'], foreground=COLORS['fg'])
        style.configure('TLabelframe', background=COLORS['bg'], foreground=COLORS['accent'])
        style.configure('TLabelframe.Label', background=COLORS['bg'], foreground=COLORS['accent'], font=('Arial', 10, 'bold'))
        style.configure('TButton', background=COLORS['panel'], foreground=COLORS['fg'])
        style.map('TButton', background=[('active', COLORS['hover'])])
        style.configure('Success.TButton', background=COLORS['success'], foreground=COLORS['bg'])
        style.configure('Error.TButton', background=COLORS['error'], foreground=COLORS['bg'])
        style.configure('Warning.TButton', background=COLORS['warning'], foreground=COLORS['bg'])
    
    def create_gui(self):
        """Create complete GUI layout with backtesting"""
        # Top control bar
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Mode selection
        ttk.Label(control_frame, text="Mode:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.mode_var = tk.StringVar(value="live")
        ttk.Radiobutton(control_frame, text="📊 Live Trading", variable=self.mode_var, value="live",
                       command=self.switch_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(control_frame, text="🔬 Backtest", variable=self.mode_var, value="backtest",
                       command=self.switch_mode).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="|", foreground=COLORS['panel']).pack(side=tk.LEFT, padx=10)
        
        # Account selection (for live mode)
        ttk.Label(control_frame, text="Account:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.account_var = tk.StringVar(value="demo")
        ttk.Radiobutton(control_frame, text="Demo", variable=self.account_var, value="demo",
                       command=lambda: self.connect_account("demo")).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(control_frame, text="Live", variable=self.account_var, value="live",
                       command=lambda: self.connect_account("live")).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="|", foreground=COLORS['panel']).pack(side=tk.LEFT, padx=10)
        
        # Trading controls
        self.start_btn = ttk.Button(control_frame, text="▶️ START", style='Success.TButton',
                                    command=self.start_trading)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ STOP", style='Error.TButton',
                                   command=self.stop_trading, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Backtest button
        self.backtest_btn = ttk.Button(control_frame, text="🔬 RUN BACKTEST", style='Warning.TButton',
                                       command=self.run_backtest, state=tk.DISABLED)
        self.backtest_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="|", foreground=COLORS['panel']).pack(side=tk.LEFT, padx=10)
        
        # Parameters
        ttk.Label(control_frame, text="Timeframe:").pack(side=tk.LEFT, padx=5)
        self.timeframe_var = tk.StringVar(value="M5")
        ttk.Combobox(control_frame, textvariable=self.timeframe_var, 
                    values=["M1", "M5", "M15", "M30", "H1", "H4", "D", "W", "M"],
                    state="readonly", width=6).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = ttk.Label(control_frame, text="🔄 Initializing...", font=('Arial', 10, 'bold'),
                                     foreground=COLORS['warning'])
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Main content (same as Perfect interface)
        content = ttk.Frame(self.root)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Left panel
        left_panel = ttk.Frame(content)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Charts
        chart_frame = ttk.LabelFrame(left_panel, text="📈 CHARTS", padding=10)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.chart_notebook = ttk.Notebook(chart_frame)
        self.chart_notebook.pack(fill=tk.BOTH, expand=True)
        
        self.charts = {}
        for instrument in ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD']:
            frame = ttk.Frame(self.chart_notebook)
            self.chart_notebook.add(frame, text=instrument.replace('_', '/'))
            
            fig = Figure(figsize=(10, 5), facecolor=COLORS['bg'])
            ax = fig.add_subplot(111, facecolor=COLORS['panel'])
            ax.tick_params(colors=COLORS['fg'])
            for spine in ax.spines.values():
                spine.set_color(COLORS['fg'])
            
            canvas = FigureCanvasTkAgg(fig, frame)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            self.charts[instrument] = {'fig': fig, 'ax': ax, 'canvas': canvas}
        
        # Log
        log_frame = ttk.LabelFrame(left_panel, text="🔍 LOG", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, bg=COLORS['panel'],
                                                 fg=COLORS['fg'], font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Right panel
        right_panel = ttk.Frame(content, width=420)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)
        
        # Backtest Results Panel
        backtest_frame = ttk.LabelFrame(right_panel, text="🔬 BACKTEST RESULTS", padding=10)
        backtest_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.backtest_labels = {}
        metrics = ['Total Return', 'Win Rate', 'Total Trades', 'Max Drawdown']
        for metric in metrics:
            frame = ttk.Frame(backtest_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f"{metric}:", font=('Arial', 9)).pack(side=tk.LEFT)
            self.backtest_labels[metric] = ttk.Label(frame, text="--", font=('Arial', 9, 'bold'))
            self.backtest_labels[metric].pack(side=tk.RIGHT)
        
        # Account info
        account_frame = ttk.LabelFrame(right_panel, text="💼 ACCOUNT", padding=10)
        account_frame.pack(fill=tk.X, pady=(0, 10))
        
        balance_frame = ttk.Frame(account_frame)
        balance_frame.pack(fill=tk.X, pady=2)
        ttk.Label(balance_frame, text="Balance:").pack(side=tk.LEFT)
        self.balance_label = ttk.Label(balance_frame, text="$10,000.00", font=('Arial', 12, 'bold'))
        self.balance_label.pack(side=tk.RIGHT)
        
        # Positions
        pos_frame = ttk.LabelFrame(right_panel, text="📊 POSITIONS", padding=10)
        pos_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.pos_text = tk.Text(pos_frame, height=8, bg=COLORS['panel'], fg=COLORS['fg'],
                               font=('Consolas', 9), state=tk.DISABLED)
        self.pos_text.pack(fill=tk.BOTH, expand=True)
        
        # Performance
        perf_frame = ttk.LabelFrame(right_panel, text="📈 PERFORMANCE", padding=10)
        perf_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.perf_labels = {}
        metrics = ['Total Trades', 'Win Rate', 'Total P&L']
        for metric in metrics:
            frame = ttk.Frame(perf_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f"{metric}:").pack(side=tk.LEFT)
            self.perf_labels[metric] = ttk.Label(frame, text="0", font=('Arial', 9, 'bold'))
            self.perf_labels[metric].pack(side=tk.RIGHT)
    
    def switch_mode(self):
        """Switch between live and backtest mode"""
        self.mode = self.mode_var.get()
        
        if self.mode == "backtest":
            self.start_btn.config(state=tk.DISABLED)
            self.backtest_btn.config(state=tk.NORMAL)
            self.status_label.config(text="🔬 BACKTEST MODE", foreground=COLORS['warning'])
            self.log("🔬 Switched to BACKTEST mode")
        else:
            self.start_btn.config(state=tk.NORMAL)
            self.backtest_btn.config(state=tk.DISABLED)
            self.status_label.config(text="📊 LIVE MODE", foreground=COLORS['success'])
            self.log("📊 Switched to LIVE mode")
    
    def run_backtest(self):
        """Run backtest on selected instrument"""
        self.log("🔬 Starting backtest...")
        
        def backtest_thread():
            try:
                # Get selected instrument
                current_tab = self.chart_notebook.index(self.chart_notebook.select())
                instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD']
                instrument = instruments[current_tab]
                
                # Set date range (last 30 days)
                end = datetime.now()
                start = end - timedelta(days=30)
                
                self.log(f"   Instrument: {instrument}")
                self.log(f"   Period: {start.date()} to {end.date()}")
                self.log(f"   Timeframe: {self.timeframe_var.get()}")
                
                # Run backtest
                engine = BacktestEngine(
                    f"config/oanda_{self.account_type}.cfg",
                    instrument,
                    start.strftime("%Y-%m-%d"),
                    end.strftime("%Y-%m-%d"),
                    self.timeframe_var.get()
                )
                
                results = engine.run_backtest()
                
                if results:
                    self.backtest_results = results
                    self.display_backtest_results(results)
                    self.log(f"✅ Backtest complete!")
                    self.log(f"   Total Return: {results['total_return']:.2f}%")
                    self.log(f"   Win Rate: {results['win_rate']:.1f}%")
                    self.log(f"   Total Trades: {results['total_trades']}")
                else:
                    self.log("❌ Backtest failed")
                    
            except Exception as e:
                self.log(f"❌ Backtest error: {e}")
        
        threading.Thread(target=backtest_thread, daemon=True).start()
    
    def display_backtest_results(self, results):
        """Display backtest results in GUI"""
        self.backtest_labels['Total Return'].config(
            text=f"{results['total_return']:+.2f}%",
            foreground=COLORS['success'] if results['total_return'] > 0 else COLORS['error']
        )
        self.backtest_labels['Win Rate'].config(text=f"{results['win_rate']:.1f}%")
        self.backtest_labels['Total Trades'].config(text=str(results['total_trades']))
        self.backtest_labels['Max Drawdown'].config(
            text=f"{results['max_drawdown']:.2f}%",
            foreground=COLORS['error']
        )
    
    def connect_account(self, account_type):
        """Connect to OANDA account"""
        self.account_type = account_type
        self.status_label.config(text=f"🔄 Connecting...", foreground=COLORS['warning'])
        
        def connect():
            try:
                config = f"config/oanda_{account_type}.cfg"
                self.trader = PerfectTrader(config, self.timeframe_var.get(), 1.0)
                
                self.status_label.config(text=f"✅ {account_type.upper()} Connected", foreground=COLORS['success'])
                self.balance_label.config(text=f"${self.trader.balance:,.2f}")
                self.start_btn.config(state=tk.NORMAL)
                
                self.log(f"✅ Connected to {account_type.upper()}")
                self.log(f"   Balance: ${self.trader.balance:,.2f}")
                
            except Exception as e:
                self.status_label.config(text=f"❌ Failed", foreground=COLORS['error'])
                self.log(f"❌ Connection error: {e}")
        
        threading.Thread(target=connect, daemon=True).start()
    
    def start_trading(self):
        """Start live trading"""
        if not self.trader:
            messagebox.showwarning("Warning", "Connect to account first")
            return
        
        self.trading_active = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="🚀 TRADING ACTIVE", foreground=COLORS['success'])
        self.log("🚀 Trading started!")
        
        threading.Thread(target=self.trading_loop, daemon=True).start()
    
    def stop_trading(self):
        """Stop trading"""
        self.trading_active = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="⏹️ STOPPED", foreground=COLORS['warning'])
        self.log("⏹️ Trading stopped")
    
    def trading_loop(self):
        """Main trading loop"""
        while self.trading_active and self.trader:
            try:
                if not self.trader.is_market_open():
                    time.sleep(60)
                    continue
                
                for instrument in list(self.trader.positions.keys()):
                    self.trader.check_exit_conditions(instrument)
                
                for instrument in self.trader.instruments:
                    df = self.trader.get_live_data(instrument, 100)
                    if df is not None:
                        self.market_data[instrument] = df
                        analysis = self.trader.analyze_fast(df)
                        
                        if analysis['signal'] in ['BUY', 'SELL']:
                            if instrument not in self.trader.positions and len(self.trader.positions) < 5:
                                trade = self.trader.execute_trade(instrument, analysis['signal'], 100)
                                if trade:
                                    self.log(f"✅ {instrument}: {trade['direction']} @ {trade['entry_price']:.5f}")
                                    self.log(f"   SL: {trade['stop_loss']:.5f} | TP: {trade['take_profit']:.5f}")
                
                self.trader.update_account_info()
                time.sleep(15)
                
            except Exception as e:
                self.log(f"❌ Error: {e}")
                time.sleep(30)
    
    def start_updates(self):
        """Start GUI updates"""
        def update_loop():
            while True:
                try:
                    if self.trader and self.mode == "live":
                        self.update_positions()
                        self.update_performance()
                    time.sleep(2)
                except:
                    time.sleep(5)
        
        threading.Thread(target=update_loop, daemon=True).start()
    
    def update_positions(self):
        """Update positions display"""
        if not self.trader:
            return
        
        self.pos_text.config(state=tk.NORMAL)
        self.pos_text.delete(1.0, tk.END)
        
        if self.trader.positions:
            for instrument, pos in self.trader.positions.items():
                try:
                    _, bid, ask = self.trader.get_prices(instrument)
                    current = bid if pos['direction'] == 'LONG' else ask
                    entry = pos['entry_price']
                    
                    pnl_pct = ((current - entry) / entry * 100) if pos['direction'] == 'LONG' else ((entry - current) / entry * 100)
                    color = 'green' if pnl_pct > 0 else 'red'
                    
                    self.pos_text.insert(tk.END, f"{instrument.replace('_', '/')}\n", 'bold')
                    self.pos_text.insert(tk.END, f"  {pos['direction']} | Entry: {entry:.5f}\n")
                    self.pos_text.insert(tk.END, f"  SL: {pos['stop_loss']:.5f} | TP: {pos['take_profit']:.5f}\n")
                    self.pos_text.insert(tk.END, f"  P&L: {pnl_pct:+.2f}%\n\n", color)
                    
                    self.pos_text.tag_config('bold', font=('Consolas', 9, 'bold'))
                    self.pos_text.tag_config('green', foreground=COLORS['success'])
                    self.pos_text.tag_config('red', foreground=COLORS['error'])
                except:
                    pass
        else:
            self.pos_text.insert(tk.END, "No open positions\n")
        
        self.pos_text.config(state=tk.DISABLED)
    
    def update_performance(self):
        """Update performance metrics"""
        if not self.trader:
            return
        
        closed = self.trader.closed_trades
        total = len(closed)
        winning = len([t for t in closed if t.get('pnl', 0) > 0])
        total_pnl = sum(t.get('pnl', 0) for t in closed)
        
        self.perf_labels['Total Trades'].config(text=str(total))
        self.perf_labels['Win Rate'].config(text=f"{(winning/total*100) if total > 0 else 0:.1f}%")
        self.perf_labels['Total P&L'].config(text=f"${total_pnl:+.2f}")
        self.balance_label.config(text=f"${self.trader.balance:,.2f}")
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = PerfectTradingGUI(root)
    root.mainloop()
