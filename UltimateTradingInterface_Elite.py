"""
Elite Ultimate Trading Interface (Phase 1 safety gates)

Implemented:
- centralized validate_entry()
- closed-candle-only validation
- spread/session/rollover/regime gating
- NAV+stop risk sizing + margin/invalid-order guards
- decision logging to logs/trade_decisions.csv
- UI rejection logging
- offline --smoke-test mode
"""

import argparse
import csv
import os
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime, time as dt_time

import pandas as pd
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
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

DECISION_FIELDS = [
    "timestamp", "instrument", "signal", "accepted", "reason", "regime",
    "spread_pips", "entry", "stop_loss", "take_profit", "units",
    "margin_available", "mode", "score"
]


@dataclass
class OrderProposal:
    instrument: str
    side: str
    entry: float
    stop_loss: float
    take_profit: float
    units: int
    risk_amount: float
    estimated_loss: float
    required_margin: float
    spread_pips: float
    regime: str


@dataclass
class ValidationResult:
    allowed: bool
    reason: str


@dataclass
class InstrumentMeta:
    name: str
    base: str
    quote: str
    pip_location: int
    display_precision: int
    margin_rate: float
    minimum_trade_size: int


class EliteTrader(tpqoa):
    def __init__(self, config_path, timeframe="M5", risk_pct=1.0, smoke_test=False):
        self.smoke_test = smoke_test
        if not self.smoke_test:
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
        self.nav = 10000.0
        self.unrealized_pl = 0.0
        self.margin_used = 0.0
        self.margin_available = 10000.0

        self.spread_limits = {
            "EUR_USD": 1.5, "USD_JPY": 1.8, "GBP_USD": 2.0, "AUD_USD": 1.8, "USD_CHF": 2.0
        }
        # Phase-1/2 portfolio safety state. Values are intentionally conservative;
        # users can tune them after validating on an OANDA practice account.
        self.instrument_meta: Dict[str, InstrumentMeta] = {}
        self.max_open_positions = 5
        self.max_currency_positions = 2
        self.margin_buffer = 0.50
        self.max_daily_drawdown = 0.05
        self.max_peak_drawdown = 0.10
        self.session_start_nav = self.nav
        self.peak_nav = self.nav

        self.log_dir = "logs"
        self.decisions_path = os.path.join(self.log_dir, "trade_decisions.csv")
        self._init_decision_log()

        self.update_account_info()
        if not self.smoke_test:
            self.refresh_instruments()

    def _init_decision_log(self):
        os.makedirs(self.log_dir, exist_ok=True)
        if not os.path.exists(self.decisions_path):
            with open(self.decisions_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=DECISION_FIELDS)
                writer.writeheader()

    def _log_decision(self, row):
        with open(self.decisions_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=DECISION_FIELDS)
            writer.writerow({k: row.get(k, "") for k in DECISION_FIELDS})

    def _decision_row(self, instrument, signal, accepted, reason, regime, spread_pips, score,
                      entry="", stop_loss="", take_profit="", units=""):
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "instrument": instrument,
            "signal": signal,
            "accepted": bool(accepted),
            "reason": reason,
            "regime": regime,
            "spread_pips": spread_pips,
            "entry": entry,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "units": units,
            "margin_available": self.margin_available,
            "mode": self.strategy_mode,
            "score": score
        }

    def update_account_info(self):
        if self.smoke_test:
            self.balance = 10000.0
            self.nav = 10000.0
            self.margin_available = 10000.0
            self.margin_used = 0.0
            self.unrealized_pl = 0.0
            return True
        try:
            summary = self.get_account_summary(detailed=True)
            self.balance = float(summary.get("balance", 10000.0))
            self.currency = summary.get("currency", "USD")
            self.nav = float(summary.get("NAV", self.balance))
            self.unrealized_pl = float(summary.get("unrealizedPL", 0.0))
            self.margin_used = float(summary.get("marginUsed", 0.0))
            self.margin_available = float(summary.get("marginAvailable", self.balance))
            if self.session_start_nav <= 0:
                self.session_start_nav = self.nav
            self.peak_nav = max(self.peak_nav, self.nav)
            return True
        except Exception as e:
            print(f"Could not get account info: {e}")
            return False

    def refresh_instruments(self):
        fx = []
        try:
            instruments = self.get_instruments()
            for ins in instruments:
                if isinstance(ins, (list, tuple)):
                    name = str(ins[1]) if len(ins) > 1 else ""
                    typ = str(ins[2]).upper() if len(ins) > 2 else ""
                else:
                    name = str(getattr(ins, "name", ""))
                    typ = str(getattr(ins, "type", "")).upper()
                if "_" in name and ("CURRENCY" in typ or typ == ""):
                    fx.append(name)
                    base, quote = name.split("_", 1)
                    try:
                        # tpqoa exposes OANDA instrument rows as tuples. Keep safe
                        # defaults for older tpqoa versions with shorter rows.
                        display_precision = int(ins[3]) if isinstance(ins, (list, tuple)) and len(ins) > 3 else (3 if "JPY" in name else 5)
                        pip_location = int(ins[4]) if isinstance(ins, (list, tuple)) and len(ins) > 4 else (-2 if quote == "JPY" else -4)
                        minimum_trade_size = int(float(ins[6])) if isinstance(ins, (list, tuple)) and len(ins) > 6 else 1
                        margin_rate = float(ins[11]) if isinstance(ins, (list, tuple)) and len(ins) > 11 else 0.05
                    except (TypeError, ValueError, IndexError):
                        display_precision = 3 if quote == "JPY" else 5
                        pip_location = -2 if quote == "JPY" else -4
                        minimum_trade_size = 1
                        margin_rate = 0.05
                    self.instrument_meta[name] = InstrumentMeta(
                        name=name, base=base, quote=quote,
                        pip_location=pip_location,
                        display_precision=display_precision,
                        margin_rate=margin_rate,
                        minimum_trade_size=minimum_trade_size,
                    )
            fx = sorted(set(fx))
            if fx:
                self.instruments = fx
                return self.instruments
        except Exception:
            pass
        return self.instruments

    def get_live_data(self, instrument, count=120):
        if self.smoke_test:
            idx = pd.date_range(end=pd.Timestamp.utcnow(), periods=count, freq="5min")
            base = 1.10 if "JPY" not in instrument else 150.0
            closes = [base + (i * 0.0001) for i in range(count)]
            if "JPY" in instrument:
                closes = [base + (i * 0.01) for i in range(count)]
            df = pd.DataFrame({
                "open": closes,
                "high": [c * 1.0005 for c in closes],
                "low": [c * 0.9995 for c in closes],
                "close": closes,
                "volume": [100] * count,
                "complete": [True] * count
            }, index=idx)
            return df

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
                        "complete": bool(getattr(c, "complete", False)),
                    }
                )
            df = pd.DataFrame(rows)
            if df.empty:
                return None
            df.set_index("time", inplace=True)
            return df
        except Exception:
            return None

    def _closed_candles(self, df):
        if df is None or len(df) < 2:
            return None
        d = df.copy()
        if "complete" in d.columns:
            d = d[d["complete"] == True]
        else:
            d = d.iloc[:-1]
        return d if d is not None and len(d) > 0 else None

    def detect_regime(self, df):
        d = self._closed_candles(df)
        if d is None or len(d) < 60:
            return "UNCERTAIN"

        d["ema_50"] = d["close"].ewm(span=50, adjust=False).mean()
        d["ema_200"] = d["close"].ewm(span=200, adjust=False).mean()
        d["ret"] = d["close"].pct_change()

        latest = d.iloc[-1]
        vol = d["ret"].rolling(20).std().iloc[-1]
        ema_gap = abs(latest["ema_50"] - latest["ema_200"]) / max(latest["close"], 1e-8)
        bb_mid = d["close"].rolling(20).mean().iloc[-1]
        bb_std = d["close"].rolling(20).std().iloc[-1]
        bb_width = (4 * bb_std / bb_mid) if bb_mid and bb_mid > 0 else 0.0

        if ema_gap > 0.0015 and vol > 0.0005:
            return "TRENDING"
        if ema_gap < 0.0007 and bb_width < 0.01:
            return "RANGING"
        return "UNCERTAIN"

    def analyze_fast(self, df):
        d = self._closed_candles(df)
        if d is None or len(d) < 60:
            return {"signal": "HOLD", "score": 0.0, "indicators": {}, "reason": "insufficient_closed_candles"}

        d["sma_20"] = d["close"].rolling(20).mean()
        d["sma_50"] = d["close"].rolling(50).mean()
        delta = d["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        d["rsi"] = 100 - (100 / (1 + rs))

        d["bb_mid"] = d["close"].rolling(20).mean()
        d["bb_std"] = d["close"].rolling(20).std()
        d["bb_upper"] = d["bb_mid"] + 2 * d["bb_std"]
        d["bb_lower"] = d["bb_mid"] - 2 * d["bb_std"]

        latest = d.iloc[-1]
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
            "reason": "ok",
        }

    def _meta(self, instrument):
        meta = self.instrument_meta.get(instrument)
        if meta:
            return meta
        base, quote = instrument.split("_", 1)
        return InstrumentMeta(
            name=instrument, base=base, quote=quote,
            pip_location=-2 if quote == "JPY" else -4,
            display_precision=3 if quote == "JPY" else 5,
            margin_rate=0.05, minimum_trade_size=1,
        )

    def conversion_to_home(self, currency):
        """Return a conservative currency->account-home conversion factor."""
        if currency == self.currency:
            return 1.0
        if self.smoke_test:
            return 1.0
        direct = f"{currency}_{self.currency}"
        inverse = f"{self.currency}_{currency}"
        try:
            if direct in self.instruments:
                _, bid, _ = self.get_prices(direct)
                return max(float(bid), 1e-8)
            if inverse in self.instruments:
                _, _, ask = self.get_prices(inverse)
                return 1.0 / max(float(ask), 1e-8)
        except Exception:
            pass
        # Do not guess conversion for an unsupported cross. Reject sizing instead.
        return 0.0

    def calculate_position_size(self, instrument, entry_price, stop_price):
        meta = self._meta(instrument)
        quote_to_home = self.conversion_to_home(meta.quote)
        if quote_to_home <= 0:
            return 0
        nav_base = self.nav if self.nav > 0 else self.balance
        risk_amount = nav_base * self.risk_pct
        loss_per_unit = abs(entry_price - stop_price) * quote_to_home
        if loss_per_unit <= 0:
            return 0
        units = int(risk_amount / loss_per_unit)
        return max(meta.minimum_trade_size, units)

    def estimate_margin(self, instrument, units, entry_price):
        meta = self._meta(instrument)
        base_to_home = self.conversion_to_home(meta.base)
        if base_to_home <= 0:
            return float("inf")
        position_value_home = abs(units) * base_to_home
        return position_value_home * max(meta.margin_rate, 0.0)

    def portfolio_guard(self, instrument):
        if len(self.positions) >= self.max_open_positions:
            return False, "max_open_positions"
        base, quote = instrument.split("_", 1)
        for currency in (base, quote):
            exposed = sum(currency in p.split("_", 1) for p in self.positions)
            if exposed >= self.max_currency_positions:
                return False, f"currency_exposure_{currency}"
        nav_base = self.nav if self.nav > 0 else self.balance
        if self.session_start_nav > 0 and nav_base <= self.session_start_nav * (1.0 - self.max_daily_drawdown):
            return False, "daily_drawdown_kill_switch"
        if self.peak_nav > 0 and nav_base <= self.peak_nav * (1.0 - self.max_peak_drawdown):
            return False, "peak_drawdown_kill_switch"
        return True, "ok"

    def get_spread_pips(self, instrument):
        if self.smoke_test:
            return 0.8
        try:
            _, bid, ask = self.get_prices(instrument)
            pip_size = 10 ** self._meta(instrument).pip_location
            return (ask - bid) / pip_size
        except Exception:
            return 9999.0

    def is_session_allowed(self):
        hour = datetime.utcnow().hour
        return 7 <= hour <= 20

    def is_rollover_window(self):
        now = datetime.utcnow().time()
        return dt_time(20, 55) <= now <= dt_time(21, 15)

    def is_market_open(self):
        return True if self.smoke_test else datetime.now().weekday() < 5

    def validate_entry(self, instrument, signal, analysis, regime, spread_pips):
        if signal not in ("BUY", "SELL"):
            return False, "hold_signal"

        if instrument in self.positions:
            return False, "already_in_position"

        portfolio_ok, portfolio_reason = self.portfolio_guard(instrument)
        if not portfolio_ok:
            return False, portfolio_reason

        if self.is_rollover_window():
            return False, "rollover_window"

        if not self.is_session_allowed():
            return False, "session_closed"

        if spread_pips > self.spread_limits.get(instrument, 2.2):
            return False, f"spread_too_high_{spread_pips:.2f}"

        if regime == "UNCERTAIN":
            return False, "uncertain_regime"

        return True, "ok"

    def execute_trade(self, instrument, signal, analysis, regime, spread_pips):
        score = float(analysis.get("score", 0.0)) if analysis else 0.0
        accepted, reason = self.validate_entry(instrument, signal, analysis, regime, spread_pips)

        if not accepted:
            self._log_decision(self._decision_row(
                instrument, signal, False, reason, regime, spread_pips, score
            ))
            return None, reason

        try:
            if self.smoke_test:
                bid, ask = 1.1000, 1.1002
            else:
                _, bid, ask = self.get_prices(instrument)

            sl_tp = {"Faster": (0.007, 0.010), "Balanced": (0.008, 0.012), "Safer": (0.006, 0.015)}
            sl_pct, tp_pct = sl_tp.get(self.strategy_mode, (0.008, 0.012))

            trailing_distance_by_mode = {"Faster": 0.0012, "Balanced": None, "Safer": None}
            tsl_pct = trailing_distance_by_mode.get(self.strategy_mode, None)

            if signal == "BUY":
                entry = ask
                direction = "LONG"
                stop_loss = entry * (1 - sl_pct)
                take_profit = entry * (1 + tp_pct)
                signed = 1
            else:
                entry = bid
                direction = "SHORT"
                stop_loss = entry * (1 + sl_pct)
                take_profit = entry * (1 - tp_pct)
                signed = -1

            units = self.calculate_position_size(instrument, entry, stop_loss)
            if units <= 0:
                reason = "invalid_units_or_conversion"
                self._log_decision(self._decision_row(
                    instrument, signal, False, reason, regime, spread_pips, score, entry, stop_loss, take_profit, units
                ))
                return None, reason

            nav_base = self.nav if self.nav > 0 else self.balance
            meta = self._meta(instrument)
            quote_to_home = self.conversion_to_home(meta.quote)
            estimated_loss = abs(entry - stop_loss) * units * quote_to_home
            allowed_risk = nav_base * self.risk_pct
            if estimated_loss > allowed_risk * 1.01:
                reason = "risk_exceeded"
                self._log_decision(self._decision_row(
                    instrument, signal, False, reason, regime, spread_pips, score, entry, stop_loss, take_profit, units
                ))
                return None, reason

            required_margin = self.estimate_margin(instrument, units, entry)
            if self.margin_available <= 0 or required_margin > self.margin_available * self.margin_buffer:
                reason = "insufficient_margin_buffer"
                self._log_decision(self._decision_row(
                    instrument, signal, False, reason, regime, spread_pips, score, entry, stop_loss, take_profit, units
                ))
                return None, reason

            proposal = OrderProposal(
                instrument=instrument, side=signal, entry=entry,
                stop_loss=stop_loss, take_profit=take_profit, units=units,
                risk_amount=allowed_risk, estimated_loss=estimated_loss,
                required_margin=required_margin, spread_pips=spread_pips,
                regime=regime,
            )
            if proposal.take_profit == proposal.entry or proposal.stop_loss == proposal.entry:
                reason = "invalid_proposal_prices"
                self._log_decision(self._decision_row(
                    instrument, signal, False, reason, regime, spread_pips, score, entry, stop_loss, take_profit, units
                ))
                return None, reason

            if self.smoke_test:
                order = {"price": entry, "id": f"SMOKE-{instrument}-{int(time.time())}"}
            else:
                order_kwargs = {
                    "sl_distance": float(abs(entry - stop_loss)),
                    "tp_price": float(take_profit),
                }
                if tsl_pct is not None:
                    order_kwargs["tsl_distance"] = float(entry * tsl_pct)
                order = self.create_order(instrument, signed * units, suppress=True, ret=True, **order_kwargs)

            if not order:
                reason = "invalid_order_response"
                self._log_decision(self._decision_row(
                    instrument, signal, False, reason, regime, spread_pips, score, entry, stop_loss, take_profit, units
                ))
                return None, reason

            trade = {
                "instrument": instrument,
                "direction": direction,
                "units": units,
                "entry_price": float(order.get("price", entry)),
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "trailing_stop_distance": float(entry * tsl_pct) if tsl_pct else None,
                "entry_time": datetime.utcnow(),
                "status": "OPEN",
                "peak_price": float(entry),
                "trough_price": float(entry),
                "order_id": order.get("id"),
            }
            self.positions[instrument] = trade
            self.trades.append(trade)

            self._log_decision(self._decision_row(
                instrument, signal, True, "ok", regime, spread_pips, score, entry, stop_loss, take_profit, units
            ))
            return trade, "ok"
        except Exception as e:
            reason = f"order_exception:{type(e).__name__}"
            self._log_decision(self._decision_row(
                instrument, signal, False, reason, regime, spread_pips, score
            ))
            return None, reason

    def close_position(self, instrument):
        if instrument not in self.positions:
            return None
        try:
            pos = self.positions[instrument]
            units = pos["units"]

            if self.smoke_test:
                order = {"pl": 0, "price": pos["entry_price"]}
            else:
                order = self.create_order(
                    instrument,
                    -units if pos["direction"] == "LONG" else units,
                    suppress=True,
                    ret=True,
                )
            if not order:
                return None

            pnl = float(order.get("pl", 0))
            pos["exit_price"] = float(order.get("price", 0))
            pos["exit_time"] = datetime.utcnow()
            pos["pnl"] = pnl
            pos["status"] = "CLOSED"
            self.closed_trades.append(pos.copy())
            del self.positions[instrument]
            self.update_account_info()
            return pos
        except Exception:
            return None


class EliteTradingGUI:
    def __init__(self, root, smoke_test=False):
        self.root = root
        self.root.title("🚀 FX Trading Bot - Elite Edition")
        self.root.geometry("1900x1000")
        self.root.configure(bg=COLORS["bg"])

        self.smoke_test = smoke_test
        self.trader = None
        self.trading_active = False
        self.market_data = {}
        self.analysis_results = {}
        self.signal_strengths = {}
        self.close_all_on_stop = tk.BooleanVar(value=True)
        self.max_chart_tabs = 12

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
        ttk.Radiobutton(top, text="Demo", variable=self.account_var, value="demo",
                        command=lambda: self.connect_account("demo")).pack(side=tk.LEFT)
        ttk.Radiobutton(top, text="Live", variable=self.account_var, value="live",
                        command=lambda: self.connect_account("live")).pack(side=tk.LEFT)

        self.start_btn = ttk.Button(top, text="▶ START", style="Success.TButton", command=self.start_trading)
        self.start_btn.pack(side=tk.LEFT, padx=8)
        self.stop_btn = ttk.Button(top, text="■ STOP", style="Error.TButton", command=self.stop_trading, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=4)

        ttk.Checkbutton(top, text="Close all positions on STOP", variable=self.close_all_on_stop).pack(side=tk.LEFT, padx=8)

        ttk.Label(top, text="Timeframe:").pack(side=tk.LEFT, padx=4)
        self.timeframe_var = tk.StringVar(value="M5")
        ttk.Combobox(top, textvariable=self.timeframe_var, values=["M1", "M5", "M15", "M30", "H1", "H4"],
                     state="readonly", width=6).pack(side=tk.LEFT)

        ttk.Label(top, text="Mode:").pack(side=tk.LEFT, padx=4)
        self.mode_var = tk.StringVar(value="Balanced")
        ttk.Combobox(top, textvariable=self.mode_var, values=["Faster", "Balanced", "Safer"],
                     state="readonly", width=10).pack(side=tk.LEFT)

        ttk.Label(top, text="Risk %:").pack(side=tk.LEFT, padx=4)
        self.risk_var = tk.DoubleVar(value=1.0)
        tk.Spinbox(top, from_=0.1, to=2.0, increment=0.1, textvariable=self.risk_var, width=5).pack(side=tk.LEFT)

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
        self.rebuild_chart_tabs(["EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF", "AUD_USD"])

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
        self.signal_container = signal_box
        self.signal_widgets = {}
        self.rebuild_signal_widgets(["EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF", "AUD_USD"])

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

    def rebuild_chart_tabs(self, instruments):
        for tab_id in self.chart_notebook.tabs():
            self.chart_notebook.forget(tab_id)
        self.charts = {}
        display_instruments = instruments[: self.max_chart_tabs]
        for inst in display_instruments:
            tab = ttk.Frame(self.chart_notebook)
            self.chart_notebook.add(tab, text=inst.replace("_", "/"))
            fig = Figure(figsize=(8, 4), facecolor=COLORS["bg"])
            ax = fig.add_subplot(111, facecolor=COLORS["panel"])
            canvas = FigureCanvasTkAgg(fig, tab)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.charts[inst] = {"fig": fig, "ax": ax, "canvas": canvas}

    def rebuild_signal_widgets(self, instruments):
        for child in self.signal_container.winfo_children():
            child.destroy()
        self.signal_widgets = {}
        for inst in instruments:
            row = ttk.Frame(self.signal_container)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=inst.replace("_", "/"), width=10).pack(side=tk.LEFT)
            bar = ttk.Progressbar(row, length=140, mode="determinate")
            bar.pack(side=tk.LEFT, padx=4)
            txt = ttk.Label(row, text="HOLD", width=6)
            txt.pack(side=tk.RIGHT)
            self.signal_widgets[inst] = (bar, txt)

    def connect_account(self, account_type):
        self.status_label.config(text=f"Connecting {account_type.upper()}...", foreground=COLORS["warning"])

        def _connect():
            try:
                cfg = f"config/oanda_{account_type}.cfg"
                self.trader = EliteTrader(cfg, self.timeframe_var.get(), self.risk_var.get(), smoke_test=self.smoke_test)
                self.rebuild_chart_tabs(self.trader.instruments)
                self.rebuild_signal_widgets(self.trader.instruments)
                shown = min(len(self.trader.instruments), self.max_chart_tabs)
                self.status_label.config(
                    text=f"{account_type.upper()} Connected ({len(self.trader.instruments)} FX pairs, showing {shown} charts)",
                    foreground=COLORS["success"],
                )
                self.log(f"Connected to {account_type.upper()} account.")
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
                self.trader.update_account_info()

                for inst in self.trader.instruments:
                    df = self.trader.get_live_data(inst, 120)
                    if df is None:
                        self.log(f"{inst} blocked: no data")
                        continue

                    self.market_data[inst] = df
                    analysis = self.trader.analyze_fast(df)
                    self.analysis_results[inst] = analysis
                    self.signal_strengths[inst] = analysis.get("score", 0.0)

                    signal = analysis.get("signal", "HOLD")
                    score = analysis.get("score", 0.0)
                    spread = self.trader.get_spread_pips(inst)
                    regime = self.trader.detect_regime(df)

                    self.log(f"{inst} regime={regime} score={score:+.2f} signal={signal}")

                    if signal in ("BUY", "SELL"):
                        trade, reason = self.trader.execute_trade(inst, signal, analysis, regime, spread)
                        if trade:
                            self.log(f"{inst} {signal} opened @ {trade['entry_price']:.5f}")
                        else:
                            self.log(f"{inst} blocked: {reason}")

                time.sleep({"Faster": 8, "Balanced": 12, "Safer": 18}.get(self.mode_var.get(), 12))
            except Exception as e:
                self.log(f"Trading loop error: {e}")
                time.sleep(5)

    def start_updates(self):
        def loop():
            while True:
                try:
                    self.update_dashboard()
                    self.update_charts()
                    self.update_signal_panel()
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

    def update_signal_panel(self):
        if not self.trader:
            return
        for inst, (bar, txt) in self.signal_widgets.items():
            analysis = self.analysis_results.get(inst, {"signal": "HOLD", "score": 0.0})
            score = max(-1.0, min(1.0, float(analysis.get("score", 0.0))))
            bar["value"] = (score + 1.0) * 50.0
            txt.config(text=analysis.get("signal", "HOLD"))

    def update_charts(self):
        for inst, ch in self.charts.items():
            df = self.market_data.get(inst)
            if df is None or df.empty:
                continue
            p = df.copy()
            p["sma_20"] = p["close"].rolling(20).mean()
            p["sma_50"] = p["close"].rolling(50).mean()

            ax = ch["ax"]
            ax.clear()
            ax.plot(p.index, p["close"], color=COLORS["accent"], linewidth=1.4, label="Price")
            if p["sma_20"].notna().any():
                ax.plot(p.index, p["sma_20"], color=COLORS["success"], linewidth=1.2, alpha=0.9, label="SMA 20")
            if p["sma_50"].notna().any():
                ax.plot(p.index, p["sma_50"], color=COLORS["warning"], linewidth=1.2, alpha=0.9, label="SMA 50")

            ax.set_title(inst.replace("_", "/"), color=COLORS["fg"])
            ax.grid(True, alpha=0.25)
            ax.legend(loc="upper left", fontsize=8, framealpha=0.25)
            ch["canvas"].draw()

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_text.see(tk.END)


def run_smoke_test():
    print("Running Elite smoke test...")
    t = EliteTrader("config/oanda_demo.cfg", timeframe="M5", risk_pct=1.0, smoke_test=True)
    inst = "EUR_USD"
    df = t.get_live_data(inst, 120)
    analysis = t.analyze_fast(df)
    regime = t.detect_regime(df)
    spread = t.get_spread_pips(inst)
    signal = analysis.get("signal", "HOLD")
    trade, reason = t.execute_trade(inst, signal, analysis, regime, spread)
    print(f"signal={signal} regime={regime} spread={spread:.2f} reason={reason} trade_opened={trade is not None}")
    print(f"decision_log={t.decisions_path}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-test", action="store_true", help="Run offline smoke test without OANDA calls")
    args = parser.parse_args()

    if args.smoke_test:
        raise SystemExit(run_smoke_test())

    root = tk.Tk()
    app = EliteTradingGUI(root, smoke_test=False)
    root.mainloop()
