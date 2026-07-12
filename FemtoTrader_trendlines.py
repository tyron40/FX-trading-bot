from tpqoa.tpqoa import tpqoa
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from helpers.technical_analysis import TechnicalAnalysis

class FemtoTrader(tpqoa):
    def __init__(
        self,
        cfg,
        instruments=['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD'],
        risk_per_trade=0.02,  # Reduced to 2% per trade for multiple instruments
        stop_loss_pct=0.15,   # 0.15% stop loss
        take_profit_pct=0.3,  # 0.3% take profit
    ):
        """
        Trend-following auto trader with multi-instrument support.
        Focuses on trendlines and market direction.
        """
        super().__init__(cfg)

        self._technical_analyzer = TechnicalAnalysis()
        self._instruments = instruments
        self._positions = {}  # Track positions per instrument
        self._risk_per_trade = risk_per_trade
        self._stop_loss_pct = stop_loss_pct
        self._take_profit_pct = take_profit_pct

        # Trend tracking
        self._market_trends = {}  # Trend direction per instrument
        self._trendlines = {}     # Trendlines per instrument
        self._chart_data = {}     # Historical data per instrument

        # Get account info
        try:
            summary = self.get_account_summary()
            self._balance = float(summary.get('balance', 1000.0))
        except Exception as e:
            print(f"Warning: Error getting account balance: {str(e)}")
            self._balance = 1000.0

        print(f"\nAccount Balance: ${self._balance:.2f}")
        print(f"\nMulti-Instrument Trend Trader:")
        print(f"Instruments: {', '.join(instruments)}")
        print("\nTrend-Following Features:")
        print("- Dynamic trendline analysis per instrument")
        print("- Swing point detection for trend direction")
        print("- Breakout trading with trend confirmation")
        print("- Multi-instrument diversification")
        print("- Trend-following bias (no counter-trend trades)")
        print(f"- {risk_per_trade*100}% risk per trade per instrument")
        print(f"- {stop_loss_pct}% stop loss")
        print(f"- {take_profit_pct}% take profit")

        # GUI callbacks
        self._gui_callbacks = {
            'price': None,
            'signal': None,
            'trend': None,
            'position': None,
            'history': None
        }

    def set_gui_callbacks(self, price_callback=None, signal_callback=None, trend_callback=None,
                         position_callback=None, history_callback=None):
        """Set GUI callback functions"""
        self._gui_callbacks['price'] = price_callback
        self._gui_callbacks['signal'] = signal_callback
        self._gui_callbacks['trend'] = trend_callback
        self._gui_callbacks['position'] = position_callback
        self._gui_callbacks['history'] = history_callback

    def _get_instrument_data(self, instrument):
        """Get historical data for trend analysis."""
        try:
            response = self.ctx.instrument.candles(
                instrument,
                granularity="M5",  # 5-minute candles for better trend analysis
                count=100,  # More data for trendlines
                price="M"
            )

            if response.status != 200:
                print(f"Error getting candles for {instrument}: {response.body}")
                return None

            data = []
            for candle in response.body.get('candles', []):
                if candle.complete:
                    data.append({
                        'time': pd.to_datetime(candle.time),
                        'open': float(candle.mid.o),
                        'high': float(candle.mid.h),
                        'low': float(candle.mid.l),
                        'close': float(candle.mid.c),
                        'volume': int(candle.volume)
                    })

            if len(data) < 50:  # Need enough data for trend analysis
                print(f"Only {len(data)} complete candles for {instrument}, need at least 50")
                return None

            df = pd.DataFrame(data[-80:])  # Use last 80 candles
            df.set_index('time', inplace=True)
            return df

        except Exception as e:
            print(f"Error getting data for {instrument}: {str(e)}")
            return None

    def _analyze_trend(self, instrument):
        """Analyze trend direction and strength for an instrument."""
        df = self._get_instrument_data(instrument)
        if df is None:
            return None

        # Store chart data
        self._chart_data[instrument] = df

        # Perform complete technical analysis
        analysis = self._technical_analyzer.analyze_chart(df)

        # Determine overall trend direction
        trend_direction = self._calculate_trend_direction(analysis, df)
        trend_strength = self._calculate_trend_strength(analysis, df)

        # Store trendlines for this instrument
        self._trendlines[instrument] = analysis.get('trendlines', [])

        trend_info = {
            'instrument': instrument,
            'direction': trend_direction,  # 1 = uptrend, -1 = downtrend, 0 = sideways
            'strength': trend_strength,    # 0-1 scale
            'analysis': analysis,
            'current_price': df['close'].iloc[-1],
            'trendlines': len(analysis.get('trendlines', [])),
            'breakouts': len(analysis.get('breakouts', [])),
            'retests': len(analysis.get('retests', []))
        }

        self._market_trends[instrument] = trend_info
        return trend_info

    def _calculate_trend_direction(self, analysis, df):
        """Calculate overall trend direction from multiple factors."""
        direction_score = 0

        # 1. Trendline slope analysis
        trendlines = analysis.get('trendlines', [])
        slope_score = 0
        for line in trendlines:
            if line['strength'] >= 3:  # Strong trendlines only
                slope_score += line['slope'] * line['strength']

        if slope_score > 0.001:
            direction_score += 2  # Strong uptrend
        elif slope_score < -0.001:
            direction_score -= 2  # Strong downtrend

        # 2. Price action relative to trendlines
        current_price = df['close'].iloc[-1]
        support_count = 0
        resistance_count = 0

        for line in trendlines:
            if line['type'] == 'support':
                if current_price > line['slope'] * len(df) + line['intercept']:
                    support_count += line['strength']
            elif line['type'] == 'resistance':
                if current_price < line['slope'] * len(df) + line['intercept']:
                    resistance_count += line['strength']

        direction_score += support_count * 0.5   # Above support = bullish
        direction_score -= resistance_count * 0.5 # Below resistance = bearish

        # 3. Recent price momentum
        recent_prices = df['close'].values[-10:]
        if len(recent_prices) >= 5:
            momentum = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
            direction_score += momentum * 100  # Scale momentum

        # 4. Breakout analysis
        breakouts = analysis.get('breakouts', [])
        for breakout in breakouts:
            if breakout['strength'] >= 3:
                direction_score += breakout['direction'] * breakout['strength'] * 0.3

        # Determine final direction
        if direction_score > 2:
            return 1   # Uptrend
        elif direction_score < -2:
            return -1  # Downtrend
        else:
            return 0   # Sideways

    def _calculate_trend_strength(self, analysis, df):
        """Calculate trend strength (0-1 scale)."""
        strength_factors = []

        # 1. Trendline strength
        trendlines = analysis.get('trendlines', [])
        if trendlines:
            avg_strength = np.mean([line['strength'] for line in trendlines])
            strength_factors.append(min(avg_strength / 5, 1.0))

        # 2. Price consistency
        recent_prices = df['close'].values[-20:]
        if len(recent_prices) >= 10:
            # Calculate linear trend
            x = np.arange(len(recent_prices))
            slope, _ = np.polyfit(x, recent_prices, 1)
            r_squared = np.corrcoef(x, recent_prices)[0, 1] ** 2
            trend_consistency = abs(slope) * r_squared * 1000  # Scale factor
            strength_factors.append(min(trend_consistency, 1.0))

        # 3. Breakout activity
        breakouts = len(analysis.get('breakouts', []))
        retests = len(analysis.get('retests', []))
        breakout_ratio = (breakouts + retests) / max(len(df), 1)
        strength_factors.append(min(breakout_ratio * 10, 1.0))

        # Average strength
        if strength_factors:
            return np.mean(strength_factors)
        return 0.0

    def _find_trading_opportunity(self):
        """Find best trading opportunity across all instruments."""
        best_opportunity = None
        best_score = 0

        for instrument in self._instruments:
            # Skip if already have position in this instrument
            if instrument in self._positions:
                continue

            trend_info = self._analyze_trend(instrument)
            if trend_info is None:
                continue

            # Calculate opportunity score
            opportunity_score = self._calculate_opportunity_score(trend_info)

            if opportunity_score > best_score and opportunity_score > 0.6:  # Minimum threshold
                best_opportunity = trend_info
                best_score = opportunity_score

        return best_opportunity

    def _find_all_trading_opportunities(self):
        """Find all valid trading opportunities across all instruments."""
        opportunities = []

        for instrument in self._instruments:
            # Skip if already have position in this instrument
            if instrument in self._positions:
                continue

            trend_info = self._analyze_trend(instrument)
            if trend_info is None:
                continue

            # Calculate opportunity score
            opportunity_score = self._calculate_opportunity_score(trend_info)

            # Only include opportunities above minimum threshold
            if opportunity_score > 0.6:
                opportunities.append(trend_info)

        # Sort by opportunity score (best first)
        opportunities.sort(key=lambda x: self._calculate_opportunity_score(x), reverse=True)

        return opportunities
                
    def _calculate_opportunity_score(self, trend_info):
        """Calculate how attractive a trading opportunity is."""
        score = 0

        # Trend strength (40% weight)
        score += trend_info['strength'] * 0.4

        # Trend direction confidence (30% weight)
        if trend_info['direction'] != 0:
            direction_confidence = abs(trend_info['direction']) * trend_info['strength']
            score += direction_confidence * 0.3

        # Breakout activity (20% weight)
        breakout_activity = min((trend_info['breakouts'] + trend_info['retests']) / 5, 1.0)
        score += breakout_activity * 0.2

        # Trendline quality (10% weight)
        trendline_quality = min(trend_info['trendlines'] / 3, 1.0)
        score += trendline_quality * 0.1

        return score

    def _calculate_position_size(self, instrument, volatility):
        """Calculate position size based on trend strength and volatility."""
        try:
            # Get current price
            time, bid, ask = self.get_prices(instrument)
            price = bid

            # Base risk amount per instrument (distribute across instruments)
            max_instruments = len(self._instruments)
            risk_per_instrument = self._balance * self._risk_per_trade / max_instruments

            # Adjust based on trend strength
            trend_info = self._market_trends.get(instrument)
            trend_multiplier = trend_info['strength'] if trend_info else 0.5

            adjusted_risk = risk_per_instrument * trend_multiplier

            # Adjust for volatility
            volatility_factor = 1 / (1 + volatility)
            final_risk = adjusted_risk * volatility_factor

            # Calculate stop loss in pips
            stop_loss_pips = price * self._stop_loss_pct / 100

            # Calculate units
            units = int(final_risk / stop_loss_pips)

            # Ensure reasonable limits
            return max(100, min(units, 50000))

        except Exception as e:
            print(f"Error calculating position size for {instrument}: {str(e)}")
            return 100

    def manage_trades(self):
        """Manage positions across all instruments."""
        try:
            # Check existing positions
            self._manage_existing_positions()

            # Look for new opportunities (can open multiple positions)
            opportunities = self._find_all_trading_opportunities()
            for opportunity in opportunities:
                if opportunity['instrument'] not in self._positions:  # Don't trade same instrument twice
                    self._open_position(opportunity)

        except Exception as e:
            print(f"Error managing trades: {str(e)}")
        
    def _manage_existing_positions(self):
        """Check and manage existing positions."""
        instruments_to_close = []

        for instrument, position in self._positions.items():
            try:
                # Get current price
                time, bid, ask = self.get_prices(instrument)
                current_price = bid

                # Calculate P&L
                entry_price = position['entry_price']
                if position['type'] == 'long':
                    profit_pct = (current_price - entry_price) / entry_price * 100
                else:
                    profit_pct = (entry_price - current_price) / entry_price * 100

                # Check stop loss
                if profit_pct <= -self._stop_loss_pct:
                    print(f"Stop loss triggered for {instrument}")
                    instruments_to_close.append(instrument)
                    continue

                # Check take profit
                if profit_pct >= self._take_profit_pct:
                    print(f"Take profit triggered for {instrument}")
                    instruments_to_close.append(instrument)
                    continue

                # Check if trend has reversed
                trend_info = self._market_trends.get(instrument)
                if trend_info:
                    current_trend = trend_info['direction']
                    position_direction = 1 if position['type'] == 'long' else -1

                    # Close if trend reverses strongly
                    if current_trend * position_direction < 0 and trend_info['strength'] > 0.7:
                        print(f"Trend reversal detected for {instrument}")
                        instruments_to_close.append(instrument)
                        continue

                # Update position info for GUI
                position['current_price'] = current_price
                position['profit_pct'] = profit_pct

            except Exception as e:
                print(f"Error managing position for {instrument}: {str(e)}")

        # Close positions
        for instrument in instruments_to_close:
            self._close_position(instrument)

    def _open_position(self, opportunity):
        """Open a new position based on trend opportunity."""
        instrument = opportunity['instrument']
        direction = opportunity['direction']

        if direction == 0:  # No clear trend
            return

        try:
            # Calculate position size
            df = self._chart_data.get(instrument)
            volatility = np.std(df['close'].values[-20:]) if df is not None else 0.001
            units = self._calculate_position_size(instrument, volatility)

            # Open position
            if direction > 0:
                order = self.create_order(instrument, units, suppress=True, ret=True)
                position_type = 'long'
            else:
                order = self.create_order(instrument, -units, suppress=True, ret=True)
                position_type = 'short'

            if order:
                self._positions[instrument] = {
                    'type': position_type,
                    'units': units,
                    'entry_price': float(order['price']),
                    'time': order['time'],
                    'trend_info': opportunity,
                    'current_price': float(order['price']),
                    'profit_pct': 0.0
                }

                print(f"\n=== New Trend-Following Position ===")
                print(f"Instrument: {instrument}")
                print(f"Type: {position_type}")
                print(f"Units: {units}")
                print(f"Entry Price: ${float(order['price'])}")
                print(f"Trend Strength: {opportunity['strength']:.2f}")
                print(f"Trend Direction: {'Up' if direction > 0 else 'Down'}")

        except Exception as e:
            print(f"Error opening position for {instrument}: {str(e)}")

    def _close_position(self, instrument):
        """Close position for an instrument."""
        if instrument not in self._positions:
            return

        position = self._positions[instrument]

        try:
            units = position['units']

            if position['type'] == 'long':
                order = self.create_order(instrument, -units, suppress=True, ret=True)
            else:
                order = self.create_order(instrument, units, suppress=True, ret=True)

            if order:
                profit = float(order['pl'])
                print(f"\n=== Position Closed ===")
                print(f"Instrument: {instrument}")
                print(f"Profit/Loss: ${profit:.2f}")
                print(f"Entry: ${position['entry_price']:.5f}")
                print(f"Exit: ${position['current_price']:.5f}")

                del self._positions[instrument]

        except Exception as e:
            print(f"Error closing position for {instrument}: {str(e)}")

    def run(self):
        """Main trading loop with multi-instrument trend following."""
        print("\nStarting Multi-Instrument Trend-Following Trader...")
        print("Press Ctrl+C to stop")

        while True:
            try:
                self.manage_trades()

                # Update GUI with current status
                if self._gui_callbacks['trend']:
                    trend_summary = {}
                    for instrument in self._instruments:
                        trend_info = self._market_trends.get(instrument)
                        if trend_info:
                            trend_summary[instrument] = {
                                'direction': trend_info['direction'],
                                'strength': trend_info['strength'],
                                'trendlines': trend_info['trendlines']
                            }
                    self._gui_callbacks['trend'](trend_summary)

                if self._gui_callbacks['position']:
                    self._gui_callbacks['position'](self._positions)

                # Wait before next check
                import time
                time.sleep(30)  # Check every 30 seconds for trend following

            except KeyboardInterrupt:
                print("\nStopping Trend-Following Trader...")
                # Close all positions
                for instrument in list(self._positions.keys()):
                    self._close_position(instrument)
                break
            except Exception as e:
                print(f"\nError in trading loop: {str(e)}")
                continue
