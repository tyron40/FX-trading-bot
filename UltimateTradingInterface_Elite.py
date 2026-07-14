"""
Perfect Ultimate Trading Interface
- Full dashboard (charts + right-side panels)
- Mode selector (Faster/Balanced/Safer)
- Automated exits (SL/TP + trailing protection + max hold)
- Stop button can close all bot-managed positions
- tpqoa-compatible broker-side protection (sl_distance, tp_price, tsl_distance)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime
import pandas as pd
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tpqoa.tpqoa import tpqoa


COLORS = {
    "bg": "#1e1e2e",
    "fg": "#cdd6f4",
    "accent": "#89b4fa",
    "success": "#a6e3a1",
    "warning": "#f9e2af",
    "error": "#f38ba8",
    "buy": "#a6e3a1",
    "sell": "#f38ba8",
    "panel": "#313244",
    "hover": "#45475a",
}


class PerfectTrader(tpqoa):
    def __init__(self, config_path, timeframe="M5", risk_pct=1.0):
        super().__init__(config_path)
        self.timeframe = timeframe
        self.risk_pct = risk_pct / 100.0
        self.strategy_mode = "Balanced"
        self.instruments = ["EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF", "AUD_USD"]

        self.positions = {}
        self.trades = []
        self.closed_trades = []

        self.balance = 10000.0
        self.currency = "USD"
        self.nav = 0.0
        self.unrealized_pl = 0.0
        self.margin_used = 0.0
        self.margin_available = 0.0

        self.update_account_info()

    def update_account_info(self):
        try:
            summary = self.get_account_summary(detailed=True)
            self.balance = float(summary.get("balance", 10000.0))
            self.currency = summary.get("currency", "USD")
            self.nav = float(summary.get("NAV", self.balance))
            self.unrealized_pl = float(summary.get("unrealizedPL", 0.0))
            self.margin_used = float(summary.get("marginUsed", 0.0))
            self.margin_available = float(summary.get("marginAvailable", self.balance))
            return True
        except Exception as e:
            print(f"Could not get account info: {e}")
            return False

    def get_live_data(self, instrument, count=120):
        try:
            response = self.ctx.instrument.candles(
                instrument,
                granularity=self.timeframe,
                count=count,
                price="MBA",
            )
            if response.status != 200:
                return None

            rows = []
            for c in response.body.get("candles", []):
                rows.append(
                    {
                        "time": pd.to_datetime(c.time),
                        "open": float(c.mid.o),
                        "high": float(c.mid.h),
                        "low": float(c.mid.l),
                        "close": float(c.mid.c),
                        "volume": int(c.volume),
                    }
                )

            df = pd.DataFrame(rows)
            if df.empty:
                return None
            df.set_index("time", inplace=True)
            return df
        except Exception as e:
            print(f"Data error: {e}")
            return None

    def analyze_fast(self, df):
        if df is None or len(df) < 60:
            return {"signal": "HOLD", "score": 0.0, "indicators": {}}

        df = df.copy()
        df["sma_20"] = df["close"].rolling(20).mean()
        df["sma_50"] = df["close"].rolling(50).mean()

        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

        df["bb_mid"] = df["close"].rolling(20).mean()
        df["bb_std"] = df["close"].rolling(20).std()
        df["bb_upper"] = df["bb_mid"] + 2 * df["bb_std"]
        df["bb_lower"] = df["bb_mid"] - 2 * df["bb_std"]

        latest = df.iloc[-1]
        score = 0.0
        indicators = {}

        if latest["sma_20"] > latest["sma_50"]:
            score += 0.3
            indicators["trend"] = "UP"
        else:
            score -= 0.3
            indicators["trend"] = "DOWN"

        if latest["rsi"] < 30:
            score += 0.4
            indicators["rsi"] = "OVERSOLD"
        elif latest["rsi"] > 70:
            score -= 0.4
            indicators["rsi"] = "OVERBOUGHT"
        else:
            indicators["rsi"] = "NEUTRAL"

        if latest["close"] < latest["bb_lower"]:
            score += 0.3
            indicators["bb"] = "BELOW_LOWER"
        elif latest["close"] > latest["bb_upper"]:
            score -= 0.3
            indicators["bb"] = "ABOVE_UPPER"
        else:
            indicators["bb"] = "NEUTRAL"

        trend_up = indicators["trend"] == "UP"
        trend_down = indicators["trend"] == "DOWN"

        thresholds = {"Faster": 0.35, "Balanced": 0.60, "Safer": 0.75}
        th = thresholds.get(self.strategy_mode, 0.60)

        signal = "HOLD"
        if self.strategy_mode == "Faster":
            if score > th and trend_up:
                signal = "BUY"
            elif score < -th and trend_down:
                signal = "SELL"
            elif trend_up and latest["close"] > latest["sma_20"] and latest["rsi"] < 72 and score > 0.20:
                signal = "BUY"
            elif trend_down and latest["close"] < latest["sma_20"] and latest["rsi"] > 28 and score < -0.20:
                signal = "SELL"
        elif self.strategy_mode == "Safer":
            if score > th and trend_up and latest["rsi"] < 65:
                signal = "BUY"
            elif score < -th and trend_down and latest["rsi"] > 35:
                signal = "SELL"
        else:
            if score > th and trend_up and latest["rsi"] < 70:
                signal = "BUY"
            elif score < -th and trend_down and latest["rsi"] > 30:
                signal = "SELL"

        return {
            "signal": signal,
            "score": float(score),
            "indicators": indicators,
            "price": float(latest["close"]),
            "rsi": float(latest["rsi"]),
        }

    def calculate_position_size(self, price):
        risk_amount = self.balance * self.risk_pct
        stop_dist = max(price * 0.008, 1e-6)
        units = int(risk_amount / stop_dist)
        return max(100, min(units, 10000))

    def execute_trade(self, instrument, signal):
        try:
            _, bid, ask = self.get_prices(instrument)
            sl_tp = {
                "Faster": (0.007, 0.010),
                "Balanced": (0.008, 0.012),
                "Safer": (0.006, 0.015),
            }
            sl_pct, tp_pct = sl_tp.get(self.strategy_mode, (0.008, 0.012))

            trailing_distance_by_mode = {
                "Faster": 0.0012,
                "Balanced": None,
                "Safer": None,
            }
            tsl_pct = trailing_distance_by_mode.get(self.strategy_mode, None)

            if signal == "BUY":
                entry = ask
                units = self.calculate_position_size(entry)
                direction = "LONG"
                stop_loss = entry * (1 - sl_pct)
                take_profit = entry * (1 + tp_pct)
                signed_units = units
            elif signal == "SELL":
                entry = bid
                units = self.calculate_position_size(entry)
                direction = "SHORT"
                stop_loss = entry * (1 + sl_pct)
                take_profit = entry * (1 - tp_pct)
                signed_units = -units
            else:
                return None

            order_kwargs = {
                "sl_distance": float(abs(entry - stop_loss)),
                "tp_price": float(take_profit),
            }
            if tsl_pct is not None:
                order_kwargs["tsl_distance"] = float(entry * tsl_pct)

            order = self.create_order(
                instrument,
                signed_units,
                suppress=True,
                ret=True,
                **order_kwargs
            )

            if not order:
                return None

            trade = {
                "instrument": instrument,
                "direction": direction,
                "units": units,
                "entry_price": float(order.get("price", entry)),
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "trailing_stop_distance": float(entry * tsl_pct) if tsl_pct else None,
                "entry_time": datetime.now(),
                "status": "OPEN",
                "peak_price": float(entry),
                "trough_price": float(entry),
                "order_id": order.get("id"),
                "tp_order_id": order.get("tpOrder", {}).get("id") if isinstance(order.get("tpOrder"), dict) else None,
                "sl_order_id": order.get("slOrder", {}).get("id") if isinstance(order.get("slOrder"), dict) else None,
                "tsl_order_id": order.get("tslOrder", {}).get("id") if isinstance(order.get("tslOrder"), dict) else None,
            }

            self.positions[instrument] = trade
            self.trades.append(trade)
            return trade
        except Exception as e:
            print(f"Trade execution error: {e}")
            return None

    def check_exit_conditions(self, instrument):
        if instrument not in self.positions:
            return
        try:
            pos = self.positions[instrument]
            _, bid, ask = self.get_prices(instrument)
            current = bid if pos["direction"] == "LONG" else ask
            if pos["direction"] == "LONG":
                if current <= pos["stop_loss"] or current >= pos["take_profit"]:
                    self.close_position(instrument)
            else:
                if current >= pos["stop_loss"] or current <= pos["take_profit"]:
                    self.close_position(instrument)
        except Exception:
            pass

    def close_position(self, instrument):
        if instrument not in self.positions:
            return None
        try:
            pos = self.positions[instrument]
            units = pos["units"]
            if pos["direction"] == "LONG":
                order = self.create_order(instrument, -units, suppress=True, ret=True)
            else:
                order = self.create_order(instrument, units, suppress=True, ret=True)

            if not order:
                return None

            pnl = float(order.get("pl", 0))
            pos["exit_price"] = float(order.get("price", 0))
            pos["exit_time"] = datetime.now()
            pos["pnl"] = pnl
            pos["status"] = "CLOSED"
            self.closed_trades.append(pos.copy())
            del self.positions[instrument]
            self.update_account_info()
            return pos
        except Exception as e:
            print(f"Close error: {e}")
            return None

    def is_market_open(self):
        return datetime.now().weekday() < 5


class PerfectTradingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 FX Trading Bot - Perfect Edition")
        self.root.geometry("1900x1000")
        self.root.configure(bg=COLORS["bg"])

        self.trader = None
        self.trading_active = False
        self.market_data = {}
        self.analysis_results = {}
        self.signal_strengths = {}
        self.close_all_on_stop = tk.BooleanVar(value=True)

        self.setup_style()
        self.create_gui()
        self.connect_account("demo")
        self.start_updates()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["fg"])
        style.configure("TLabelframe", background=COLORS["bg"], foreground=COLORS["accent"])
        style.configure("TLabelframe.Label", background=COLORS["bg"], foreground=COLORS["accent"])
        style.configure("Success.TButton", background=COLORS["success"], foreground=COLORS["bg"])
        style.configure("Error.TButton", background=COLORS["error"], foreground=COLORS["bg"])

    def create_gui(self):
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top, text="Account:").pack(side=tk.LEFT, padx=4)
        self.account_var = tk.StringVar(value="demo")
        ttk.Radiobutton(top, text="Demo", variable=self.account_var, value="demo", command=lambda: self.connect_account("demo")).pack(side=tk.LEFT)
        ttk.Radiobutton(top, text="Live", variable=self.account_var, value="live", command=lambda: self.connect_account("live")).pack(side=tk.LEFT)

        self.start_btn = ttk.Button(top, text="▶ START", style="Success.TButton", command=self.start_trading)
        self.start_btn.pack(side=tk.LEFT, padx=8)
        self.stop_btn = ttk.Button(top, text="■ STOP", style="Error.TButton", command=self.stop_trading, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=4)

        ttk.Checkbutton(top, text="Close all positions on STOP", variable=self.close_all_on_stop).pack(side=tk.LEFT, padx=8)

        ttk.Label(top, text="Timeframe:").pack(side=tk.LEFT, padx=4)
        self.timeframe_var = tk.StringVar(value="M5")
        ttk.Combobox(top, textvariable=self.timeframe_var, values=["M1", "M5", "M15", "M30", "H1", "H4"], state="readonly", width=6).pack(side=tk.LEFT)

        ttk.Label(top, text="Mode:").pack(side=tk.LEFT, padx=4)
        self.mode_var = tk.StringVar(value="Balanced")
        ttk.Combobox(top, textvariable=self.mode_var, values=["Faster", "Balanced", "Safer"], state="readonly", width=10).pack(side=tk.LEFT)

        ttk.Label(top, text="Risk %:").pack(side=tk.LEFT, padx=4)
        self.risk_var = tk.DoubleVar(value=1.0)
        tk.Spinbox(top, from_=0.5, to=5.0, increment=0.5, textvariable=self.risk_var, width=5).pack(side=tk.LEFT)

        self.status_label = ttk.Label(top, text="Initializing...", foreground=COLORS["warning"])
        self.status_label.pack(side=tk.RIGHT)

        content = ttk.Frame(self.root)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        left = ttk.Frame(content)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        charts_box = ttk.LabelFrame(left, text="LIVE CHARTS")
        charts_box.pack(fill=tk.BOTH, expand=True)

        self.chart_notebook = ttk.Notebook(charts_box)
        self.chart_notebook.pack(fill=tk.BOTH, expand=True)

        self.charts = {}
        for inst in ["EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF", "AUD_USD"]:
            tab = ttk.Frame(self.chart_notebook)
            self.chart_notebook.add(tab, text=inst.replace("_", "/"))
            fig = Figure(figsize=(8, 4), facecolor=COLORS["bg"])
            ax = fig.add_subplot(111, facecolor=COLORS["panel"])
            canvas = FigureCanvasTkAgg(fig, tab)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.charts[inst] = {"fig": fig, "ax": ax, "canvas": canvas}

        log_box = ttk.LabelFrame(left, text="ANALYSIS LOG")
        log_box.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        self.log_text = scrolledtext.ScrolledText(log_box, height=8, bg=COLORS["panel"], fg=COLORS["fg"])
        self.log_text.pack(fill=tk.BOTH, expand=True)

        right = ttk.Frame(content, width=420)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)

        account_box = ttk.LabelFrame(right, text="ACCOUNT INFO")
        account_box.pack(fill=tk.X, pady=(0, 8))
        self.balance_label = ttk.Label(account_box, text="Balance: --")
        self.balance_label.pack(anchor="w")
        self.nav_label = ttk.Label(account_box, text="NAV: --")
        self.nav_label.pack(anchor="w")
        self.upl_label = ttk.Label(account_box, text="Unrealized P&L: --")
        self.upl_label.pack(anchor="w")
        self.margin_label = ttk.Label(account_box, text="Margin Used: --")
        self.margin_label.pack(anchor="w")
        self.market_label = ttk.Label(account_box, text="Market: --")
        self.market_label.pack(anchor="w")

        signal_box = ttk.LabelFrame(right, text="SIGNAL STRENGTH")
        signal_box.pack(fill=tk.X, pady=(0, 8))
        self.signal_widgets = {}
        for inst in ["EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF", "AUD_USD"]:
            row = ttk.Frame(signal_box)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=inst.replace("_", "/"), width=10).pack(side=tk.LEFT)
            bar = ttk.Progressbar(row, length=140, mode="determinate")
            bar.pack(side=tk.LEFT, padx=4)
            txt = ttk.Label(row, text="HOLD", width=6)
            txt.pack(side=tk.RIGHT)
            self.signal_widgets[inst] = (bar, txt)

        pos_box = ttk.LabelFrame(right, text="OPEN POSITIONS")
        pos_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        self.pos_text = scrolledtext.ScrolledText(pos_box, height=8, bg=COLORS["panel"], fg=COLORS["fg"])
        self.pos_text.pack(fill=tk.BOTH, expand=True)

        perf_box = ttk.LabelFrame(right, text="PERFORMANCE")
        perf_box.pack(fill=tk.X, pady=(0, 8))
        self.perf_total = ttk.Label(perf_box, text="Total Trades: 0")
        self.perf_total.pack(anchor="w")
        self.perf_win = ttk.Label(perf_box, text="Win Rate: 0.0%")
        self.perf_win.pack(anchor="w")
        self.perf_pnl = ttk.Label(perf_box, text="Total P&L: $0.00")
        self.perf_pnl.pack(anchor="w")

        hist_box = ttk.LabelFrame(right, text="TRADE HISTORY")
        hist_box.pack(fill=tk.BOTH, expand=True)
        self.history_text = scrolledtext.ScrolledText(hist_box, height=8, bg=COLORS["panel"], fg=COLORS["fg"])
        self.history_text.pack(fill=tk.BOTH, expand=True)

    def connect_account(self, account_type):
        self.status_label.config(text=f"Connecting {account_type.upper()}...", foreground=COLORS["warning"])

        def _connect():
            try:
                cfg = f"config/oanda_{account_type}.cfg"
                self.trader = PerfectTrader(cfg, self.timeframe_var.get(), self.risk_var.get())
                self.status_label.config(text=f"{account_type.upper()} Connected", foreground=COLORS["success"])
                self.log(f"Connected to {account_type.upper()} account")
            except Exception as e:
                self.status_label.config(text="Connection failed", foreground=COLORS["error"])
                self.log(f"Connection error: {e}")

        threading.Thread(target=_connect, daemon=True).start()

    def start_trading(self):
        if not self.trader:
            messagebox.showwarning("Warning", "Connect account first")
            return
        self.trading_active = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="TRADING ACTIVE", foreground=COLORS["success"])
        self.log("Trading started")
        threading.Thread(target=self.trading_loop, daemon=True).start()

    def stop_trading(self):
        self.trading_active = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        if self.close_all_on_stop.get() and self.trader:
            for inst in list(self.trader.positions.keys()):
                self.trader.close_position(inst)
        self.status_label.config(text="STOPPED", foreground=COLORS["warning"])
        self.log("Trading stopped")

    def manage_open_positions(self):
        if not self.trader:
            return
        max_hold_by_mode = {"Faster": 12 * 60, "Balanced": 35 * 60, "Safer": 60 * 60}
        max_hold = max_hold_by_mode.get(self.mode_var.get(), 35 * 60)

        for inst in list(self.trader.positions.keys()):
            pos = self.trader.positions.get(inst)
            if not pos:
                continue
            try:
                _, bid, ask = self.trader.get_prices(inst)
                current = bid if pos["direction"] == "LONG" else ask
                entry = pos["entry_price"]

                if pos["direction"] == "LONG":
                    pos["peak_price"] = max(pos.get("peak_price", entry), current)
                    if self.mode_var.get() == "Faster":
                        locked_profit_trigger = entry * 1.0018
                        trail_factor = 0.9988
                    else:
                        locked_profit_trigger = entry * 1.003
                        trail_factor = 0.998
                    if pos["peak_price"] > locked_profit_trigger:
                        trail = pos["peak_price"] * trail_factor
                        pos["stop_loss"] = max(pos["stop_loss"], trail)
                else:
                    pos["trough_price"] = min(pos.get("trough_price", entry), current)
                    if self.mode_var.get() == "Faster":
                        locked_profit_trigger = entry * 0.9982
                        trail_factor = 1.0012
                    else:
                        locked_profit_trigger = entry * 0.997
                        trail_factor = 1.002
                    if pos["trough_price"] < locked_profit_trigger:
                        trail = pos["trough_price"] * trail_factor
                        pos["stop_loss"] = min(pos["stop_loss"], trail)

                held_seconds = (datetime.now() - pos["entry_time"]).total_seconds()
                if held_seconds > max_hold:
                    self.log(f"Time-exit triggered for {inst}")
                    self.trader.close_position(inst)
                    continue

                self.trader.check_exit_conditions(inst)
            except Exception as e:
                self.log(f"Position manage error {inst}: {e}")

    def trading_loop(self):
        while self.trading_active and self.trader:
            try:
                if not self.trader.is_market_open():
                    self.log("Market closed")
                    time.sleep(30)
                    continue

                self.trader.strategy_mode = self.mode_var.get()
                self.trader.timeframe = self.timeframe_var.get()
                self.trader.risk_pct = self.risk_var.get() / 100.0

                self.manage_open_positions()

                for inst in self.trader.instruments:
                    df = self.trader.get_live_data(inst, 120)
                    if df is None:
                        continue
                    self.market_data[inst] = df
                    analysis = self.trader.analyze_fast(df)
                    self.analysis_results[inst] = analysis
                    self.signal_strengths[inst] = analysis["score"]

                    self.log(f"{inst} score={analysis['score']:+.2f} signal={analysis['signal']} mode={self.mode_var.get()}")

                    if analysis["signal"] in ("BUY", "SELL") and inst not in self.trader.positions:
                        trade = self.trader.execute_trade(inst, analysis["signal"])
                        if trade:
                            has_sl = "YES" if trade.get("sl_order_id") else "NO"
                            has_tp = "YES" if trade.get("tp_order_id") else "NO"
                            has_ts = "YES" if trade.get("tsl_order_id") else "NO"
                            self.log(
                                f"{inst} {analysis['signal']} opened @ {trade['entry_price']:.5f} "
                                f"[OANDA SL:{has_sl} TP:{has_tp} TS:{has_ts}]"
                            )

                self.trader.update_account_info()
                interval = {"Faster": 8, "Balanced": 12, "Safer": 18}.get(self.mode_var.get(), 12)
                time.sleep(interval)
            except Exception as e:
                self.log(f"Trading loop error: {e}")
                time.sleep(5)

    def start_updates(self):
        def loop():
            while True:
                try:
                    self.update_dashboard()
                    self.update_charts()
                except Exception:
                    pass
                time.sleep(2)

        threading.Thread(target=loop, daemon=True).start()

    def update_dashboard(self):
        if not self.trader:
            return
        self.balance_label.config(text=f"Balance: ${self.trader.balance:,.2f}")
        self.nav_label.config(text=f"NAV: ${self.trader.nav:,.2f}")
        self.upl_label.config(text=f"Unrealized P&L: ${self.trader.unrealized_pl:+,.2f}")
        self.margin_label.config(text=f"Margin Used: ${self.trader.margin_used:,.2f}")
        self.market_label.config(text=f"Market: {'OPEN' if self.trader.is_market_open() else 'CLOSED'}")

        for inst, (bar, txt) in self.signal_widgets.items():
            score = float(self.signal_strengths.get(inst, 0.0))
            bar["value"] = max(0, min(100, (score + 1) * 50))
            if score > 0.5:
                txt.config(text="BUY")
            elif score < -0.5:
                txt.config(text="SELL")
            else:
                txt.config(text="HOLD")

        self.pos_text.delete("1.0", tk.END)
        for inst, pos in self.trader.positions.items():
            self.pos_text.insert(
                tk.END,
                f"{inst} {pos['direction']}\nEntry: {pos['entry_price']:.5f}\n"
                f"SL: {pos['stop_loss']:.5f}  TP: {pos['take_profit']:.5f}\n\n",
            )

        closed = self.trader.closed_trades
        total = len(closed)
        wins = len([t for t in closed if t.get("pnl", 0) > 0])
        pnl = sum(t.get("pnl", 0) for t in closed)
        win_rate = (wins / total * 100) if total else 0.0
        self.perf_total.config(text=f"Total Trades: {total}")
        self.perf_win.config(text=f"Win Rate: {win_rate:.1f}%")
        self.perf_pnl.config(text=f"Total P&L: ${pnl:+.2f}")

        self.history_text.delete("1.0", tk.END)
        for t in reversed(closed[-12:]):
            self.history_text.insert(
                tk.END,
                f"[{t['exit_time'].strftime('%H:%M:%S')}] {t['instrument']} {t['direction']} "
                f"P&L ${t.get('pnl',0):+.2f}\n",
            )

    def update_charts(self):
        for inst, ch in self.charts.items():
            df = self.market_data.get(inst)
            if df is None or df.empty:
                continue

            plot_df = df.copy()
            plot_df["sma_20"] = plot_df["close"].rolling(20).mean()
            plot_df["sma_50"] = plot_df["close"].rolling(50).mean()

            ax = ch["ax"]
            ax.clear()

            ax.plot(plot_df.index, plot_df["close"], color=COLORS["accent"], linewidth=1.4, label="Price")

            if plot_df["sma_20"].notna().any():
                ax.plot(plot_df.index, plot_df["sma_20"], color=COLORS["success"], linewidth=1.2, alpha=0.9, label="SMA 20")
            if plot_df["sma_50"].notna().any():
                ax.plot(plot_df.index, plot_df["sma_50"], color=COLORS["warning"], linewidth=1.2, alpha=0.9, label="SMA 50")

            recent = plot_df.tail(40).dropna(subset=["close"])
            if len(recent) >= 5:
                y = recent["close"].values
                x = np.arange(len(y))
                m, b = np.polyfit(x, y, 1)
                trend_y = m * x + b
                ax.plot(recent.index, trend_y, color="#ff9e64", linewidth=1.4, linestyle="--", label="Trendline")

            if self.trader and inst in self.trader.positions:
                p = self.trader.positions[inst]
                entry = p.get("entry_price")
                if entry:
                    marker_color = COLORS["buy"] if p.get("direction") == "LONG" else COLORS["sell"]
                    ax.axhline(entry, color=marker_color, linestyle=":", linewidth=1.1, alpha=0.8, label="Entry")

            if self.trader:
                closed = [t for t in self.trader.closed_trades if t.get("instrument") == inst and t.get("exit_price") is not None]
                if closed:
                    last_closed = closed[-1]
                    ax.axhline(last_closed["exit_price"], color="#cba6f7", linestyle=":", linewidth=1.0, alpha=0.7, label="Last Exit")

            ax.set_title(inst.replace("_", "/"), color=COLORS["fg"])
            ax.grid(True, alpha=0.25)
            ax.legend(loc="upper left", fontsize=8, framealpha=0.25)
            ch["canvas"].draw()

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_text.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = PerfectTradingGUI(root)
    root.mainloop()
