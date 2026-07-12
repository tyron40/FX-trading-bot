import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np
from datetime import datetime

class ChartVisualizer:
    def __init__(self):
        self.fig, self.ax = plt.subplots(figsize=(14, 8))
        self.price_data = None
        self.trendlines = []
        self.patterns = []
        self.current_position = None

    def update_chart(self, price_data, trendlines=None, patterns=None, current_position=None):
        """Update the chart with new data and overlays."""
        self.price_data = price_data
        self.trendlines = trendlines or []
        self.patterns = patterns or []
        self.current_position = current_position

        self._draw_chart()

    def _draw_chart(self):
        """Draw the complete chart with all overlays."""
        if self.price_data is None or len(self.price_data) == 0:
            return

        self.ax.clear()

        # Plot candlestick chart
        self._plot_candles()

        # Plot trendlines
        self._plot_trendlines()

        # Plot patterns
        self._plot_patterns()

        # Plot position marker
        if self.current_position:
            self._plot_position()

        # Format chart
        self._format_chart()

        # Refresh display
        plt.draw()
        plt.pause(0.1)

    def _plot_candles(self):
        """Plot candlestick chart."""
        df = self.price_data

        for idx, row in df.iterrows():
            # Determine candle color
            color = 'green' if row['close'] >= row['open'] else 'red'

            # Plot high-low line
            self.ax.plot([idx, idx], [row['low'], row['high']], color='black', linewidth=1)

            # Plot open-close body
            body_height = abs(row['close'] - row['open'])
            body_bottom = min(row['open'], row['close'])
            body_width = 0.6

            self.ax.add_patch(Rectangle(
                (idx - body_width/2, body_bottom),
                body_width,
                body_height,
                facecolor=color,
                edgecolor='black',
                linewidth=1
            ))

    def _plot_trendlines(self):
        """Plot trendlines on the chart."""
        if not self.trendlines:
            return

        df = self.price_data
        indices = np.arange(len(df))

        for line in self.trendlines:
            slope = line['slope']
            intercept = line['intercept']

            # Calculate trendline points
            x_points = indices
            y_points = slope * x_points + intercept

            # Plot trendline
            color = 'blue' if line['type'] == 'support' else 'red'
            linestyle = '--' if line['strength'] < 4 else '-'
            linewidth = 1 + (line['strength'] - 3) * 0.5 if line['strength'] >= 3 else 1

            self.ax.plot(df.index, y_points, color=color, linestyle=linestyle,
                        linewidth=linewidth, alpha=0.8,
                        label=f"{line['type'].title()} ({line['strength']} points)")

    def _plot_patterns(self):
        """Plot candle pattern markers."""
        if not self.patterns:
            return

        df = self.price_data

        for pattern in self.patterns:
            idx = pattern['index']
            if idx >= len(df):
                continue

            price = df.iloc[idx]['close']
            direction = pattern['direction']

            # Choose marker based on pattern type and direction
            if 'Engulfing' in pattern['pattern']:
                marker = '^' if direction > 0 else 'v'
                color = 'green' if direction > 0 else 'red'
                size = 100
            elif 'Star' in pattern['pattern']:
                marker = '*' if direction > 0 else '*'
                color = 'green' if direction > 0 else 'red'
                size = 150
            elif 'Hammer' in pattern['pattern'] or 'Pin' in pattern['pattern']:
                marker = 'D' if direction > 0 else 'd'
                color = 'green' if direction > 0 else 'red'
                size = 80
            elif 'Doji' in pattern['pattern']:
                marker = 'o'
                color = 'gray'
                size = 60
            else:
                marker = 's'
                color = 'orange'
                size = 50

            # Plot pattern marker
            self.ax.scatter(df.index[idx], price, marker=marker, color=color,
                          s=size, alpha=0.8, edgecolors='black',
                          label=f"{pattern['pattern']} ({pattern['strength']})")

    def _plot_position(self):
        """Plot current position marker."""
        if not self.current_position or not self.price_data:
            return

        df = self.price_data
        entry_price = self.current_position['entry_price']
        position_type = self.current_position['type']

        # Plot entry line
        color = 'green' if position_type == 'long' else 'red'
        linestyle = '--'

        self.ax.axhline(y=entry_price, color=color, linestyle=linestyle,
                       linewidth=2, alpha=0.7,
                       label=f"Entry: {position_type.upper()} @ {entry_price:.5f}")

        # Add position info text
        last_price = df.iloc[-1]['close']
        y_pos = entry_price + (last_price - entry_price) * 0.1

        self.ax.text(df.index[-1], y_pos,
                    f"{position_type.upper()}\n{self.current_position['units']} units",
                    fontsize=10, ha='right', va='bottom',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor=color, alpha=0.7))

    def _format_chart(self):
        """Format the chart appearance."""
        self.ax.set_title('EUR/USD Advanced Analysis Chart', fontsize=16, fontweight='bold')
        self.ax.set_xlabel('Time', fontsize=12)
        self.ax.set_ylabel('Price (USD)', fontsize=12)

        # Format x-axis dates
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        self.ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45)

        # Add grid
        self.ax.grid(True, alpha=0.3)

        # Add legend
        if self.trendlines or self.patterns or self.current_position:
            self.ax.legend(loc='upper left', fontsize=10)

        # Adjust layout
        plt.tight_layout()

    def show(self):
        """Show the chart (blocking)."""
        plt.show()

    def save_chart(self, filename="chart.png"):
        """Save chart to file."""
        self.fig.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Chart saved as {filename}")

    def get_chart_data(self):
        """Get current chart data for GUI integration."""
        return {
            'price_data': self.price_data,
            'trendlines': self.trendlines,
            'patterns': self.patterns,
            'position': self.current_position
        }

# Example usage
if __name__ == "__main__":
    # Create sample data for testing
    dates = pd.date_range('2024-01-01 10:00', periods=50, freq='1min')
    np.random.seed(42)

    # Generate sample price data
    base_price = 1.0850
    prices = []
    for i in range(50):
        change = np.random.normal(0, 0.0005)
        base_price += change
        high = base_price + abs(np.random.normal(0, 0.0002))
        low = base_price - abs(np.random.normal(0, 0.0002))
        open_price = prices[-1]['close'] if prices else base_price
        close = base_price

        prices.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close
        })

    df = pd.DataFrame(prices, index=dates)

    # Create visualizer
    viz = ChartVisualizer()

    # Sample trendlines
    trendlines = [
        {
            'type': 'support',
            'slope': 0.0001,
            'intercept': 1.0820,
            'points': [(10, 1.0830), (20, 1.0840), (30, 1.0850)],
            'strength': 4
        },
        {
            'type': 'resistance',
            'slope': -0.00005,
            'intercept': 1.0880,
            'points': [(15, 1.0873), (25, 1.0868), (35, 1.0863)],
            'strength': 3
        }
    ]

    # Sample patterns
    patterns = [
        {
            'index': 20,
            'pattern': 'Bullish Engulfing',
            'direction': 1,
            'strength': 'Strong'
        },
        {
            'index': 35,
            'pattern': 'Hammer',
            'direction': 1,
            'strength': 'Medium'
        }
    ]

    # Update chart
    viz.update_chart(df, trendlines, patterns)

    # Save chart
    viz.save_chart("sample_chart.png")

    print("Chart visualization example completed!")
