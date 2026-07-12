"""
Ultimate FX Trading Interface - Final Version
- OANDA-style instrument panel with live prices
- Modern, professional design
- Real-time bid/ask display
- Fast updates and actual trading
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from datetime import datetime
from tpqoa.tpqoa import tpqoa

# Professional color scheme
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
    'hover': '#45475a',
    'instrument_bg': '#45475a',
    'instrument_selected': '#585b70'
}

class FastTrader(tpqoa):
    """Optimized trader with fast execution"""
    
    def __init__(self, config_path, timeframe="M5", risk_pct=1.0):
        super().__init__(config_path)
        self.timeframe = timeframe
        self.risk_pct = risk_pct / 100.0
        self.instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD', 
                           'EUR_JPY', 'GBP_JPY', 'EUR_GBP', 'NZD_USD', 'USD_CAD']
        self.positions = {}
        self.trades = []
        self.running = False
        self.balance = 10000.0
        self.live_prices = {}
        
        # Get actual balance
        try:
            summary = self.get_account_summary(detailed=True)
            self.balance = float(summary.get('balance', 10000.0))
        except:
            pass
    
    def get_live_prices_all(self):
        """Get live prices for all instruments - FAST"""
        prices = {}
        for instrument in self.instruments:
            
                # Use streaming price endpoint for speed
                response = self.ctx.pricing.get(
                    self.account_id,
                    instruments=instrument
                )
                if response.status == 200:
        def get_live_data(self, instrument, count=100):
                    if price_data:
                        price = price_data[0]
                        bid = float(price.bids[0].price) if price.bids else 0
                        ask = float(price.asks[0].price) if price.asks else 0
                        prices[instrument] = {
                            'bid': bid,
                            'ask': ask,
                            'spread': ask - bid,
                            'mid': (bid + ask) / 2
                        }
            except Exception as e:
                # Fallback to old method
                try:
                    _, bid, ask = self.get_prices(instrument)
                    prices[instrument] = {
                        'bid': bid,
                        'ask': ask,
                        'spread': ask - bid,
                        'mid': (bid + ask) / 2
                    }
                except:
                    pass
        return prices
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
            return None
    
    def analyze_fast(self, df):
        """Fast multi-indicator analysis"""
        if df is None or len(df) < 50:
            return {'signal': 'HOLD', 'score': 0.0}
        
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
        
        latest = df.iloc[-1]
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
        
        # Bollinger
        if latest['close'] < latest['bb_lower']:
            score += 0.3
        elif latest['close'] > latest['bb_upper']:
            score -= 0.3
        
        signal = 'BUY' if score > 0.5 else 'SELL' if score < -0.5 else 'HOLD'
        
        return {
            'signal': signal,
            'score': score,
            'price': latest['close'],
            'rsi': latest['rsi']
        }
    
    def execute_trade(self, instrument, signal, units=100):
        """Execute trade"""
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
            print(f"Trade error: {e}")
            return None


class UltimateTradingGUI:
    """Professional trading interface with OANDA-style instrument panel"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 FX Trading Bot - Professional Edition")
        self.root.geometry("1900x1000")
        self.root.configure(bg=COLORS['bg'])
        
        self.setup_style()
        
        self.trader = None
        self.account_type = "demo"
        self.trading_active = False
        self.selected_instrument = "EUR_USD"
        
        self.market_data = {}
        self.analysis_results = {}
        self.instrument_widgets = {}
        
        self.create_gui()
        self.connect_account("demo")
        self.start_updates()
    
    def setup_style(self):
        """Configure modern style"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=COLORS['bg'])
        style.configure('TLabel', background=COLORS['bg'], foreground=COLORS['fg'])
        style.configure('TLabelframe', background=COLORS['bg'], foreground=COLORS['accent'])
        style.configure('TLabelframe.Label', background=COLORS['bg'], foreground=COLORS['accent'], font=('Arial', 10, 'bold'))
        style.configure('Success.TButton', background=COLORS['success'], foreground=COLORS['bg'])
        style.configure('Error.TButton', background=COLORS['error'], foreground=COLORS['bg'])
    
    def create_gui(self):
        """Create professional GUI with instrument panel"""
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
        
        ttk.Label(control_frame, text="|", foreground=COLORS['panel']).pack(side=tk.LEFT, padx=10)
        
        self.start_btn = ttk.Button(control_frame, text="▶️ START TRADING", style='Success.TButton',
                                    command=self.start_trading)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ STOP", style='Error.TButton',
                                   command=self.stop_trading, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="|", foreground=COLORS['panel']).pack(side=tk.LEFT, padx=10)
        ttk.Label(control_frame, text="Timeframe:").pack(side=tk.LEFT, padx=5)
        self.timeframe_var = tk.StringVar(value="M5")
        ttk.Combobox(control_frame, textvariable=self.timeframe_var, values=["M1", "M5", "M15", "H1"],
                    state="readonly", width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Risk %:").pack(side=tk.LEFT, padx=5)
        self.risk_var = tk.DoubleVar(value=1.0)
        tk.Spinbox(control_frame, from_=0.5, to=5.0, increment=0.5, textvariable=self.risk_var,
                  width=5, bg=COLORS['panel'], fg=COLORS['fg']).pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(control_frame, text="🔄 Initializing...", font=('Arial', 10, 'bold'),
                                     foreground=COLORS['warning'])
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Main content
        content = ttk.Frame(self.root)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # LEFT PANEL - INSTRUMENTS (OANDA-style)
        left_panel = ttk.Frame(content, width=220)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_panel.pack_propagate(False)
        
        instruments_frame = ttk.LabelFrame(left_panel, text="📊 INSTRUMENTS", padding=5)
        instruments_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollable instrument list
        canvas = tk.Canvas(instruments_frame, bg=COLORS['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(instruments_frame, orient="vertical", command=canvas.yview)
        self.instruments_container = ttk.Frame(canvas)
        
        self.instruments_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.instruments_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create instrument widgets
        self.create_instrument_widgets()
        
        # MIDDLE PANEL - Chart
        middle_panel = ttk.Frame(content)
        middle_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        chart_frame = ttk.LabelFrame(middle_panel, text="📈 LIVE CHART", padding=10)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        fig = Figure(figsize=(10, 6), facecolor=COLORS['bg'])
        self.ax = fig.add_subplot(111, facecolor=COLORS['panel'])
        self.ax.tick_params(colors=COLORS['fg'])
        for spine in self.ax.spines.values():
            spine.set_color(COLORS['fg'])
        
        self.chart_canvas = FigureCanvasTkAgg(fig, chart_frame)
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Analysis log
        log_frame = ttk.LabelFrame(middle_panel, text="🔍 ANALYSIS LOG", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, bg=COLORS['panel'],
                                                 fg=COLORS['fg'], font=('Consolas', 9),
                                                 insertbackground=COLORS['fg'])
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # RIGHT PANEL - Info
        right_panel = ttk.Frame(content, width=350)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)
        
        # Account
        account_frame = ttk.LabelFrame(right_panel, text="💼 ACCOUNT", padding=10)
        account_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.balance_label = ttk.Label(account_frame, text="Balance: $10,000.00",
                                      font=('Arial', 14, 'bold'), foreground=COLORS['success'])
        self.balance_label.pack()
        
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
        for metric in ['Total Trades', 'Win Rate', 'Total P&L']:
            frame = ttk.Frame(perf_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f"{metric}:").pack(side=tk.LEFT)
            self.perf_labels[metric] = ttk.Label(frame, text="0", font=('Arial', 10, 'bold'))
            self.perf_labels[metric].pack(side=tk.RIGHT)
        
        # History
        history_frame = ttk.LabelFrame(right_panel, text="📝 HISTORY", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True)
        
        self.history_text = scrolledtext.ScrolledText(history_frame, height=10, bg=COLORS['panel'],
                                                     fg=COLORS['fg'], font=('Consolas', 8),
                                                     insertbackground=COLORS['fg'])
        self.history_text.pack(fill=tk.BOTH, expand=True)
    
    def create_instrument_widgets(self):
        """Create OANDA-style instrument widgets"""
        if not self.trader:
            return
        
        for instrument in self.trader.instruments:
            # Instrument frame
            frame = tk.Frame(self.instruments_container, bg=COLORS['instrument_bg'], 
                           relief=tk.RAISED, borderwidth=1, cursor="hand2")
            frame.pack(fill=tk.X, pady=2, padx=2)
            frame.bind("<Button-1>", lambda e, inst=instrument: self.select_instrument(inst))
            
            # Instrument name
            name_label = tk.Label(frame, text=instrument.replace('_', '/'), 
                                bg=COLORS['instrument_bg'], fg=COLORS['fg'],
                                font=('Arial', 10, 'bold'))
            name_label.pack(anchor=tk.W, padx=5, pady=(5, 0))
            name_label.bind("<Button-1>", lambda e, inst=instrument: self.select_instrument(inst))
            
            # Price container
            price_frame = tk.Frame(frame, bg=COLORS['instrument_bg'])
            price_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
            
            # Bid
            bid_frame = tk.Frame(price_frame, bg=COLORS['instrument_bg'])
            bid_frame.pack(side=tk.LEFT, expand=True)
            tk.Label(bid_frame, text="BID", bg=COLORS['instrument_bg'], 
                    fg=COLORS['fg'], font=('Arial', 7)).pack()
            bid_label = tk.Label(bid_frame, text="0.00000", bg=COLORS['instrument_bg'],
                               fg=COLORS['sell'], font=('Arial', 16, 'bold'))
            bid_label.pack()
            
            # Ask
            ask_frame = tk.Frame(price_frame, bg=COLORS['instrument_bg'])
            ask_frame.pack(side=tk.RIGHT, expand=True)
            tk.Label(ask_frame, text="ASK", bg=COLORS['instrument_bg'],
                    fg=COLORS['fg'], font=('Arial', 7)).pack()
            ask_label = tk.Label(ask_frame, text="0.00000", bg=COLORS['instrument_bg'],
                               fg=COLORS['buy'], font=('Arial', 16, 'bold'))
            ask_label.pack()
            
            self.instrument_widgets[instrument] = {
                'frame': frame,
                'bid_label': bid_label,
                'ask_label': ask_label
            }
    
    def select_instrument(self, instrument):
        """Select instrument and update chart"""
        self.selected_instrument = instrument
        
        # Update visual selection
        for inst, widgets in self.instrument_widgets.items():
            if inst == instrument:
                widgets['frame'].config(bg=COLORS['instrument_selected'])
            else:
                widgets['frame'].config(bg=COLORS['instrument_bg'])
        
        self.log(f"📊 Selected: {instrument.replace('_', '/')}")
        self.update_chart()
    
    def update_instrument_prices(self):
        """Update all instrument prices"""
        if not self.trader:
            return
        
        prices = self.trader.get_live_prices_all()
        
        for instrument, price_data in prices.items():
            if instrument in self.instrument_widgets:
                widgets = self.instrument_widgets[instrument]
                bid = price_data['bid']
                ask = price_data['ask']
                
                # Format based on instrument
                if 'JPY' in instrument:
                    widgets['bid_label'].config(text=f"{bid:.3f}")
                    widgets['ask_label'].config(text=f"{ask:.3f}")
                else:
                    widgets['bid_label'].config(text=f"{bid:.5f}")
                    widgets['ask_label'].config(text=f"{ask:.5f}")
    
    def connect_account(self, account_type):
        """Connect to OANDA"""
        self.account_type = account_type
        self.status_label.config(text=f"🔄 Connecting...", foreground=COLORS['warning'])
        
        def connect():
            try:
                config = f"config/oanda_{account_type}.cfg"
                self.trader = FastTrader(config, self.timeframe_var.get(), self.risk_var.get())
                self.status_label.config(text=f"✅ {account_type.upper()} Connected",
                                        foreground=COLORS['success'])
                self.balance_label.config(text=f"Balance: ${self.trader.balance:,.2f}")
                self.start_btn.config(state=tk.NORMAL)
                self.create_instrument_widgets()
                self.log(f"✅ Connected to {account_type.upper()}")
            except Exception as e:
                self.status_label.config(text=f"❌ Failed", foreground=COLORS['error'])
                self.log(f"❌ Error: {e}")
        
        threading.Thread(target=connect, daemon=True).start()
    
    def start_trading(self):
        """Start trading"""
        if not self.trader:
            return
        
        self.trading_active = True
        self.trader.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="🚀 TRADING ACTIVE", foreground=COLORS['success'])
        self.log("🚀 Trading started!")
        
        threading.Thread(target=self.trading_loop, daemon=True).start()
    
    def stop_trading(self):
        """Stop trading"""
        self.trading_active = False
        if self.trader:
            self.trader.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="⏹️ STOPPED", foreground=COLORS['warning'])
        self.log("⏹️ Stopped")
    
    def trading_loop(self):
        """Trading loop"""
        while self.trading_active and self.trader:
            try:
                for instrument in self.trader.instruments[:5]:  # Trade top 5
                    df = self.trader.get_live_data(instrument, 100)
                    if df is not None:
                        self.market_data[instrument] = df
                        analysis = self.trader.analyze_fast(df)
                        
                        if analysis['signal'] in ['BUY', 'SELL']:
                            if instrument not in self.trader.positions:
                                self.log(f"🎯 {instrument}: {analysis['signal']} (score: {analysis['score']:.2f})")
                                trade = self.trader.execute_trade(instrument, analysis['signal'], 100)
                                if trade:
                                    self.log(f"✅ {instrument}: {trade['direction']} @ {trade['entry_price']:.5f}")
                
                time.sleep(15)
            except Exception as e:
                self.log(f"❌ Error: {e}")
                time.sleep(30)
    
    def start_updates(self):
        
        # Price update thread - very fast
        def price_update_loop():
        def update_chart(self):
                try:
                    if self.trader:
            """Update chart for selected instrument"""
                    time.sleep(0.5)  # Update prices every 0.5 seconds
                except Exception as e:
                    print(f"Price update error: {e}")
                    time.sleep(2)
        
        # Chart and position update thread - moderate speed
        def display_update_loop():
            if self.selected_instrument in self.market_data:
                try:
                    if self.trader:
                df = self.market_data[self.selected_instrument]
                        self.update_positions()
                        self.update_performance()
                    time.sleep(2)  # Update displays every 2 seconds
                except Exception as e:
                    print(f"Display update error: {e}")
                    time.sleep(5)
        
        threading.Thread(target=price_update_loop, daemon=True).start()
        threading.Thread(target=display_update_loop, daemon=True).start()
            if df is not None and len(df) > 0:
                self.ax.clear()
                self.ax.plot(df.index, df['close'], color=COLORS['accent'], linewidth=1.5, label='Price')
                
                if 'sma_20' in df.columns:
                    self.ax.plot(df.index, df['sma_20'], color=COLORS['success'], linewidth=1, alpha=0.7, label='SMA 20')
                if 'sma_50' in df.columns:
                    self.ax.plot(df.index, df['sma_50'], color=COLORS['warning'], linewidth=1, alpha=0.7, label='SMA 50')
                
                self.ax.set_title(f"{self.selected_instrument.replace('_', '/')} - {self.timeframe_var.get()}", 
                                color=COLORS['fg'], fontsize=12, fontweight='bold')
                self.ax.set_xlabel('Time', color=COLORS['fg'])
                self.ax.set_ylabel('Price', color=COLORS['fg'])
                self.ax.legend(facecolor=COLORS['panel'], edgecolor=COLORS['fg'], labelcolor=COLORS['fg'])
                self.ax.grid(True, alpha=0.2, color=COLORS['fg'])
                
                self.chart_canvas.draw()
    
    def update_positions(self):
        """Update positions"""
        if not self.trader:
            return
        
        self.pos_text.config(state=tk.NORMAL)
        self.pos_text.delete(1.0, tk.END)
        
        if self.trader.positions:
            for instrument, pos in self.trader.positions.items():
                try:
                    _, bid, ask = self.trader.get_prices(instrument)
                    current = bid
                    entry = pos['entry_price']
                    
                    if pos['direction'] == 'LONG':
                        pnl_pct = (current - entry) / entry * 100
                    else:
                        pnl_pct = (entry - current) / entry * 100
                    
                    color = 'green' if pnl_pct > 0 else 'red'
                    
                    self.pos_text.insert(tk.END, f"{instrument.replace('_', '/')}\n", 'bold')
                    self.pos_text.insert(tk.END, f"  {pos['direction']} | Entry: {entry:.5f}\n")
                    self.pos_text.insert(tk.END, f"  Current: {current:.5f} | P&L: {pnl_pct:+.2f}%\n\n", color)
                    
                    self.pos_text.tag_config('bold', font=('Consolas', 9, 'bold'))
                    self.pos_text.tag_config('green', foreground=COLORS['success'])
                    self.pos_text.tag_config('red', foreground=COLORS['error'])
                except:
                    pass
        else:
            self.pos_text.insert(tk.END, "No open positions\n")
        
        self.pos_text.config(state=tk.DISABLED)
    
    def update_performance(self):
        """Update performance"""
        if not self.trader:
            return
        
        trades = self.trader.trades
        total = len(trades)
        winning = len([t for t in trades if t.get('pnl', 0) > 0])
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        
        self.perf_labels['Total Trades'].config(text=str(total))
        self.perf_labels['Win Rate'].config(text=f"{(winning/total*100) if total > 0 else 0:.1f}%")
        self.perf_labels['Total P&L'].config(text=f"${total_pnl:+.2f}")
        
        self.balance_label.config(text=f"Balance: ${self.trader.balance + total_pnl:,.2f}")
    
    def log(self, message):
        """Log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
        lines = self.log_text.get(1.0, tk.END).split('\n')
        if len(lines) > 102:
            self.log_text.delete(1.0, '3.0')


if __name__ == "__main__":
    root = tk.Tk()
    app = UltimateTradingGUI(root)
    root.mainloop()
