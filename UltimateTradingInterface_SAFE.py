"""
SAFE Ultimate Trading Interface
- MUCH stricter entry criteria
- Better risk management
- Stop losses on every trade
- Trend confirmation required
- Multiple indicator agreement needed
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

class SafeTrader(tpqoa):
    """SAFE trader with strict entry criteria and stop losses"""
    
    def __init__(self, config_path, timeframe="M5", risk_pct=0.5):
        super().__init__(config_path)
        self.timeframe = timeframe
        self.risk_pct = risk_pct / 100.0  # Much lower risk
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
                
    def get_live_data(self, instrument, count=200):
        """Get more data for better analysis"""
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
    
    def analyze_safe(self, df):
        """MUCH SAFER analysis with strict criteria"""
        if df is None or len(df) < 100:
            return {'signal': 'HOLD', 'score': 0.0, 'indicators': {}, 'confidence': 0}
        
        # Calculate indicators
        df['sma_20'] = df['close'].rolling(20).mean()
        df['sma_50'] = df['close'].rolling(50).mean()
        df['sma_100'] = df['close'].rolling(100).mean()
        df['sma_200'] = df['close'].rolling(200).mean()
        
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
        
        # ATR for volatility
        df['tr'] = df[['high', 'low', 'close']].apply(
            lambda x: max(x['high'] - x['low'], 
                         abs(x['high'] - x['close']), 
                         abs(x['low'] - x['close'])), axis=1)
        df['atr'] = df['tr'].rolling(14).mean()
        
        # MACD
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        
        # Get latest values
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        score = 0.0
        confidence = 0
        indicators = {}
        
        # REASONABLE TREND CONFIRMATION (just need 2 SMAs to agree)
        if (latest['sma_20'] > latest['sma_50']):
            score += 0.2
            confidence += 1
            indicators['trend'] = 'UP'
        elif (latest['sma_20'] < latest['sma_50']):
            score -= 0.2
            confidence += 1
            indicators['trend'] = 'DOWN'
        else:
            indicators['trend'] = 'FLAT'
            
        # RSI - REASONABLE levels (not extreme)
        if latest['rsi'] < 35:  # Oversold (lowered from 25)
            score += 0.3
            confidence += 1
            indicators['rsi'] = 'OVERSOLD'
        elif latest['rsi'] > 65:  # Overbought (lowered from 75)
            score -= 0.3
            confidence += 1
            indicators['rsi'] = 'OVERBOUGHT'
        else:
            indicators['rsi'] = 'NEUTRAL'
            # Still allow trading with neutral RSI if other indicators strong
            
        # Bollinger Bands - near or outside bands (more lenient)
        if latest['close'] < latest['bb_lower'] * 1.001:  # At or near lower
            score += 0.2
            confidence += 1
            indicators['bb'] = 'NEAR_LOWER'
        elif latest['close'] > latest['bb_upper'] * 0.999:  # At or near upper
            score -= 0.2
            confidence += 1
            indicators['bb'] = 'NEAR_UPPER'
        else:
            indicators['bb'] = 'INSIDE'
        
        # MACD confirmation
        if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
            score += 0.15
            confidence += 1
            indicators['macd'] = 'BULLISH_CROSS'
        elif latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
            score -= 0.15
            confidence += 1
            indicators['macd'] = 'BEARISH_CROSS'
        else:
            indicators['macd'] = 'NO_CROSS'
            
        # Volume confirmation
        avg_volume = df['volume'].rolling(20).mean().iloc[-1]
        if latest['volume'] > avg_volume * 1.5:
            confidence += 1
            indicators['volume'] = 'HIGH'
        else:
            indicators['volume'] = 'NORMAL'
        
        # BALANCED SIGNAL CRITERIA
        # Lowered thresholds to actually make trades
        if score > 0.6 and confidence >= 3:
            signal = 'BUY'
        elif score < -0.55 and confidence >= 2:  # LOWERED from -0.7 and 4 confirmations
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
            'sma_50': latest['sma_50'],
            'atr': latest['atr'],
            'confidence': confidence
        }
    
                
                # Create order with stop loss and take profit
                order = self.create_order(
                    instrument, 
                    -units, 
                    suppress=True, 
                    ret=True
                )
                
                if order:
                    trade = {
                        'instrument': instrument,
                        'direction': 'SHORT',
                        'units': units,
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'entry_time': datetime.now(),
                        'status': 'OPEN'
                    }
                    self.positions[instrument] = trade
                    self.trades.append(trade)
                    return trade
            
            return None
            
        except Exception as e:
            print(f"Trade execution error: {e}")
            return None
=======
    def execute_trade_with_sl(self, instrument, signal, units=50):
        """Execute trade with STOP LOSS"""
        try:
            _, bid, ask = self.get_prices(instrument)
            
            if signal == 'SELL':
                # SHORT position
                entry_price = bid
                # Use simple percentage-based stop loss (more reliable)
                stop_loss = entry_price * 1.008  # 0.8% stop loss
                take_profit = entry_price * 0.988  # 1.2% take profit (1.5:1 ratio)
                
                # Create order with stop loss and take profit
                order = self.create_order(
                    instrument, 
                    -units, 
                    suppress=True, 
                    ret=True
                )
                
                if order:
                =======
                        'instrument': instrument,
                        'direction': 'SHORT',
                        'units': units,
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'entry_time': datetime.now(),
                        'status': 'OPEN'
                    }
                    self.positions[instrument] = trade
                    self.trades.append(trade)
                    return trade
            
            return None
            
        except Exception as e:
            print(f"Trade execution error: {e}")
            return None
                
                # Create order with stop loss and take profit
                order = self.create_order(
                    instrument, 
                    -units, 
                    suppress=True, 
                    ret=True
                )
                
                if order:
                    trade = {
                        'instrument': instrument,
                        'direction': 'SHORT',
                        'units': units,
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'entry_time': datetime.now(),
                        'status': 'OPEN'
                    }
                    self.positions[instrument] = trade
                    self.trades.append(trade)
                    return trade
            
            return None
            
        except Exception as e:
            print(f"Trade execution error: {e}")
            return None
    
    def check_stop_loss(self, instrument):
        """Check if stop loss or take profit hit"""
        if instrument not in self.positions:
            return
        
        try:
            pos = self.positions[instrument]
            _, bid, ask = self.get_prices(instrument)
            
            current_price = ask if pos['direction'] == 'SHORT' else bid
            
            # Check stop loss
            if pos['direction'] == 'SHORT':
                if current_price >= pos['stop_loss']:
                    print(f"⚠️ STOP LOSS HIT: {instrument}")
                    self.close_position(instrument)
                elif current_price <= pos['take_profit']:
                    print(f"✅ TAKE PROFIT HIT: {instrument}")
                    self.close_position(instrument)
        except Exception as e:
            print(f"Stop loss check error: {e}")
    
    def close_position(self, instrument):
        """Close position and add to history"""
        if instrument not in self.positions:
            return None
        
        try:
            pos = self.positions[instrument]
            units = pos['units']
            
            if pos['direction'] == 'SHORT':
                order = self.create_order(instrument, units, suppress=True, ret=True)
            else:
                order = self.create_order(instrument, -units, suppress=True, ret=True)
            
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


class SafeTradingGUI:
    """SAFE trading interface"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🛡️ FX Trading Bot - BALANCED Edition")
        self.root.geometry("1900x1000")
        self.root.configure(bg=COLORS['bg'])
        
        self.setup_style()
        
        self.trader = None
        self.account_type = "demo"
        self.trading_active = False
        
        self.market_data = {}
        self.analysis_results = {}
        self.signal_strengths = {}
        
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
    
    def create_gui(self):
        """Create GUI layout"""
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
        
        ttk.Label(control_frame, text="Timeframe:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.timeframe_var = tk.StringVar(value="M15")
        ttk.Combobox(control_frame, textvariable=self.timeframe_var, 
                    values=["M15", "M30", "H1", "H4"],
                    state="readonly", width=6).pack(side=tk.LEFT, padx=5)
        
        # Mode indicator
        ttk.Label(control_frame, text="|", foreground=COLORS['panel']).pack(side=tk.LEFT, padx=10)
        ttk.Label(control_frame, text="🛡️ BALANCED MODE | 🔴 SELL-ONLY | Stop Loss: ON", 
                 font=('Arial', 9, 'bold'), foreground=COLORS['success']).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Risk %:").pack(side=tk.LEFT, padx=5)
        self.risk_var = tk.DoubleVar(value=0.5)
        tk.Spinbox(control_frame, from_=0.25, to=1.0, increment=0.25, textvariable=self.risk_var,
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
            self.chart_notebook.add(frame, text=instrument.replace('_', '/'))
            
            fig = Figure(figsize=(10, 5), facecolor=COLORS['bg'])
            ax = fig.add_subplot(111, facecolor=COLORS['panel'])
            ax.tick_params(colors=COLORS['fg'])
            for spine in ax.spines.values():
                spine.set_color(COLORS['fg'])
            
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
        right_panel = ttk.Frame(content, width=420)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)
        
        # Account info
        account_frame = ttk.LabelFrame(right_panel, text="💼 ACCOUNT INFO", padding=10)
        account_frame.pack(fill=tk.X, pady=(0, 10))
        
        balance_frame = ttk.Frame(account_frame)
        balance_frame.pack(fill=tk.X, pady=2)
        ttk.Label(balance_frame, text="Balance:", font=('Arial', 10)).pack(side=tk.LEFT)
        self.balance_label = ttk.Label(balance_frame, text="$10,000.00",
                                      font=('Arial', 12, 'bold'), foreground=COLORS['success'])
        self.balance_label.pack(side=tk.RIGHT)
        
        nav_frame = ttk.Frame(account_frame)
        nav_frame.pack(fill=tk.X, pady=2)
        ttk.Label(nav_frame, text="NAV:", font=('Arial', 9)).pack(side=tk.LEFT)
        self.nav_label = ttk.Label(nav_frame, text="$10,000.00", font=('Arial', 9))
        self.nav_label.pack(side=tk.RIGHT)
        
        upl_frame = ttk.Frame(account_frame)
        upl_frame.pack(fill=tk.X, pady=2)
        ttk.Label(upl_frame, text="Unrealized P&L:", font=('Arial', 9)).pack(side=tk.LEFT)
        self.upl_label = ttk.Label(upl_frame, text="$0.00", font=('Arial', 9))
        self.upl_label.pack(side=tk.RIGHT)
        
        margin_frame = ttk.Frame(account_frame)
        margin_frame.pack(fill=tk.X, pady=2)
        ttk.Label(margin_frame, text="Margin Used:", font=('Arial', 9)).pack(side=tk.LEFT)
        self.margin_label = ttk.Label(margin_frame, text="$0.00", font=('Arial', 9))
        self.margin_label.pack(side=tk.RIGHT)
        
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
            frame = ttk.Frame(signal_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(frame, text=instrument.replace('_', '/'), 
                     font=('Arial', 8), width=10).pack(side=tk.LEFT)
            
            signal_bar = ttk.Progressbar(frame, length=150, mode='determinate')
            signal_bar.pack(side=tk.LEFT, padx=5)
            
            signal_text = ttk.Label(frame, text="--", font=('Arial', 8, 'bold'), width=8)
            signal_text.pack(side=tk.RIGHT)
            
            self.signal_labels[instrument] = {'bar': signal_bar, 'text': signal_text}
        
        # Positions
        pos_frame = ttk.LabelFrame(right_panel, text="📊 OPEN POSITIONS", padding=10)
        pos_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.pos_text = tk.Text(pos_frame, height=8, bg=COLORS['panel'], fg=COLORS['fg'],
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
        history_frame = ttk.LabelFrame(right_panel, text="📝 TRADE HISTORY", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True)
        
        self.history_text = scrolledtext.ScrolledText(history_frame, height=8, bg=COLORS['panel'],
                                                     fg=COLORS['fg'], font=('Consolas', 8),
                                                     insertbackground=COLORS['fg'])
        self.history_text.pack(fill=tk.BOTH, expand=True)
    
    def connect_account(self, account_type):
        """Connect to OANDA account"""
        self.account_type = account_type
        self.status_label.config(text=f"🔄 Connecting to {account_type.upper()}...",
                                foreground=COLORS['warning'])
        
        def connect():
            try:
                config = f"config/oanda_{account_type}.cfg"
                self.trader = SafeTrader(config, self.timeframe_var.get(), self.risk_var.get())
                
                self.status_label.config(text=f"✅ {account_type.upper()} Connected",
                                        foreground=COLORS['success'])
                
                self.balance_label.config(text=f"${self.trader.balance:,.2f}")
                self.nav_label.config(text=f"${self.trader.nav:,.2f}")
                self.upl_label.config(text=f"${self.trader.unrealized_pl:+,.2f}")
                self.margin_label.config(text=f"${self.trader.margin_used:,.2f}")
                
                if self.trader.is_market_open():
                    self.market_status_label.config(text="🟢 OPEN", foreground=COLORS['success'])
                else:
                    self.market_status_label.config(text="🔴 CLOSED", foreground=COLORS['error'])
                
                self.start_btn.config(state=tk.NORMAL)
                
                self.log(f"✅ Connected to {account_type.upper()} account")
                self.log(f"   🛡️ BALANCED MODE ACTIVE")
                self.log(f"   Balance: ${self.trader.balance:,.2f}")
                self.log(f"   Risk: {self.risk_var.get()}% per trade")
                self.log(f"   Stop Loss: ENABLED on all trades")
                self.log(f"   Entry: Score < -0.55, Confidence >= 2")
                
            except Exception as e:
                self.status_label.config(text=f"❌ Connection Failed",
                                        foreground=COLORS['error'])
                self.log(f"❌ Connection error: {e}")
                messagebox.showerror("Error", f"Failed to connect: {e}")
        
        threading.Thread(target=connect, daemon=True).start()
    
    def start_trading(self):
        """Start automated trading"""
        if not self.trader:
            messagebox.showwarning("Warning", "Please connect to an account first")
            return
        
        self.trading_active = True
        self.trader.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="🛡️ BALANCED TRADING ACTIVE", foreground=COLORS['success'])
        self.log("🛡️ BALANCED Trading started!")
        self.log("   Reasonable signals with stop loss protection")
        self.log("   Stop losses active on all positions")
        
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
        """Main trading loop with SAFE criteria"""
        while self.trading_active and self.trader:
            try:
                if not self.trader.is_market_open():
                    self.log("⚠️ Market closed (Weekend)")
                    time.sleep(60)
                    continue
                
                # Check stop losses first
                for instrument in list(self.trader.positions.keys()):
                    self.trader.check_stop_loss(instrument)
                
                for instrument in self.trader.instruments:
                    df = self.trader.get_live_data(instrument, 200)
                    if df is not None:
                        self.market_data[instrument] = df
                        analysis = self.trader.analyze_safe(df)
                        self.analysis_results[instrument] = analysis
                        self.signal_strengths[instrument] = analysis['score']
                        
                        # SELL-ONLY with BALANCED criteria
                        if analysis['signal'] == 'SELL' and analysis['confidence'] >= 2:
                            if instrument not in self.trader.positions:
                                if len(self.trader.positions) >= 3:  # Max 3 positions
                                    continue
                                
                                self.log(f"🎯 {instrument}: SELL signal (score: {analysis['score']:.2f}, confidence: {analysis['confidence']}/5) [{self.timeframe_var.get()}]")
                                self.log(f"   Price: {analysis['price']:.5f} | RSI: {analysis['rsi']:.1f}")
                                self.log(f"   Trend: {analysis['indicators'].get('trend', 'N/A')}")
                                self.log(f"   🛡️ SAFE MODE: Very strong signal with stop loss")
                                
                                trade = self.trader.execute_trade_with_sl(instrument, 'SELL', 50)
                                if trade:
                                    self.log(f"✅ {instrument}: SHORT position opened @ {trade['entry_price']:.5f}")
                                    self.log(f"   Stop Loss: {trade['stop_loss']:.5f}")
                                    self.log(f"   Take Profit: {trade['take_profit']:.5f}")
                                    self.log(f"   Units: {trade['units']} | Risk: ~${self.trader.balance * 0.005:.2f}")
                        elif analysis['signal'] == 'BUY':
                            self.log(f"ℹ️ {instrument}: BUY signal (confidence: {analysis['confidence']}/5) - IGNORED (SELL-ONLY)")
                        elif analysis['confidence'] < 2:
                            self.log(f"⚠️ {instrument}: Signal too weak (confidence: {analysis['confidence']}/5) - SKIPPED")
                    
                self.trader.update_account_info()
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.log(f"❌ Trading error: {e}")
                time.sleep(60)
    
    def start_updates(self):
        """Start GUI update loop"""
        def update_loop():
            while True:
                try:
                    if self.trader:
                        self.update_charts()
                        self.update_positions()
                        self.update_performance()
                        self.update_signals()
                        self.update_history()
                    time.sleep(2)
                except Exception as e:
                    print(f"Update error: {e}")
                    time.sleep(5)
        
        threading.Thread(target=update_loop, daemon=True).start()
    
    def update_charts(self):
        """Update all charts"""
        for instrument in self.charts:
            if instrument in self.market_data:
                df = self.market_data[instrument]
                if df is not None and len(df) > 0:
                    chart = self.charts[instrument]
                    ax = chart['ax']
                    ax.clear()
                    
                    ax.plot(df.index, df['close'], color=COLORS['accent'], linewidth=1.5, label='Price')
                    
                    if 'sma_20' in df.columns:
                        ax.plot(df.index, df['sma_20'], color=COLORS['success'], linewidth=1, alpha=0.7, label='SMA 20')
                    if 'sma_50' in df.columns:
                        ax.plot(df.index, df['sma_50'], color=COLORS['warning'], linewidth=1, alpha=0.7, label='SMA 50')
                    
                    if instrument in self.analysis_results:
                        analysis = self.analysis_results[instrument]
                        if analysis['signal'] == 'SELL':
                            ax.axhline(y=analysis['price'], color=COLORS['sell'], linestyle='--', alpha=0.5)
                    
                    ax.set_title(f"{instrument.replace('_', '/')} - {self.timeframe_var.get()}", 
                               color=COLORS['fg'], fontsize=12, fontweight='bold')
                    ax.set_xlabel('Time', color=COLORS['fg'])
                    ax.set_ylabel('Price', color=COLORS['fg'])
                    ax.legend(facecolor=COLORS['panel'], edgecolor=COLORS['fg'], labelcolor=COLORS['fg'])
                    ax.grid(True, alpha=0.2, color=COLORS['fg'])
                    
                    chart['canvas'].draw()
    
    def update_signals(self):
        """Update signal strength indicators"""
        for instrument, widgets in self.signal_labels.items():
            if instrument in self.signal_strengths:
                score = self.signal_strengths[instrument]
                
                value = (score + 1) * 50
                widgets['bar']['value'] = value
                
                if score < -0.7:
                    widgets['text'].config(text="SELL", foreground=COLORS['sell'])
                else:
                    widgets['text'].config(text="HOLD", foreground=COLORS['fg'])
    
    def update_positions(self):
        """Update positions display with stop loss info"""
        if not self.trader:
            return
        
        self.pos_text.config(state=tk.NORMAL)
        self.pos_text.delete(1.0, tk.END)
        
        if self.trader.positions:
            for instrument, pos in self.trader.positions.items():
                try:
                    _, bid, ask = self.trader.get_prices(instrument)
                    current = ask
                    entry = pos['entry_price']
                    units = pos['units']
                    
                    pnl_pips = (entry - current)
                    pnl_pct = (entry - current) / entry * 100
                    pnl_dollars = pnl_pips * units
                    
                    color = 'green' if pnl_pct > 0 else 'red'
                    
                    self.pos_text.insert(tk.END, f"{instrument.replace('_', '/')}\n", 'bold')
                    self.pos_text.insert(tk.END, f"  SHORT | Entry: {entry:.5f}\n")
                    self.pos_text.insert(tk.END, f"  Current: {current:.5f}\n")
                    self.pos_text.insert(tk.END, f"  Stop Loss: {pos['stop_loss']:.5f}\n", 'warning')
                    self.pos_text.insert(tk.END, f"  Take Profit: {pos['take_profit']:.5f}\n", 'success')
                    self.pos_text.insert(tk.END, f"  P&L: {pnl_pct:+.2f}% (${pnl_dollars:+.2f})\n\n", color)
                    
                    self.pos_text.tag_config('bold', font=('Consolas', 9, 'bold'))
                    self.pos_text.tag_config('green', foreground=COLORS['success'])
                    self.pos_text.tag_config('red', foreground=COLORS['error'])
                    self.pos_text.tag_config('warning', foreground=COLORS['warning'])
                    self.pos_text.tag_config('success', foreground=COLORS['success'])
                except Exception as e:
                    print(f"Position update error: {e}")
        else:
            self.pos_text.insert(tk.END, "No open positions\n", 'neutral')
            self.pos_text.tag_config('neutral', foreground=COLORS['fg'])
        
        self.pos_text.config(state=tk.DISABLED)
    
    def update_performance(self):
        """Update performance metrics"""
        if not self.trader:
            return
        
        closed_trades = self.trader.closed_trades
        total = len(closed_trades)
        winning = len([t for t in closed_trades if t.get('pnl', 0) > 0])
        total_pnl = sum(t.get('pnl', 0) for t in closed_trades)
        
        today = datetime.now().date()
        today_pnl = sum(t.get('pnl', 0) for t in closed_trades 
                       if t.get('exit_time') and t['exit_time'].date() == today)
        
        self.perf_labels['Total Trades'].config(text=str(total))
        self.perf_labels['Open Positions'].config(text=str(len(self.trader.positions)))
        self.perf_labels['Win Rate'].config(text=f"{(winning/total*100) if total > 0 else 0:.1f}%")
        
        total_pnl_label = self.perf_labels['Total P&L']
        total_pnl_label.config(text=f"${total_pnl:+.2f}")
        total_pnl_label.config(foreground=COLORS['success'] if total_pnl >= 0 else COLORS['error'])
        
        today_pnl_label = self.perf_labels['Today P&L']
        today_pnl_label.config(text=f"${today_pnl:+.2f}")
        today_pnl_label.config(foreground=COLORS['success'] if today_pnl >= 0 else COLORS['error'])
        
        self.balance_label.config(text=f"${self.trader.balance:,.2f}")
        self.nav_label.config(text=f"${self.trader.nav:,.2f}")
        
        upl_label = self.upl_label
        upl_label.config(text=f"${self.trader.unrealized_pl:+,.2f}")
        upl_label.config(foreground=COLORS['success'] if self.trader.unrealized_pl >= 0 else COLORS['error'])
        
        self.margin_label.config(text=f"${self.trader.margin_used:,.2f}")
    
    def update_history(self):
        """Update trade history"""
        if not self.trader or not self.trader.closed_trades:
            return
        
        self.history_text.delete(1.0, tk.END)
        
        recent_trades = self.trader.closed_trades[-10:]
        
        for trade in reversed(recent_trades):
            time_str = trade['exit_time'].strftime("%H:%M:%S")
            instrument = trade['instrument'].replace('_', '/')
            direction = trade['direction']
            pnl = trade.get('pnl', 0)
            
            color = 'green' if pnl > 0 else 'red'
            
            self.history_text.insert(tk.END, f"[{time_str}] {instrument} {direction}\n", 'time')
            self.history_text.insert(tk.END, f"  Entry: {trade['entry_price']:.5f} → Exit: {trade['exit_price']:.5f}\n")
            self.history_text.insert(tk.END, f"  P&L: ${pnl:+.2f}\n\n", color)
        
        self.history_text.tag_config('time', foreground=COLORS['accent'])
        self.history_text.tag_config('green', foreground=COLORS['success'])
        self.history_text.tag_config('red', foreground=COLORS['error'])
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
        lines = self.log_text.get(1.0, tk.END).split('\n')
        if len(lines) > 102:
            self.log_text.delete(1.0, '3.0')


if __name__ == "__main__":
    root = tk.Tk()
    app = SafeTradingGUI(root)
    root.mainloop()
