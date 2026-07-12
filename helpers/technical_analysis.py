import numpy as np
import pandas as pd
from scipy import stats
from datetime import datetime, timedelta

class TechnicalAnalysis:
    def __init__(self):
        self.swing_points = []
        self.trendlines = []
        self.candle_patterns = []

    def detect_swing_points(self, df, min_swing=0.0005, lookback=5):
        """Detect swing high and low points in price data."""
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values

        swing_highs = []
        swing_lows = []

        for i in range(lookback, len(highs) - lookback):
            # Check for swing high
            is_swing_high = True
            for j in range(i - lookback, i + lookback + 1):
                if j != i and highs[j] >= highs[i]:
                    is_swing_high = False
                    break

            if is_swing_high and abs(highs[i] - closes[i]) > min_swing:
                swing_highs.append((i, highs[i], df.index[i]))

            # Check for swing low
            is_swing_low = True
            for j in range(i - lookback, i + lookback + 1):
                if j != i and lows[j] <= lows[i]:
                    is_swing_low = False
                    break

            if is_swing_low and abs(lows[i] - closes[i]) > min_swing:
                swing_lows.append((i, lows[i], df.index[i]))

        return swing_highs, swing_lows

    def construct_trendlines(self, swing_points, min_points=3, max_distance=0.001):
        """Construct trendlines from swing points."""
        trendlines = []

        # Separate highs and lows
        highs = [(idx, price, time) for idx, price, time in swing_points if price > 0]  # Assuming highs are positive
        lows = [(idx, price, time) for idx, price, time in swing_points if price < 0]   # Assuming lows are negative

        # Construct resistance lines (from swing highs)
        if len(highs) >= min_points:
            resistance_lines = self._find_parallel_lines(highs, 'resistance', max_distance)
            trendlines.extend(resistance_lines)

        # Construct support lines (from swing lows)
        if len(lows) >= min_points:
            support_lines = self._find_parallel_lines(lows, 'support', max_distance)
            trendlines.extend(support_lines)

        return trendlines

    def _find_parallel_lines(self, points, line_type, max_distance):
        """Find parallel trendlines from points."""
        lines = []

        for i in range(len(points)):
            for j in range(i + 2, len(points)):
                # Calculate slope and intercept
                x1, y1, t1 = points[i]
                x2, y2, t2 = points[j]

                if x2 == x1:
                    continue

                slope = (y2 - y1) / (x2 - x1)
                intercept = y1 - slope * x1

                # Check how many points fit this line
                fitting_points = []
                for k in range(len(points)):
                    x, y, t = points[k]
                    predicted_y = slope * x + intercept
                    distance = abs(y - predicted_y)

                    if distance <= max_distance:
                        fitting_points.append((x, y, t))

                # If enough points fit, create trendline
                if len(fitting_points) >= 3:
                    lines.append({
                        'type': line_type,
                        'slope': slope,
                        'intercept': intercept,
                        'points': fitting_points,
                        'strength': len(fitting_points),
                        'start_time': min(t for _, _, t in fitting_points),
                        'end_time': max(t for _, _, t in fitting_points)
                    })

        # Remove duplicate lines (keep strongest)
        unique_lines = []
        for line in lines:
            is_duplicate = False
            for existing in unique_lines:
                if (abs(line['slope'] - existing['slope']) < 0.001 and
                    abs(line['intercept'] - existing['intercept']) < 0.001):
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_lines.append(line)

        return unique_lines

    def detect_candle_patterns(self, df):
        """Detect various candle patterns."""
        patterns = []

        for i in range(2, len(df)):
            pattern = self._analyze_candle_pattern(df.iloc[i-2:i+1])
            if pattern:
                patterns.append({
                    'index': i,
                    'pattern': pattern['name'],
                    'direction': pattern['direction'],
                    'strength': pattern['strength'],
                    'time': df.index[i]
                })

        return patterns

    def _analyze_candle_pattern(self, candles):
        """Analyze a set of 3 candles for patterns."""
        if len(candles) < 3:
            return None

        c1, c2, c3 = candles.iloc[0], candles.iloc[1], candles.iloc[2]

        # Calculate body sizes and directions
        body1 = abs(c1['close'] - c1['open'])
        body2 = abs(c2['close'] - c2['open'])
        body3 = abs(c3['close'] - c3['open'])

        dir1 = 1 if c1['close'] > c1['open'] else -1
        dir2 = 1 if c2['close'] > c2['open'] else -1
        dir3 = 1 if c3['close'] > c3['open'] else -1

        # Bullish Engulfing
        if (dir1 == -1 and dir2 == 1 and
            c2['open'] <= c1['close'] and c2['close'] >= c1['open'] and
            body2 > body1 * 1.5):
            return {'name': 'Bullish Engulfing', 'direction': 1, 'strength': 'Strong'}

        # Bearish Engulfing
        if (dir1 == 1 and dir2 == -1 and
            c2['open'] >= c1['close'] and c2['close'] <= c1['open'] and
            body2 > body1 * 1.5):
            return {'name': 'Bearish Engulfing', 'direction': -1, 'strength': 'Strong'}

        # Morning Star
        if (dir1 == -1 and dir2 == -1 and dir3 == 1 and
            body1 > body2 and body3 > body2 and
            c3['close'] > (c1['open'] + c1['close']) / 2):
            return {'name': 'Morning Star', 'direction': 1, 'strength': 'Strong'}

        # Evening Star
        if (dir1 == 1 and dir2 == 1 and dir3 == -1 and
            body1 > body2 and body3 > body2 and
            c3['close'] < (c1['open'] + c1['close']) / 2):
            return {'name': 'Evening Star', 'direction': -1, 'strength': 'Strong'}

        # Three White Soldiers
        if dir1 == 1 and dir2 == 1 and dir3 == 1 and body1 > 0 and body2 > 0 and body3 > 0:
            if c2['close'] > c1['close'] and c3['close'] > c2['close']:
                return {'name': 'Three White Soldiers', 'direction': 1, 'strength': 'Strong'}

        # Three Black Crows
        if dir1 == -1 and dir2 == -1 and dir3 == -1 and body1 > 0 and body2 > 0 and body3 > 0:
            if c2['close'] < c1['close'] and c3['close'] < c2['close']:
                return {'name': 'Three Black Crows', 'direction': -1, 'strength': 'Strong'}

        # Pin Bar (Hammer/Shooting Star)
        total_range2 = c2['high'] - c2['low']
        body_ratio2 = body2 / total_range2 if total_range2 > 0 else 0

        if body_ratio2 < 0.3:  # Small body
            upper_wick = c2['high'] - max(c2['open'], c2['close'])
            lower_wick = min(c2['open'], c2['close']) - c2['low']

            if lower_wick > body2 * 2 and lower_wick > upper_wick:
                return {'name': 'Hammer', 'direction': 1, 'strength': 'Medium'}
            elif upper_wick > body2 * 2 and upper_wick > lower_wick:
                return {'name': 'Shooting Star', 'direction': -1, 'strength': 'Medium'}

        # Doji
        if body_ratio2 < 0.1:
            return {'name': 'Doji', 'direction': 0, 'strength': 'Weak'}

        # Inside Bar
        if (c2['high'] <= c1['high'] and c2['low'] >= c1['low']):
            return {'name': 'Inside Bar', 'direction': 0, 'strength': 'Medium'}

        # Outside Bar
        if (c2['high'] >= c1['high'] and c2['low'] <= c1['low']):
            direction = 1 if c2['close'] > c1['close'] else -1
            return {'name': 'Outside Bar', 'direction': direction, 'strength': 'Medium'}

        return None

    def check_breakouts(self, df, trendlines, current_price):
        """Check for breakouts above/below trendlines."""
        breakouts = []

        for line in trendlines:
            slope = line['slope']
            intercept = line['intercept']

            # Get the most recent point on the trendline
            last_index = len(df) - 1
            trendline_price = slope * last_index + intercept

            # Check for breakout
            if line['type'] == 'resistance':
                if current_price > trendline_price * 1.0005:  # 5 pip breakout
                    breakouts.append({
                        'type': 'resistance_breakout',
                        'direction': 1,
                        'strength': line['strength'],
                        'trendline': line
                    })
            elif line['type'] == 'support':
                if current_price < trendline_price * 0.9995:  # 5 pip breakout
                    breakouts.append({
                        'type': 'support_breakout',
                        'direction': -1,
                        'strength': line['strength'],
                        'trendline': line
                    })

        return breakouts

    def check_retests(self, df, trendlines, current_price, recent_high, recent_low):
        """Check for retests of broken trendlines."""
        retests = []

        for line in trendlines:
            slope = line['slope']
            intercept = line['intercept']

            # Get the most recent point on the trendline
            last_index = len(df) - 1
            trendline_price = slope * last_index + intercept

            # Check for retest (price approaches trendline after breakout)
            if line['type'] == 'resistance':
                if abs(current_price - trendline_price) / trendline_price < 0.001:  # Within 10 pips
                    if recent_high > trendline_price * 1.0005:  # Recent breakout
                        retests.append({
                            'type': 'resistance_retest',
                            'direction': 1,
                            'trendline': line
                        })
            elif line['type'] == 'support':
                if abs(current_price - trendline_price) / trendline_price < 0.001:  # Within 10 pips
                    if recent_low < trendline_price * 0.9995:  # Recent breakout
                        retests.append({
                            'type': 'support_retest',
                            'direction': -1,
                            'trendline': line
                        })

        return retests

    def analyze_chart(self, df):
        """Complete chart analysis combining all techniques."""
        # Detect swing points
        swing_highs, swing_lows = self.detect_swing_points(df)
        all_swings = [(idx, price, time) for idx, price, time in swing_highs] + \
                    [(idx, -price, time) for idx, price, time in swing_lows]  # Negative for lows

        # Construct trendlines
        trendlines = self.construct_trendlines(all_swings)

        # Detect candle patterns
        patterns = self.detect_candle_patterns(df)

        # Get current price and recent levels
        current_price = df['close'].iloc[-1]
        recent_high = df['high'].iloc[-5:].max()
        recent_low = df['low'].iloc[-5:].min()

        # Check for breakouts and retests
        breakouts = self.check_breakouts(df, trendlines, current_price)
        retests = self.check_retests(df, trendlines, current_price, recent_high, recent_low)

        return {
            'swing_points': {'highs': swing_highs, 'lows': swing_lows},
            'trendlines': trendlines,
            'patterns': patterns,
            'breakouts': breakouts,
            'retests': retests,
            'current_price': current_price,
            'analysis_time': datetime.now()
        }

    def get_trading_signal(self, analysis_result):
        """Generate trading signal based on complete analysis."""
        signal_strength = 0
        signal_direction = 0
        reasons = []

        # Trendline breakouts (strong signal)
        for breakout in analysis_result['breakouts']:
            if breakout['strength'] >= 3:  # Strong trendline
                signal_strength += 2
                signal_direction += breakout['direction']
                reasons.append(f"Trendline breakout ({breakout['type']})")

        # Retests (confirmation signal)
        for retest in analysis_result['retests']:
            signal_strength += 1
            signal_direction += retest['direction']
            reasons.append(f"Trendline retest ({retest['type']})")

        # Candle patterns
        for pattern in analysis_result['patterns'][-3:]:  # Last 3 patterns
            if pattern['strength'] == 'Strong':
                signal_strength += 2
                signal_direction += pattern['direction']
                reasons.append(f"Candle pattern: {pattern['pattern']}")
            elif pattern['strength'] == 'Medium':
                signal_strength += 1
                signal_direction += pattern['direction']
                reasons.append(f"Candle pattern: {pattern['pattern']}")

        # Determine final signal
        if signal_strength >= 3:  # Minimum strength threshold
            direction = 1 if signal_direction > 0 else -1
            confidence = min(signal_strength / 6, 1.0)  # Max confidence 1.0

            return {
                'direction': direction,
                'strength': confidence,
                'reasons': reasons,
                'analysis': analysis_result
            }

        return None  # No strong signal
