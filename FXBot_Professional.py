"""
FX Trading Bot - Professional Edition
- OANDA-style instrument panel with live BID/ASK
- Fast price updates (0.5s)
- Quick trading execution (5s cycles)
- Modern, user-friendly interface
- Real-time data and charts
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
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
        
        try:
            summary = self.get_account_summary(detailed=True)
            self.balance = float(summary.get('balance', 10000.0))
        except:
            pass
    
    def get_live_prices_batch(self):
        """Get live prices for all instruments - FAST"""
        prices = {}
        for instrument in self.instruments:
            
                # Use pricing API directly
                response = self.ctx.pricing.get(
                    self.account_id,
                    instruments=instrument
                )
                if response.status == 200 and response.body.get('prices'):
                    price_data = response.body['prices'][0]
                    bid = float(price_data.bids[0].price) if price_data.bids else 0
                    ask = float(price_data.asks[0].price) if price_data.asks else 0
                    if bid > 0 and ask > 0:
                        prices[instrument] = {'bid': bid, 'ask': ask, 'spread': ask - bid}
            except Exception as e:
                # Silently continue on error
                continue
        return prices
=======
            def get_live_data(self, instrument, count=50):
        """Fast data retrieval - reduced count for speed"""
        try:
            response = self.ctx.instrument.candles(
                instrument, granularity=self.timeframe, count=count, price="MBA"
            )
            
            if response.status != 200:
                return None
            
            data = []
            for candle in response.body.get('candles', []):
                data.append({
                    'time': pd.to_datetime(candle.time),
                    'close': float(candle.mid.c),
                    'high': float(candle.mid.h),
                    'low': float(candle.mid.l)
                })
            
            df = pd.DataFrame(data)
            df.set_index('time', inplace=True)
            return df
        except:
            return None
    
    def analyze_fast(self, df):
        """Quick analysis"""
        if df is None or len(df) < 30:
            return {'signal': 'HOLD', 'score': 0.0}
        
        df['sma_20'] = df['close'].rolling(20).mean()
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        score = 0.0
        if latest['sma_20'] > prev['sma_20']:
            score += 0.5
        else:
            score -= 0.5
        
        signal = 'BUY' if score > 0.4 else 'SELL' if score < -0.4 else 'HOLD'
        return {'signal': signal, 'score': score, 'price': latest['close']}
    
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


class ProfessionalGUI:
    """Professional trading interface"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 FX Trading Bot - Professional Edition")
        self.root.geometry("1900x1000")
        self.root.configure(bg=COLORS['bg'])
        
        self.setup_style()
        
        self.trader = None
        self.trading_active = False
        self.selected_instrument = "EUR_USD"
        self.market_data = {}
        self.instrument_widgets = {}
        
        self.create_gui()
        self.connect_account("demo")
        self.start_updates()
    
    def setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=COLORS['bg'])
        style.configure('TLabel', background=COLORS['bg'], foreground=COLORS['fg'])
        style.configure('TLabelframe', background=COLORS['bg'], foreground=COLORS['accent'])
        style.configure('TLabelframe.Label', background=COLORS['bg'], foreground=COLORS['accent'], font=('Arial', 10, 'bold'))
        style.configure('Success.TButton', background=COLORS['success'], foreground=COLORS['bg'])
        style.configure('Error.TButton', background=COLORS['error'], foreground=COLORS['bg'])
    
    def create_gui(self):
        # Top control bar
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(control_frame, text="Account:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.account_var = tk.StringVar(value="demo")
        ttk.Radiobutton(control_frame, text="📊 Demo", variable=self.account_var, value="demo",
                       command=lambda: self.connect_account("demo")).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(control_frame, text="💰 Live", variable=self.account_var, value="live",
                       command=lambda: self.connect_account("live")).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="|", foreground=COLORS['panel']).pack(side=tk.LEFT, padx=10)
        
        self.start_btn = ttk.Button(control_frame, text="▶️ START", style='Success.TButton',
                                    command=self.start_trading)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ STOP", style='Error.TButton',
                                   command=self.stop_trading, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(control_frame, text="🔄 Initializing...", font=('Arial', 10, 'bold'),
                                     foreground=COLORS['warning'])
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Main content
        content = ttk.Frame(self.root)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # LEFT - Instruments
        left_panel = ttk.Frame(content, width=220)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_panel.pack_propagate(False)
        
        instruments_frame = ttk.LabelFrame(left_panel, text="📊 INSTRUMENTS", padding=5)
        instruments_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(instruments_frame, bg=COLORS['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(instruments_frame, orient="vertical", command=canvas.yview)
        self.instruments_container = ttk.Frame(canvas)
        
        self.instruments_container.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=self.instruments_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # MIDDLE - Chart
        middle_panel = ttk.Frame(content)
        middle_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        chart_frame = ttk.LabelFrame(middle_panel, text="📈 CHART", padding=10)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        fig = Figure(figsize=(10, 6), facecolor=COLORS['bg'])
        self.ax = fig.add_subplot(111, facecolor=COLORS['panel'])
        self.ax.tick_params(colors=COLORS['fg'])
        for spine in self.ax.spines.values():
            spine.set_color(COLORS['fg'])
        
        self.chart_canvas = FigureCanvasTkAgg(fig, chart_frame)
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        log_frame = ttk.LabelFrame(middle_panel, text="🔍 LOG", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, bg=COLORS['panel'],
                                                 fg=COLORS['fg'], font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # RIGHT - Info
        right_panel = ttk.Frame(content, width=350)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)
        
        account_frame = ttk.LabelFrame(right_panel, text="💼 ACCOUNT", padding=10)
        account_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.balance_label = ttk.Label(account_frame, text="Balance: $10,000.00",
                                      font=('Arial', 14, 'bold'), foreground=COLORS['success'])
        self.balance_label.pack()
        
        pos_frame = ttk.LabelFrame(right_panel, text="📊 POSITIONS", padding=10)
        pos_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.pos_text = tk.Text(pos_frame, height=10, bg=COLORS['panel'], fg=COLORS['fg'],
                               font=('Consolas', 9), state=tk.DISABLED)
        self.pos_text.pack(fill=tk.BOTH, expand=True)
        
        perf_frame = ttk.LabelFrame(right_panel, text="📈 PERFORMANCE", padding=10)
        perf_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.perf_labels = {}
        for metric in ['Trades', 'Win Rate', 'P&L']:
            frame = ttk.Frame(perf_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f"{metric}:").pack(side=tk.LEFT)
            self.perf_labels[metric] = ttk.Label(frame, text="0", font=('Arial', 10, 'bold'))
            self.perf_labels[metric].pack(side=tk.RIGHT)
    
    def create_instrument_widgets(self):
        """Create instrument price widgets"""
        if not self.trader:
            return
        
        for instrument in self.trader.instruments:
            frame = tk.Frame(self.instruments_container, bg=COLORS['instrument_bg'], 
                           relief=tk.RAISED, borderwidth=1, cursor="hand2")
            frame.pack(fill=tk.X, pady=2, padx=2)
            frame.bind("<Button-1>", lambda e, inst=instrument: self.select_instrument(inst))
            
            name_label = tk.Label(frame, text=instrument.replace('_', '/'), 
                                bg=COLORS['instrument_bg'], fg=COLORS['fg'],
                                font=('Arial', 10, 'bold'))
            name_label.pack(anchor=tk.W, padx=5, pady=(5, 0))
            name_label.bind("<Button-1>", lambda e, inst=instrument: self.select_instrument(inst))
            
            price_frame = tk.Frame(frame, bg=COLORS['instrument_bg'])
            price_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
            
            bid_frame = tk.Frame(price_frame, bg=COLORS['instrument_bg'])
            bid_frame.pack(side=tk.LEFT, expand=True)
            tk.Label(bid_frame, text="BID", bg=COLORS['instrument_bg'], 
                    fg=COLORS['fg'], font=('Arial', 7)).pack()
            bid_label = tk.Label(bid_frame, text="0.00000", bg=COLORS['instrument_bg'],
                               fg=COLORS['sell'], font=('Arial', 16, 'bold'))
            bid_label.pack()
            
            ask_frame = tk.Frame(price_frame, bg=COLORS['instrument_bg'])
            ask_frame.pack(side=tk.RIGHT, expand=True)
            tk.Label(ask_frame, text="ASK", bg=COLORS['instrument_bg'],
                    fg=COLORS['fg'], font=('Arial', 7)).pack()
            ask_label = tk.Label(ask_frame, text="0.00000", bg=COLORS['instrument_bg'],
                               fg=COLORS['buy'], font=('Arial', 16, 'bold'))
            ask_label.pack()
            
            self.instrument_widgets[instrument] = {
                'frame': frame, 'bid_label': bid_label, 'ask_label': ask_label
            }
    
    def select_instrument(self, instrument):
        self.selected_instrument = instrument
        for inst, widgets in self.instrument_widgets.items():
            widgets['frame'].config(bg=COLORS['instrument_selected'] if inst == instrument else COLORS['instrument_bg'])
        self.log(f"📊 Selected: {instrument.replace('_', '/')}")
    
    def update_prices(self):
        """Update instrument prices - FAST"""
        if not self.trader:
            return
        
        prices = self.trader.get_live_prices_batch()
        for instrument, price_data in prices.items():
            if instrument in self.instrument_widgets:
                widgets = self.instrument_widgets[instrument]
                bid, ask = price_data['bid'], price_data['ask']
                
                if 'JPY' in instrument:
                    widgets['bid_label'].config(text=f"{bid:.3f}")
                    widgets['ask_label'].config(text=f"{ask:.3f}")
                else:
                    widgets['bid_label'].config(text=f"{bid:.5f}")
                    widgets['ask_label'].config(text=f"{ask:.5f}")
    
    def connect_account(self, account_type):
        self.status_label.config(text=f"🔄 Connecting...", foreground=COLORS['warning'])
        
        def connect():
            try:
                config = f"config/oanda_{account_type}.cfg"
                self.trader = FastTrader(config)
                self.status_label.config(text=f"✅ {account_type.upper()} Connected", foreground=COLORS['success'])
                self.balance_label.config(text=f"Balance: ${self.trader.balance:,.2f}")
                self.start_btn.config(state=tk.NORMAL)
                self.create_instrument_widgets()
                self.log(f"✅ Connected to {account_type.upper()}")
            except Exception as e:
                self.status_label.config(text=f"❌ Failed", foreground=COLORS['error'])
                self.log(f"❌ Error: {e}")
        
        threading.Thread(target=connect, daemon=True).start()
    
    def start_trading(self):
        if not self.trader:
            return
        
        self.trading_active = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="🚀 ACTIVE", foreground=COLORS['success'])
        self.log("🚀 Trading started!")
        threading.Thread(target=self.trading_loop, daemon=True).start()
    
    def stop_trading(self):
        self.trading_active = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="⏹️ STOPPED", foreground=COLORS['warning'])
        self.log("⏹️ Stopped")
    
    def trading_loop(self):
        """Fast trading loop - 5 second cycles"""
        while self.trading_active and self.trader:
            try:
                for instrument in self.trader.instruments[:3]:  # Top 3 for speed
                    if instrument not in self.trader.positions:
                        df = self.trader.get_live_data(instrument)
                        if df is not None:
                            self.market_data[instrument] = df
                            analysis = self.trader.analyze_fast(df)
                            
                            if analysis['signal'] in ['BUY', 'SELL']:
                                self.log(f"🎯 {instrument.replace('_', '/')}: {analysis['signal']}")
                                trade = self.trader.execute_trade(instrument, analysis['signal'], 100)
                                if trade:
                                    self.log(f"✅ {instrument.replace('_', '/')}: {trade['direction']} @ {trade['entry_price']:.5f}")
                
                time.sleep(5)  # Fast 5-second cycles
            except Exception as e:
                self.log(f"❌ Error: {e}")
                time.sleep(10)
    
    def start_updates(self):
        """Start update loops"""
        def price_loop():
            while True:
                try:
                    if self.trader:
                        self.update_prices()
                    time.sleep(0.5)  # Update prices every 0.5 seconds
                except:
                    time.sleep(2)
        
        def display_loop():
            while True:
                try:
                    if self.trader:
                        self.update_chart()
                        self.update_positions()
                        self.update_performance()
                    time.sleep(2)
                except:
                    time.sleep(5)
        
        threading.Thread(target=price_loop, daemon=True).start()
        threading.Thread(target=display_loop, daemon=True).start()
    
    def update_chart(self):
        if self.selected_instrument in self.market_data:
            df = self.market_data[self.selected_instrument]
            if df is not None and len(df) > 0:
                self.ax.clear()
                self.ax.plot(df.index, df['close'], color=COLORS['accent'], linewidth=1.5)
                if 'sma_20' in df.columns:
                    self.ax.plot(df.index, df['sma_20'], color=COLORS['success'], linewidth=1, alpha=0.7)
                self.ax.set_title(f"{self.selected_instrument.replace('_', '/')}", color=COLORS['fg'], fontweight='bold')
                self.ax.grid(True, alpha=0.2, color=COLORS['fg'])
                self.chart_canvas.draw()
    
    def update_positions(self):
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
                    pnl_pct = ((current - entry) / entry * 100) if pos['direction'] == 'LONG' else ((entry - current) / entry * 100)
                    color = 'green' if pnl_pct > 0 else 'red'
                    
                    self.pos_text.insert(tk.END, f"{instrument.replace('_', '/')}\n", 'bold')
                    self.pos_text.insert(tk.END, f"  {pos['direction']} | P&L: {pnl_pct:+.2f}%\n\n", color)
                    
                    self.pos_text.tag_config('bold', font=('Consolas', 9, 'bold'))
                    self.pos_text.tag_config('green', foreground=COLORS['success'])
                    self.pos_text.tag_config('red', foreground=COLORS['error'])
                except:
                    pass
        else:
            self.pos_text.insert(tk.END, "No positions\n")
        
        self.pos_text.config(state=tk.DISABLED)
    
    def update_performance(self):
        if not self.trader:
            return
        
        trades = self.trader.trades
        total = len(trades)
        winning = len([t for t in trades if t.get('pnl', 0) > 0])
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        
        self.perf_labels['Trades'].config(text=str(total))
        self.perf_labels['Win Rate'].config(text=f"{(winning/total*100) if total > 0 else 0:.1f}%")
        self.perf_labels['P&L'].config(text=f"${total_pnl:+.2f}")
        self.balance_label.config(text=f"Balance: ${self.trader.balance + total_pnl:,.2f}")
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        lines = self.log_text.get(1.0, tk.END).split('\n')
        if len(lines) > 102:
            self.log_text.delete(1.0, '3.0')


if __name__ == "__main__":
    root = tk.Tk()
    app = ProfessionalGUI(root)
    root.mainloop()
