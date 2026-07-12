import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
import time
from datetime import datetime
from livetrading.FemtoTrader import FemtoTrader
import os
import shutil

class TradingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FX Auto Trader - Live Dashboard")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e1e1e')

        # Message queue for thread communication
        self.message_queue = queue.Queue()

        # Trading state
        self.trader = None
        self.trading_thread = None
        self.is_trading = False

        # Setup GUI
        self.setup_styles()
        self.create_widgets()
        self.setup_layout()

        # Start message processing
        self.process_messages()

    def setup_styles(self):
        """Setup custom styles for modern look"""
        style = ttk.Style()
        style.configure('Modern.TFrame', background='#1e1e1e')
        style.configure('Modern.TLabel', background='#1e1e1e', foreground='#ffffff', font=('Segoe UI', 10))
        style.configure('Title.TLabel', background='#1e1e1e', foreground='#00ff88', font=('Segoe UI', 16, 'bold'))
        style.configure('Balance.TLabel', background='#1e1e1e', foreground='#ffff00', font=('Segoe UI', 14, 'bold'))
        style.configure('Status.TLabel', background='#1e1e1e', foreground='#ff6b6b', font=('Segoe UI', 12))

    def create_widgets(self):

        # Header
        self.header_frame = ttk.Frame(self.root, style='Modern.TFrame')
        self.title_label = ttk.Label(self.header_frame, text="🤖 FX Auto Trader Dashboard", style='Title.TLabel')

        # Configuration Panel
        self.config_frame = ttk.Frame(self.root, style='Modern.TFrame')
        self.config_title = ttk.Label(self.config_frame, text="⚙️ Trading Configuration", style='Title.TLabel')

        # Risk settings
        self.risk_label = ttk.Label(self.config_frame, text="Risk per trade (%):", style='Modern.TLabel')
        self.risk_var = tk.StringVar(value="5.0")
        self.risk_entry = tk.Entry(self.config_frame, textvariable=self.risk_var, width=10, bg='#2d2d2d', fg='#ffffff')

        self.sl_label = ttk.Label(self.config_frame, text="Stop Loss (%):", style='Modern.TLabel')
        self.sl_var = tk.StringVar(value="0.25")
        self.sl_entry = tk.Entry(self.config_frame, textvariable=self.sl_var, width=10, bg='#2d2d2d', fg='#ffffff')

        self.tp_label = ttk.Label(self.config_frame, text="Take Profit (%):", style='Modern.TLabel')
        self.tp_var = tk.StringVar(value="0.5")
        self.tp_entry = tk.Entry(self.config_frame, textvariable=self.tp_var, width=10, bg='#2d2d2d', fg='#ffffff')

        # Instrument selection
        self.instrument_mode_label = ttk.Label(self.config_frame, text="Instrument Selection:", style='Modern.TLabel')
        self.instrument_mode_var = tk.StringVar(value="auto")
        self.auto_radio = tk.Radiobutton(self.config_frame, text="Auto (Bot chooses best)", variable=self.instrument_mode_var,
                                       value="auto", bg='#1e1e1e', fg='#ffffff', selectcolor='#1e1e1e',
                                       command=self.toggle_instrument_selection)
        self.manual_radio = tk.Radiobutton(self.config_frame, text="Manual (Select pair)", variable=self.instrument_mode_var,
                                         value="manual", bg='#1e1e1e', fg='#ffffff', selectcolor='#1e1e1e',
                                         command=self.toggle_instrument_selection)

        self.pair_label = ttk.Label(self.config_frame, text="Select Pair:", style='Modern.TLabel')
        self.pair_var = tk.StringVar(value="EUR_USD")
        self.pair_combo = ttk.Combobox(self.config_frame, textvariable=self.pair_var,
                                     values=['EUR_USD', 'GBP_USD', 'USD_JPY', 'AUD_USD', 'USD_CAD', 'USD_CHF'],
                                     state='disabled', width=10)

        # Timing info
        self.timing_info = ttk.Label(self.config_frame,
                                   text="⏱️ Bot checks for trades every 30 seconds. Trades occur when strong signals are detected.",
                                   style='Modern.TLabel', wraplength=600)

        # Account Info
        self.account_frame = ttk.Frame(self.root, style='Modern.TFrame')
        self.balance_label = ttk.Label(self.account_frame, text="Account Balance: $0.00", style='Balance.TLabel')
        self.instrument_label = ttk.Label(self.account_frame, text="Current Instrument: None", style='Modern.TLabel')
        self.account_type_label = ttk.Label(self.account_frame, text="Account Type: Live", style='Modern.TLabel')

        # Current Position
        self.position_frame = ttk.Frame(self.root, style='Modern.TFrame')
        self.position_title = ttk.Label(self.position_frame, text="📊 Current Position", style='Title.TLabel')
        self.position_status = ttk.Label(self.position_frame, text="No active position", style='Status.TLabel')
        self.position_details = ttk.Label(self.position_frame, text="", style='Modern.TLabel')

        # Control Panel
        self.control_frame = ttk.Frame(self.root, style='Modern.TFrame')
        self.start_button = tk.Button(self.control_frame, text="▶️ START TRADING", command=self.start_trading,
                                    bg='#00ff88', fg='black', font=('Segoe UI', 12, 'bold'),
                                    relief='raised', padx=20, pady=10)
        self.stop_button = tk.Button(self.control_frame, text="⏹️ STOP TRADING", command=self.stop_trading,
                                   bg='#ff6b6b', fg='white', font=('Segoe UI', 12, 'bold'),
                                   relief='raised', padx=20, pady=10, state='disabled')

        # Trading Log
        self.log_frame = ttk.Frame(self.root, style='Modern.TFrame')
        self.log_title = ttk.Label(self.log_frame, text="📝 Trading Activity Log", style='Title.TLabel')
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=20, width=80,
                                                bg='#2d2d2d', fg='#ffffff', font=('Consolas', 9),
                                                insertbackground='#ffffff')

        # Market Analysis
        self.analysis_frame = ttk.Frame(self.root, style='Modern.TFrame')
        self.analysis_title = ttk.Label(self.analysis_frame, text="🔍 Market Analysis", style='Title.TLabel')
        self.analysis_text = tk.Text(self.analysis_frame, height=8, width=80,
                                   bg='#2d2d2d', fg='#ffffff', font=('Segoe UI', 9),
                                   state='disabled', wrap=tk.WORD)

        # Status Bar
        self.status_frame = ttk.Frame(self.root, style='Modern.TFrame')
        self.status_label = ttk.Label(self.status_frame, text="Configure settings and start trading...", style='Modern.TLabel')

    def setup_layout(self):

        # Header
        self.header_frame.pack(fill='x', padx=20, pady=10)
        self.title_label.pack()

        # Configuration Panel
        self.config_frame.pack(fill='x', padx=20, pady=10)
        self.config_title.pack(anchor='w')

        # Risk settings row
        risk_frame = ttk.Frame(self.config_frame, style='Modern.TFrame')
        risk_frame.pack(fill='x', pady=5)
        self.risk_label.pack(side='left', padx=5)
        self.risk_entry.pack(side='left', padx=5)
        self.sl_label.pack(side='left', padx=10)
        self.sl_entry.pack(side='left', padx=5)
        self.tp_label.pack(side='left', padx=10)
        self.tp_entry.pack(side='left', padx=5)

        # Instrument selection row
        instrument_frame = ttk.Frame(self.config_frame, style='Modern.TFrame')
        instrument_frame.pack(fill='x', pady=5)
        self.instrument_mode_label.pack(side='left', padx=5)
        self.auto_radio.pack(side='left', padx=5)
        self.manual_radio.pack(side='left', padx=10)
        self.pair_label.pack(side='left', padx=5)
        self.pair_combo.pack(side='left', padx=5)

        # Timing info
        self.timing_info.pack(anchor='w', pady=10)

        # Account Info
        self.account_frame.pack(fill='x', padx=20, pady=5)
        self.balance_label.pack(side='left', padx=10)
        self.instrument_label.pack(side='left', padx=10)
        self.account_type_label.pack(side='right', padx=10)

        # Current Position
        self.position_frame.pack(fill='x', padx=20, pady=10)
        self.position_title.pack(anchor='w')
        self.position_status.pack(anchor='w', pady=5)
        self.position_details.pack(anchor='w')

        # Control Panel
        self.control_frame.pack(fill='x', padx=20, pady=10)
        self.start_button.pack(side='left', padx=10)
        self.stop_button.pack(side='left', padx=10)

        # Trading Log
        self.log_frame.pack(fill='both', expand=True, padx=20, pady=10)
        self.log_title.pack(anchor='w')
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Market Analysis
        self.analysis_frame.pack(fill='x', padx=20, pady=10)
        self.analysis_title.pack(anchor='w')
        self.analysis_text.pack(fill='x', padx=5, pady=5)

        # Status Bar
        self.status_frame.pack(fill='x', padx=20, pady=5)
        self.status_label.pack()

    def toggle_instrument_selection(self):
        """Toggle manual instrument selection"""
        if self.instrument_mode_var.get() == "manual":
            self.pair_combo.config(state='normal')
        else:
            self.pair_combo.config(state='disabled')

    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def update_analysis(self, analysis_data):
        """Update market analysis display"""
        self.analysis_text.config(state='normal')
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(tk.END, analysis_data)
        self.analysis_text.config(state='disabled')

    def update_position(self, position_info):
        """Update position display"""
        if position_info:
            self.position_status.config(text=f"Active: {position_info.get('type', '').upper()}", foreground='#00ff88')
            details = f"Units: {position_info.get('units', 0)} | Entry: ${position_info.get('entry_price', 0):.5f}"
            self.position_details.config(text=details)
        else:
            self.position_status.config(text="No active position", foreground='#ff6b6b')
            self.position_details.config(text="")

    def update_balance(self, balance):
        """Update balance display"""
        self.balance_label.config(text=f"Account Balance: ${balance:.2f}")

    def update_instrument(self, instrument):
        """Update instrument display"""
        if instrument:
            self.instrument_label.config(text=f"Current Instrument: {instrument}")
        else:
            self.instrument_label.config(text="Current Instrument: None")

    def start_trading(self):
        """Start the trading bot"""
        if self.is_trading:
            return

        self.log_message("🚀 Starting FX Auto Trader...")
        self.status_label.config(text="Initializing trader...")

        # Setup config
        if not os.path.exists("config/oanda_live.cfg"):
            self.log_message("❌ Live config not found!")
            return

        shutil.copy2("config/oanda_live.cfg", "oanda.cfg")

        # Create trader with GUI callbacks
        self.trader = FemtoTrader(
            cfg="oanda.cfg",
            risk_per_trade=0.05,
            stop_loss_pct=0.25,
            take_profit_pct=0.5,
        )

        # Set GUI callbacks for thread-safe updates
        self.trader.set_gui_callbacks(
            price_callback=lambda price: self.message_queue.put(('price', price)),
            signal_callback=lambda signal: self.message_queue.put(('signal', signal)),
            news_callback=lambda news: self.message_queue.put(('news', news)),
            technical_callback=lambda tech: self.message_queue.put(('technical', tech)),
            position_callback=lambda pos: self.message_queue.put(('position', pos)),
            history_callback=lambda hist: self.message_queue.put(('history', hist))
        )

        # Update balance
        self.update_balance(self.trader._balance)

        # Start trading thread
        self.is_trading = True
        self.trading_thread = threading.Thread(target=self.trading_loop, daemon=True)
        self.trading_thread.start()

        # Update UI
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_label.config(text="Trading active...")
            
    def stop_trading(self):
        """Stop the trading bot"""
        if not self.is_trading:
            return

        self.log_message("🛑 Stopping FX Auto Trader...")
        self.is_trading = False

        if self.trader and self.trader._position:
            self.trader.close_position()

        # Update UI
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text="Trading stopped")

    def trading_loop(self):
        """Main trading loop running in background thread"""
        self.message_queue.put(('log', "Smart Auto Trader initialized"))
        self.message_queue.put(('instrument', None))

        while self.is_trading:
            try:
                # Check for stop datetime
                if hasattr(self.trader, '_stop_datetime') and self.trader._stop_datetime:
                    if datetime.now() >= self.trader._stop_datetime:
                        self.message_queue.put(('log', f"Stop datetime reached: {self.trader._stop_datetime.strftime('%Y-%m-%d %H:%M:%S')}"))
                        self.is_trading = False
                        break

                # Update position
                self.message_queue.put(('position', self.trader._position))

                # Manage trades
                self.trader.manage_trades()

                # Update instrument
                self.message_queue.put(('instrument', self.trader._pair))

                # Get market analysis for display
                if self.trader._pair:
                    analysis = self.trader._analyze_market(self.trader._pair)
                    if analysis:
                        analysis_text = f"""Market Analysis:
Strength: {analysis['strength']:.2f}
Direction: {'📈 Long' if analysis['direction'] > 0 else '📉 Short'}
Price: ${analysis['current_price']:.5f}

Sentiment Score: {analysis['sentiment']['sentiment_score']:.2f}
News Articles: {analysis['sentiment']['news_count']}
"""
                        self.message_queue.put(('analysis', analysis_text))
                else:
                    self.message_queue.put(('analysis', "No instrument selected yet."))

                # Wait before next check (reduced to 30 seconds for faster updates)
                time.sleep(30)

            except Exception as e:
                self.message_queue.put(('log', f"Error in trading loop: {str(e)}"))
                time.sleep(5)

        self.message_queue.put(('log', "Trading loop ended"))

    def process_messages(self):
        """Process messages from trading thread"""
        try:
            while True:
                message_type, data = self.message_queue.get_nowait()

                if message_type == 'log':
                    self.log_message(data)
                elif message_type == 'analysis':
                    self.update_analysis(data)
                elif message_type == 'position':
                    self.update_position(data)
                elif message_type == 'balance':
                    self.update_balance(data)
                elif message_type == 'instrument':
                    self.update_instrument(data)

        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self.process_messages)

    def on_closing(self):
        """Handle window closing"""
        self.stop_trading()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = TradingGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
