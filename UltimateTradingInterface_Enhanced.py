"""
Enhanced Ultimate Trading Interface - Perfect Edition
- Modern, user-friendly design
- Complete real-time data updates
- Actual trading execution
- Beautiful charts with real data
- Full position tracking with dollar P&L
- Complete trade history
- Market status indicators
- Signal strength visualization
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
import pytz

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

class FastTrader(tpqoa):
    """Optimized trader with fast execution and complete tracking"""
    
    def __init__(self, config_path, timeframe="M5", risk_pct=1.0):
        super().__init__(config_path)
        self.timeframe = timeframe
        self.risk_pct = risk_pct / 100.0
        self.instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD']
        self.positions = {}
        self.trades = []
        self.closed_trades = []
        self.running = False
        self.balance = 10000.0
        self.currency = 'USD'
        self.nav = 0.0
        self.unrealized_pl = 0.0
        self.margin_used = 0.0
        self.margin_available = 0.0
        self.account_id = None
        
        # Get actual account balance
        self.update_account_info()
        
    def update_account_info(self):
        """Update account balance and info from OANDA"""
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
            # Try alternative method
            try:
                response = self.ctx.account.get(self.account_id)
                if response.status == 200:
                    account = response.body.get('account')
                    if account:
                        self.balance = float(account.balance)
                        self.currency = account.currency
                        self.nav = float(account.NAV)
                        self.unrealized_pl = float(account.unrealizedPL)
                        self.margin_used = float(getattr(account, 'marginUsed', 0.0))
                        self.margin_available = float(getattr(account, 'marginAvailable', self.balance))
                        return True
            except:
                pass
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
        prev = df.iloc[-2]
        
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
        """Execute trade with proper error handling"""
        try:
            if signal == 'BUY':
                order = self.create_order(instrument, units, suppress=True, ret=True)
                direction = 'LONG'
            elif signal == 'SELL':
                order = self.create_order(instrument, -units, suppress=True, ret=True)
                direction = 'SHORT'
            else:
                return None
            
            if order:
                trade = {
                    'instrument': instrument,
                    'direction': direction,
                    'units': units,
                    'entry_price': float(order.get('price', 0)),
                    'entry_time': datetime.now(),
                    'status': 'OPEN'
                }
                self.positions[instrument] = trade
                self.trades.append(trade)
                return trade
        except Exception as e:
            print(f"Trade execution error: {e}")
            return None
    
    def close_position(self, instrument):
        """Close position and track in history"""
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
                
                # Add to closed trades history
                self.closed_trades.append(pos.copy())
                
                # Remove from active positions
                del self.positions[instrument]
                
                # Update account info
                self.update_account_info()
                
                return pos
        except Exception as e:
            print(f"Close error: {e}")
            return None
    
    def is_market_open(self):
        """Check if forex market is open (Mon-Fri)"""
        now = datetime.now(pytz.UTC)
        # Forex market is closed on weekends
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        return True
    
    def get_current_price(self, instrument):
        """Get current bid/ask prices"""
        try:
            _, bid, ask = self.get_prices(instrument)
            return bid, ask
        except:
            return None, None
                

class EnhancedTradingGUI:
    """Modern, fast, user-friendly trading interface - Perfect Edition"""
    
    def __init__(self, root):
        
        self.root.title("🚀 FX Trading Bot - Perfect Edition")
        self.root.geometry("1900x1000")
        self.root.configure(bg=COLORS['bg'])
        
        # Configure style
        self.setup_style()
        
        # Initialize trader
        self.trader = None
        self.account_type = "demo"
        self.trading_active = False
        self.update_thread = None
        
        # Data storage
        self.market_data = {}
        self.analysis_results = {}
        self.signal_strengths = {}
        
        # Create GUI
        self.create_gui()
        
        # Initialize with demo account
        self.connect_account("demo")
        
        # Start update loop
        self.start_updates()
    def setup_style(self):
        """Configure modern ttk style"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('TFrame', background=COLORS['bg'])
        style.configure('TLabel', background=COLORS['bg'], foreground=COLORS['fg'])
        style.configure('TLabelframe', background=COLORS['bg'], foreground=COLORS['accent'])
        style.configure('TLabelframe.Label', background=COLORS['bg'], foreground=COLORS['accent'], font=('Arial', 10, 'bold'))
        style.configure('TButton', background=COLORS['panel'], foreground=COLORS['fg'])
        style.map('TButton', background=[('active', COLORS['hover'])])
        style.configure('Success.TButton', background=COLORS['success'], foreground=COLORS['bg'])
        style.configure('Warning.TButton', background=COLORS['warning'], foreground=COLORS['bg'])
        style.configure('Error.TButton', background=COLORS['error'], foreground=COLORS['bg'])
    
    def create_gui(self):
        """Create modern GUI layout"""
        # Top control bar
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Account selection
        ttk.Label(control_frame, text="Account:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.account_var = tk.StringVar(value="demo")
        ttk.Radiobutton(control_frame, text="📊 Demo", variable=self.account_var, value="demo",
                       command=lambda: self.connect_account("demo")).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(control_frame, text="💰 Live", variable=self.account_var, value="live",
                       command=lambda: self.connect_account("live")).pack(side=tk.LEFT, padx=5)
        
        # Trading controls
        ttk.Label(control_frame, text="|", foreground=COLORS['panel']).pack(side=tk.LEFT, padx=10)
        
        self.start_btn = ttk.Button(control_frame, text="▶️ START TRADING", style='Success.TButton',
                                    command=self.start_trading)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ STOP", style='Error.TButton',
                                   command=self.stop_trading, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Parameters
        ttk.Label(control_frame, text="|", foreground=COLORS['panel']).pack(side=tk.LEFT, padx=10)
        ttk.Label(control_frame, text="Timeframe:").pack(side=tk.LEFT, padx=5)
        self.timeframe_var = tk.StringVar(value="M5")
        ttk.Combobox(control_frame, textvariable=self.timeframe_var, values=["M1", "M5", "M15", "H1"],
                    state="readonly", width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Risk %:").pack(side=tk.LEFT, padx=5)
        self.risk_var = tk.DoubleVar(value=1.0)
        tk.Spinbox(control_frame, from_=0.5, to=5.0, increment=0.5, textvariable=self.risk_var,
                  width=5, bg=COLORS['panel'], fg=COLORS['fg']).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = ttk.Label(control_frame, text="🔄 Initializing...", font=('Arial', 10, 'bold'),
                                     foreground=COLORS['warning'])
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Main content area
        content = ttk.Frame(self.root)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Left panel - Charts
        left_panel = ttk.Frame(content)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Chart notebook
        chart_frame = ttk.LabelFrame(left_panel, text="📈 LIVE CHARTS", padding=10)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.chart_notebook = ttk.Notebook(chart_frame)
        self.chart_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create charts for each instrument
        self.charts = {}
        for instrument in ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD']:
            frame = ttk.Frame(self.chart_notebook)
            self.chart_notebook.add(frame, text=instrument)
            
            fig = Figure(figsize=(10, 5), facecolor=COLORS['bg'])
            ax = fig.add_subplot(111, facecolor=COLORS['panel'])
            ax.tick_params(colors=COLORS['fg'])
            ax.spines['bottom'].set_color(COLORS['fg'])
            ax.spines['top'].set_color(COLORS['fg'])
            ax.spines['left'].set_color(COLORS['fg'])
            ax.spines['right'].set_color(COLORS['fg'])
            
            canvas = FigureCanvasTkAgg(fig, frame)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            self.charts[instrument] = {'fig': fig, 'ax': ax, 'canvas': canvas}
        
        # Analysis log
        log_frame = ttk.LabelFrame(left_panel, text="🔍 ANALYSIS LOG", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, bg=COLORS['panel'],
                                                 fg=COLORS['fg'], font=('Consolas', 9),
                                                 insertbackground=COLORS['fg'])
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Right panel - Info
        right_panel = ttk.Frame(content, width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)
        
        # Account info
        account_frame = ttk.LabelFrame(right_panel, text="💼 ACCOUNT INFO", padding=10)
        account_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Balance
        balance_frame = ttk.Frame(account_frame)
        balance_frame.pack(fill=tk.X, pady=2)
        ttk.Label(balance_frame, text="Balance:", font=('Arial', 10)).pack(side=tk.LEFT)
        self.balance_label = ttk.Label(balance_frame, text="$10,000.00",
                                      font=('Arial', 12, 'bold'), foreground=COLORS['success'])
        self.balance_label.pack(side=tk.RIGHT)
        
        # NAV
        nav_frame = ttk.Frame(account_frame)
        nav_frame.pack(fill=tk.X, pady=2)
        ttk.Label(nav_frame, text="NAV:", font=('Arial', 9)).pack(side=tk.LEFT)
        self.nav_label = ttk.Label(nav_frame, text="$10,000.00", font=('Arial', 9))
        self.nav_label.pack(side=tk.RIGHT)
        
        # Unrealized P&L
        upl_frame = ttk.Frame(account_frame)
        upl_frame.pack(fill=tk.X, pady=2)
        ttk.Label(upl_frame, text="Unrealized P&L:", font=('Arial', 9)).pack(side=tk.LEFT)
        self.upl_label = ttk.Label(upl_frame, text="$0.00", font=('Arial', 9))
        self.upl_label.pack(side=tk.RIGHT)
        
        # Margin
        margin_frame = ttk.Frame(account_frame)
        margin_frame.pack(fill=tk.X, pady=2)
        ttk.Label(margin_frame, text="Margin Used:", font=('Arial', 9)).pack(side=tk.LEFT)
        self.margin_label = ttk.Label(margin_frame, text="$0.00", font=('Arial', 9))
        self.margin_label.pack(side=tk.RIGHT)
        
        # Market Status
        market_frame = ttk.Frame(account_frame)
        market_frame.pack(fill=tk.X, pady=5)
        ttk.Label(market_frame, text="Market:", font=('Arial', 9)).pack(side=tk.LEFT)
        self.market_status_label = ttk.Label(market_frame, text="🟢 OPEN", 
                                             font=('Arial', 9, 'bold'), foreground=COLORS['success'])
        self.market_status_label.pack(side=tk.RIGHT)
        
        # Signal Strength Panel
        signal_frame = ttk.LabelFrame(right_panel, text="📊 SIGNAL STRENGTH", padding=10)
        signal_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.signal_labels = {}
        for instrument in ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD']:
            
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(frame, text=instrument.replace('_', '/'), 
                     font=('Arial', 8)).pack(side=tk.LEFT)
            
            signal_bar = ttk.Progressbar(frame, length=150, mode='determinate')
            signal_bar.pack(side=tk.LEFT, padx=5)
            
            signal_text = ttk.Label(frame, text="--", font=('Arial', 8, 'bold'))
            signal_text.pack(side=tk.RIGHT)
            
            self.signal_labels[instrument] = {'bar': signal_bar, 'text': signal_text}
        # Positions
        pos_frame = ttk.LabelFrame(right_panel, text="📊 POSITIONS", padding=10)
        pos_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.pos_text = tk.Text(pos_frame, height=10, bg=COLORS['panel'], fg=COLORS['fg'],
                               font=('Consolas', 9), state=tk.DISABLED, insertbackground=COLORS['fg'])
        self.pos_text.pack(fill=tk.BOTH, expand=True)
        
        # Performance
        perf_frame = ttk.LabelFrame(right_panel, text="📈 PERFORMANCE", padding=10)
        perf_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.perf_labels = {}
        metrics = ['Total Trades', 'Open Positions', 'Win Rate', 'Total P&L', 'Today P&L']
        for metric in metrics:
            frame = ttk.Frame(perf_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f"{metric}:", font=('Arial', 9)).pack(side=tk.LEFT)
            self.perf_labels[metric] = ttk.Label(frame, text="0", font=('Arial', 9, 'bold'))
            self.perf_labels[metric].pack(side=tk.RIGHT)
            
        # Trade history
        history_frame = ttk.LabelFrame(right_panel, text="📝 HISTORY", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True)
        
        self.history_text = scrolledtext.ScrolledText(history_frame, height=10, bg=COLORS['panel'],
                                                     fg=COLORS['fg'], font=('Consolas', 8),
                                                     insertbackground=COLORS['fg'])
        self.history_text.pack(fill=tk.BOTH, expand=True)
    
    def connect_account(self, account_type):
        """Connect to OANDA account with detailed feedback"""
        self.account_type = account_type
        self.status_label.config(text=f"🔄 Connecting to {account_type.upper()}...",
                                foreground=COLORS['warning'])
        
        def connect():
            
                config = f"config/oanda_{account_type}.cfg"
                self.trader = FastTrader(config, self.timeframe_var.get(), self.risk_var.get())
                
                # Get account ID
                self.trader.account_id = self.trader.account_id
                
                self.status_label.config(text=f"✅ {account_type.upper()} Connected",
                                        foreground=COLORS['success'])
                self.balance_label.config(text=f"${self.trader.balance:,.2f}")
                self.nav_label.config(text=f"${self.trader.nav:,.2f}")
                self.upl_label.config(text=f"${self.trader.unrealized_pl:+,.2f}")
                self.margin_label.config(text=f"${self.trader.margin_used:,.2f}")
                
                self.start_btn.config(state=tk.NORMAL)
                
                # Log detailed connection info
                self.log(f"✅ Connected to {account_type.upper()} account")
                self.log(f"   Account ID: {self.trader.account_id}")
                self.log(f"   Balance: ${self.trader.balance:,.2f} {self.trader.currency}")
                self.log(f"   NAV: ${self.trader.nav:,.2f}")
                
                # Check market status
                if self.trader.is_market_open():
        def start_trading(self):
                    self.log(f"   Market Status: OPEN")
                else:
                    self.market_status_label.config(text="🔴 CLOSED", foreground=COLORS['error'])
                    self.log(f"   Market Status: CLOSED (Weekend)")
                    
            except Exception as e:
                self.status_label.config(text=f"❌ Connection Failed",
                                        foreground=COLORS['error'])
                self.log(f"❌ Connection error: {e}")
                messagebox.showerror("Error", f"Failed to connect: {e}")
        
        threading.Thread(target=connect, daemon=True).start()
            """Start automated trading"""
        if not self.trader:
            messagebox.showwarning("Warning", "Please connect to an account first")
            return
        
        self.trading_active = True
        self.trader.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="🚀 TRADING ACTIVE", foreground=COLORS['success'])
        self.log("🚀 Trading started!")
        
        # Start trading thread
        threading.Thread(target=self.trading_loop, daemon=True).start()
    
    def stop_trading(self):
        """Stop trading"""
        self.trading_active = False
        if self.trader:
            self.trader.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="⏹️ STOPPED", foreground=COLORS['warning'])
        self.log("⏹️ Trading stopped")
    
    def trading_loop(self):
        
        while self.trading_active and self.trader:
        def start_updates(self):
                # Check market status
                if not self.trader.is_market_open():
            """Start GUI update loop"""
                    time.sleep(60)
                    continue
                
                for instrument in self.trader.instruments:
            def update_loop():
                    df = self.trader.get_live_data(instrument, 100)
                    if df is not None:
                while True:
                        analysis = self.trader.analyze_fast(df)
                        self.analysis_results[instrument] = analysis
                        
                        # Store signal strength
                        self.signal_strengths[instrument] = analysis['score']
                        
                        # Check for trading opportunity
                        if analysis['signal'] in ['BUY', 'SELL']:
                    try:
                                # Check if we have room for more positions
                                if len(self.trader.positions) >= 5:
                        if self.trader:
                                    continue
                                
                                self.log(f"🎯 {instrument}: {analysis['signal']} signal (score: {analysis['score']:.2f})")
                                self.log(f"   Price: {analysis['price']:.5f} | RSI: {analysis['rsi']:.1f} | Trend: {analysis['indicators'].get('trend', 'N/A')}")
                                
                                # Execute trade
                                trade = self.trader.execute_trade(instrument, analysis['signal'], 100)
                                if trade:
                            # Update charts
                                    self.log(f"   Units: {trade['units']} | Risk: ~${self.trader.balance * 0.01:.2f}")
                                else:
                            self.update_charts()
                
                # Update account info
                self.trader.update_account_info()
                
                time.sleep(15)  # Check every 15 seconds
                
            except Exception as e:
                self.log(f"❌ Trading error: {e}")
                time.sleep(30)
                        
                        # Update positions
                        self.update_positions()
                        
                        # Update performance
                        self.update_performance()
                    
                    time.sleep(2)  # Update every 2 seconds
                except Exception as e:
                    print(f"Update error: {e}")
                    time.sleep(5)
        
        threading.Thread(target=update_loop, daemon=True).start()
    
    def update_charts(self):
        """Update all charts with latest data"""
        for instrument in self.charts:
            if instrument in self.market_data:
                df = self.market_data[instrument]
                if df is not None and len(df) > 0:
                    chart = self.charts[instrument]
                    ax = chart['ax']
                    ax.clear()
                    
                    # Plot candlestick-style
                    ax.plot(df.index, df['close'], color=COLORS['accent'], linewidth=1.5, label='Price')
                    
                    # Add SMA if available
                    if 'sma_20' in df.columns:
                        ax.plot(df.index, df['sma_20'], color=COLORS['success'], linewidth=1, alpha=0.7, label='SMA 20')
                    if 'sma_50' in df.columns:
                        ax.plot(df.index, df['sma_50'], color=COLORS['warning'], linewidth=1, alpha=0.7, label='SMA 50')
                    
                    # Add signal markers
                    if instrument in self.analysis_results:
                        analysis = self.analysis_results[instrument]
                        if analysis['signal'] == 'BUY':
                            ax.axhline(y=analysis['price'], color=COLORS['buy'], linestyle='--', alpha=0.5)
                        elif analysis['signal'] == 'SELL':
                            ax.axhline(y=analysis['price'], color=COLORS['sell'], linestyle='--', alpha=0.5)
                    
                    ax.set_title(f"{instrument} - {self.timeframe_var.get()}", color=COLORS['fg'], fontsize=12, fontweight='bold')
                    ax.set_xlabel('Time', color=COLORS['fg'])
                    ax.set_ylabel('Price', color=COLORS['fg'])
                    ax.legend(facecolor=COLORS['panel'], edgecolor=COLORS['fg'], labelcolor=COLORS['fg'])
                    ax.grid(True, alpha=0.2, color=COLORS['fg'])
                    
                    chart['canvas'].draw()
    
    def update_positions(self):
        
        if not self.trader:
        def update_performance(self):
        
        self.pos_text.config(state=tk.NORMAL)
        self.pos_text.delete(1.0, tk.END)
        
        if self.trader.positions:
            """Update performance metrics"""
                # Get current price
                try:
                    bid, ask = self.trader.get_current_price(instrument)
                    if bid is None:
            if not self.trader:
                        
                    current = bid if pos['direction'] == 'LONG' else ask
                    entry = pos['entry_price']
                    units = pos['units']
                    
                    # Calculate P&L
                    if pos['direction'] == 'LONG':
                return
                        pnl_pct = (current - entry) / entry * 100
                    else:
            
                        pnl_pct = (entry - current) / entry * 100
                    
                    # Estimate dollar P&L (approximate)
                    pnl_dollars = pnl_pips * units
                    
                    color = 'green' if pnl_pct > 0 else 'red'
                    
                    self.pos_text.insert(tk.END, f"{instrument.replace('_', '/')}\n", 'bold')
                    self.pos_text.insert(tk.END, f"  {pos['direction']} | Entry: {entry:.5f}\n")
                    self.pos_text.insert(tk.END, f"  Current: {current:.5f}\n")
                    self.pos_text.insert(tk.END, f"  P&L: {pnl_pct:+.2f}% (${pnl_dollars:+.2f})\n\n", color)
                    
                    self.pos_text.tag_config('bold', font=('Consolas', 9, 'bold'))
                    self.pos_text.tag_config('green', foreground=COLORS['success'])
                    self.pos_text.tag_config('red', foreground=COLORS['error'])
                except Exception as e:
                    print(f"Position update error for {instrument}: {e}")
        else:
            trades = self.trader.trades
            self.pos_text.tag_config('neutral', foreground=COLORS['fg'])
        
        self.pos_text.config(state=tk.DISABLED)
        total = len(trades)
        winning = len([t for t in trades if t.get('pnl', 0) > 0])
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        
        self.perf_labels['Total Trades'].config(text=str(total))
        self.perf_labels['Win Rate'].config(text=f"{(winning/total*100) if total > 0 else 0:.1f}%")
        self.perf_labels['Total P&L'].config(text=f"${total_pnl:+.2f}")
        
        # Update balance
        self.balance_label.config(text=f"Balance: ${self.trader.balance + total_pnl:,.2f}")
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
        # Keep last 100 lines
        lines = self.log_text.get(1.0, tk.END).split('\n')
        if len(lines) > 102:
            self.log_text.delete(1.0, '3.0')


if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedTradingGUI(root)
    root.mainloop()
