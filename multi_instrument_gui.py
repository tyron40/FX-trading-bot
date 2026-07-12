import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.gridspec as gridspec
import pandas as pd
from datetime import datetime
from FemtoTrader_trendlines import FemtoTrader

class MultiInstrumentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Instrument Trend-Following Trader")
        self.root.geometry("1600x1000")

        # Initialize trader
        self.trader = None
        self.chart_canvases = {}
        self.instrument_frames = {}

        # Trading data
        self.trend_data = {}
        self.positions = {}
        self.account_balance = 0.0

        # Create GUI components
        self.create_widgets()

        # Start trader in background thread
        self.start_trader()

    def create_widgets(self):
        """Create all GUI widgets."""
        # Main container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Controls and Status
        left_panel = ttk.Frame(main_container)
        main_container.add(left_panel, weight=1)

        # Control panel
        control_frame = ttk.LabelFrame(left_panel, text="Trading Controls", padding=10)
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

        ttk.Label(status_frame, text="Active Positions:").grid(row=0, column=4, sticky=tk.W)
        self.positions_label = ttk.Label(status_frame, text="0")
        self.positions_label.grid(row=0, column=5, sticky=tk.W, padx=(5, 20))

        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        self.start_button = ttk.Button(button_frame, text="Start Trading", command=self.start_trading)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_button = ttk.Button(button_frame, text="Stop Trading", command=self.stop_trading, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))

        self.close_all_button = ttk.Button(button_frame, text="Close All Positions", command=self.close_all_positions, state=tk.DISABLED)
        self.close_all_button.pack(side=tk.LEFT, padx=(0, 10))

        # Instruments status
        instruments_frame = ttk.LabelFrame(left_panel, text="Instrument Status", padding=10)
        instruments_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create instrument status displays
        self.instrument_status = {}
        instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD']

        for i, instrument in enumerate(instruments):
            frame = ttk.Frame(instruments_frame)
            frame.pack(fill=tk.X, pady=2)

            ttk.Label(frame, text=f"{instrument}:", width=10).pack(side=tk.LEFT)

            # Trend indicator
            trend_label = ttk.Label(frame, text="Analyzing...", width=12, anchor=tk.CENTER)
            trend_label.pack(side=tk.LEFT, padx=(5, 0))
            self.instrument_status[instrument] = {
                'trend': trend_label,
                'position': ttk.Label(frame, text="No position", width=15, anchor=tk.CENTER),
                'pnl': ttk.Label(frame, text="$0.00", width=10, anchor=tk.E)
            }
            self.instrument_status[instrument]['position'].pack(side=tk.LEFT, padx=(5, 0))
            self.instrument_status[instrument]['pnl'].pack(side=tk.RIGHT)

        # Activity log
        log_frame = ttk.LabelFrame(left_panel, text="Trading Activity", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.activity_log = scrolledtext.ScrolledText(log_frame, height=15, width=50)
        self.activity_log.pack(fill=tk.BOTH, expand=True)

        # Right panel - Charts
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel, weight=2)

        # Charts container
        charts_frame = ttk.LabelFrame(right_panel, text="Live Charts", padding=10)
        charts_frame.pack(fill=tk.BOTH, expand=True)

        # Create chart grid (2x3 for 5 instruments + summary)
        self.charts_container = ttk.Frame(charts_frame)
        self.charts_container.pack(fill=tk.BOTH, expand=True)

        # Initialize charts will be done after trader starts

    def start_trader(self):
        """Start the trader in background thread."""
        def run_trader():
            try:
                instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD']
                self.trader = FemtoTrader("config/oanda_practice.cfg", instruments=instruments)

                # Set up callbacks
                self.trader.set_gui_callbacks(
                    trend_callback=self.update_trends,
                    position_callback=self.update_positions
                )

                self.status_label.config(text="Connected", foreground="green")
                self.start_button.config(state=tk.NORMAL)

                # Initialize charts
                self.root.after(1000, self.init_charts)

            except Exception as e:
                self.status_label.config(text=f"Error: {str(e)}", foreground="red")
                self.log_activity(f"Connection error: {str(e)}")

        trader_thread = threading.Thread(target=run_trader, daemon=True)
        trader_thread.start()

    def init_charts(self):
        """Initialize charts for all instruments."""
        if not self.trader:
            return

        instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD']

        # Clear existing charts
        for widget in self.charts_container.winfo_children():
            widget.destroy()

        # Create chart grid
        for i, instrument in enumerate(instruments):
            row = i // 3
            col = i % 3

            # Create frame for this instrument
            frame = ttk.LabelFrame(self.charts_container, text=instrument, padding=5)
            frame.grid(row=row, column=col, sticky=tk.NSEW, padx=2, pady=2)

            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=(4, 3))
            fig.patch.set_facecolor('#f0f0f0')
            ax.set_facecolor('#ffffff')

            # Initial empty plot
            ax.plot([], [], 'b-', linewidth=1)
            ax.set_title(f"{instrument} Trend", fontsize=10)
            ax.grid(True, alpha=0.3)

            # Create canvas
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            self.chart_canvases[instrument] = {
                'fig': fig,
                'ax': ax,
                'canvas': canvas
            }

        # Configure grid weights
        self.charts_container.grid_rowconfigure(0, weight=1)
        self.charts_container.grid_rowconfigure(1, weight=1)
        for i in range(3):
            self.charts_container.grid_columnconfigure(i, weight=1)

    def start_trading(self):
        """Start automated trading."""
        if self.trader:
            self.status_label.config(text="Trading Active", foreground="green")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.close_all_button.config(state=tk.NORMAL)

            # Start trading in background thread
            def trading_loop():
                try:
                    self.trader.run()
                except Exception as e:
                    self.log_activity(f"Trading error: {str(e)}")

            trading_thread = threading.Thread(target=trading_loop, daemon=True)
            trading_thread.start()

    def stop_trading(self):
        """Stop automated trading."""
        if self.trader:
            self.status_label.config(text="Trading Stopped", foreground="orange")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.close_all_button.config(state=tk.DISABLED)

    def close_all_positions(self):
        """Close all open positions."""
        if self.trader:
            for instrument in list(self.trader._positions.keys()):
                self.trader._close_position(instrument)
            self.update_positions({})

    def update_trends(self, trend_data):
        """Update trend information for all instruments."""
        self.trend_data = trend_data

        for instrument, data in trend_data.items():
            if instrument in self.instrument_status:
                # Update trend display
                direction = data.get('direction', 0)
                strength = data.get('strength', 0)

                if direction > 0:
                    trend_text = f"UP ({strength:.2f})"
                    color = "green"
                elif direction < 0:
                    trend_text = f"DOWN ({strength:.2f})"
                    color = "red"
                else:
                    trend_text = f"SIDE ({strength:.2f})"
                    color = "gray"

                self.instrument_status[instrument]['trend'].config(text=trend_text, foreground=color)

                # Update chart
                self.update_instrument_chart(instrument, data)

    def update_positions(self, positions):
        """Update position information."""
        self.positions = positions
        self.positions_label.config(text=str(len(positions)))

        # Reset all position displays
        for instrument in self.instrument_status:
            self.instrument_status[instrument]['position'].config(text="No position", foreground="black")
            self.instrument_status[instrument]['pnl'].config(text="$0.00", foreground="black")

        # Update active positions
        for instrument, position in positions.items():
            if instrument in self.instrument_status:
                position_type = position['type'].upper()
                profit_pct = position.get('profit_pct', 0)

                self.instrument_status[instrument]['position'].config(
                    text=f"{position_type} ({position['units']}u)",
                    foreground="green" if position_type == "LONG" else "red"
                )

                pnl_color = "green" if profit_pct > 0 else "red" if profit_pct < 0 else "black"
                self.instrument_status[instrument]['pnl'].config(
                    text=f"{profit_pct:+.2f}%",
                    foreground=pnl_color
                )

    def update_instrument_chart(self, instrument, trend_data):
        """Update chart for a specific instrument."""
        if instrument not in self.chart_canvases:
            return

        chart_info = self.chart_canvases[instrument]
        ax = chart_info['ax']

        # Clear previous plot
        ax.clear()

        # Get chart data from trader
        chart_data = self.trader._chart_data.get(instrument)
        if chart_data is not None and len(chart_data) > 0:
            # Plot price data
            ax.plot(chart_data.index, chart_data['close'], 'b-', linewidth=1, alpha=0.7)

            # Plot trendlines
            trendlines = trend_data.get('analysis', {}).get('trendlines', [])
            for line in trendlines:
                if line['strength'] >= 3:  # Only strong trendlines
                    slope = line['slope']
                    intercept = line['intercept']

                    # Calculate trendline points
                    x_points = range(len(chart_data))
                    y_points = [slope * x + intercept for x in x_points]

                    color = 'green' if line['type'] == 'support' else 'red'
                    linestyle = '-' if line['strength'] >= 4 else '--'
                    ax.plot(chart_data.index, y_points, color=color, linestyle=linestyle,
                           linewidth=1, alpha=0.8, label=f"{line['type']} ({line['strength']})")

            # Add current position marker if exists
            if instrument in self.positions:
                position = self.positions[instrument]
                color = 'green' if position['type'] == 'long' else 'red'
                ax.axhline(y=position['entry_price'], color=color, linestyle='--',
                          linewidth=2, alpha=0.7, label=f"Entry: {position['entry_price']:.5f}")

        # Format chart
        ax.set_title(f"{instrument} Trend", fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', which='major', labelsize=8)

        # Rotate x-axis labels
        plt.setp(ax.get_xticklabels(), rotation=45)

        # Refresh canvas
        chart_info['canvas'].draw()

    def log_activity(self, message):
        """Log activity to the activity log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.activity_log.see(tk.END)

def main():
    """Main function to run the multi-instrument GUI."""
    root = tk.Tk()
    app = MultiInstrumentGUI(root)

    # Set up window close handler
    def on_closing():
        if app.trader:
            app.log_activity("Closing all positions...")
            for instrument in list(app.trader._positions.keys()):
                app.trader._close_position(instrument)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
