import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from datetime import datetime
from FemtoTrader_advanced import FemtoTrader
from chart_visualizer import ChartVisualizer

class AdvancedTradingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced FX Auto Trader - Trendlines & Patterns")
        self.root.geometry("1400x900")

        # Initialize trader and visualizer
        self.trader = None
        self.visualizer = ChartVisualizer()
        self.chart_canvas = None

        # Trading data
        self.current_price = 0.0
        self.account_balance = 0.0
        self.current_position = None
        self.trade_history = []
        self.chart_data = None

        # Create GUI components
        self.create_widgets()

        # Start trader in background thread
        self.start_trader()

    def create_widgets(self):
        """Create all GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top control panel
        control_frame = ttk.LabelFrame(main_frame, text="Trading Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # Status indicators
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill=tk.X)

        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky=tk.W)
        self.status_label = ttk.Label(status_frame, text="Initializing...", foreground="orange")
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 20))

        ttk.Label(status_frame, text="Balance:").grid(row=0, column=2, sticky=tk.W)
        self.balance_label = ttk.Label(status_frame, text="$0.00")
        self.balance_label.grid(row=0, column=3, sticky=tk.W, padx=(5, 20))

        ttk.Label(status_frame, text="Current Price:").grid(row=0, column=4, sticky=tk.W)
        self.price_label = ttk.Label(status_frame, text="$0.00000")
        self.price_label.grid(row=0, column=5, sticky=tk.W, padx=(5, 20))

        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        self.start_button = ttk.Button(button_frame, text="Start Trading", command=self.start_trading)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_button = ttk.Button(button_frame, text="Stop Trading", command=self.stop_trading, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))

        self.close_position_button = ttk.Button(button_frame, text="Close Position", command=self.close_position, state=tk.DISABLED)
        self.close_position_button.pack(side=tk.LEFT, padx=(0, 10))

        # Main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel - Chart
        chart_frame = ttk.LabelFrame(content_frame, text="Live Chart Analysis", padding=10)
        chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Chart canvas placeholder
        self.chart_frame = ttk.Frame(chart_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)

        # Right panel - Information
        info_frame = ttk.Frame(content_frame)
        info_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Current position
        position_frame = ttk.LabelFrame(info_frame, text="Current Position", padding=10)
        position_frame.pack(fill=tk.X, pady=(0, 10))

        self.position_text = tk.Text(position_frame, height=6, width=40, state=tk.DISABLED)
        position_text_scroll = ttk.Scrollbar(position_frame, command=self.position_text.yview)
        self.position_text.config(yscrollcommand=position_text_scroll.set)
        self.position_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        position_text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Analysis log
        analysis_frame = ttk.LabelFrame(info_frame, text="Analysis Log", padding=10)
        analysis_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.analysis_text = scrolledtext.ScrolledText(analysis_frame, height=15, width=40)
        self.analysis_text.pack(fill=tk.BOTH, expand=True)

        # Trade history
        history_frame = ttk.LabelFrame(info_frame, text="Trade History", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True)

        self.history_text = scrolledtext.ScrolledText(history_frame, height=8, width=40)
        self.history_text.pack(fill=tk.BOTH, expand=True)

        # Initialize chart
        self.init_chart()

    def init_chart(self):
        """Initialize the matplotlib chart in the GUI."""
        # Create figure and canvas
        self.visualizer.fig.set_size_inches(8, 6)
        self.chart_canvas = FigureCanvasTkAgg(self.visualizer.fig, master=self.chart_frame)
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def start_trader(self):
        """Start the trader in background thread."""
        def run_trader():
            try:
                self.trader = FemtoTrader("config/oanda_practice.cfg")

                # Set up callbacks
                self.trader.set_gui_callbacks(
                    price_callback=self.update_price,
                    signal_callback=self.update_signal,
                    chart_callback=self.update_chart,
                    position_callback=self.update_position,
                    history_callback=self.update_history
                )

                self.status_label.config(text="Connected", foreground="green")
                self.start_button.config(state=tk.NORMAL)

            except Exception as e:
                self.status_label.config(text=f"Error: {str(e)}", foreground="red")
                messagebox.showerror("Connection Error", f"Failed to connect to OANDA: {str(e)}")

        trader_thread = threading.Thread(target=run_trader, daemon=True)
        trader_thread.start()

    def start_trading(self):
        """Start automated trading."""
        if self.trader:
            self.status_label.config(text="Trading Active", foreground="green")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.close_position_button.config(state=tk.NORMAL)

            # Start trading in background thread
            def trading_loop():
                try:
                    self.trader.run()
                except Exception as e:
                    self.log_analysis(f"Trading error: {str(e)}")

            trading_thread = threading.Thread(target=trading_loop, daemon=True)
            trading_thread.start()

    def stop_trading(self):
        """Stop automated trading."""
        if self.trader:
            self.trader.close_position()
            self.status_label.config(text="Trading Stopped", foreground="orange")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.close_position_button.config(state=tk.DISABLED)

    def close_position(self):
        """Manually close current position."""
        if self.trader and self.trader._position:
            self.trader.close_position()
            self.update_position(None)

    def update_price(self, price):
        """Update current price display."""
        self.current_price = price
        self.price_label.config(text=f"${price:.5f}")

    def update_signal(self, signal):
        """Update signal information."""
        if signal:
            self.log_analysis(f"Signal: {signal}")

    def update_chart(self, chart_data):
        """Update chart with new analysis data."""
        if chart_data and 'price_data' in chart_data:
            self.chart_data = chart_data

            # Update visualizer
            self.visualizer.update_chart(
                chart_data['price_data'],
                chart_data.get('trendlines', []),
                chart_data.get('patterns', []),
                self.current_position
            )

            # Refresh canvas
            if self.chart_canvas:
                self.chart_canvas.draw()

    def update_position(self, position):
        """Update current position display."""
        self.current_position = position

        self.position_text.config(state=tk.NORMAL)
        self.position_text.delete(1.0, tk.END)

        if position:
            self.position_text.insert(tk.END, f"Type: {position['type'].upper()}\n")
            self.position_text.insert(tk.END, f"Units: {position['units']}\n")
            self.position_text.insert(tk.END, f"Entry Price: ${position['entry_price']:.5f}\n")
            self.position_text.insert(tk.END, f"Time: {position['time']}\n")

            if 'signal' in position:
                signal = position['signal']
                self.position_text.insert(tk.END, f"Signal Strength: {signal.get('strength', 0):.2f}\n")
                self.position_text.insert(tk.END, f"Reasons: {', '.join(signal.get('reasons', []))}\n")
        else:
            self.position_text.insert(tk.END, "No open position")

        self.position_text.config(state=tk.DISABLED)

    def update_history(self, trade):
        """Update trade history."""
        if trade:
            self.trade_history.append(trade)
            self.history_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {trade}\n")
            self.history_text.see(tk.END)

    def log_analysis(self, message):
        """Log analysis information."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.analysis_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.analysis_text.see(tk.END)

def main():
    """Main function to run the GUI."""
    root = tk.Tk()
    app = AdvancedTradingGUI(root)

    # Set up window close handler
    def on_closing():
        if app.trader and app.trader._position:
            if messagebox.askyesno("Close Position", "You have an open position. Close it before exiting?"):
                app.trader.close_position()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
