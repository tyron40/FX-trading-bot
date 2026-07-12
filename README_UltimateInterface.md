# 🚀 Ultimate FX Trading Interface

A comprehensive, professional-grade FX trading interface that combines advanced algorithmic trading with an intuitive GUI. Features account toggling, integrated backtesting, and sophisticated bullish rejection blocks strategy.

## ✨ Features

### 🎛️ Account Management
- **Toggle between Demo and Live accounts** with one click
- **Secure connection handling** with automatic reconnection
- **Account balance and margin monitoring**

### 🧠 Advanced Trading Logic
- **Bullish Rejection Blocks Strategy**: Advanced candlestick pattern recognition for reversal detection
- **Multi-Strategy Analysis**: Combines trend following, momentum, and mean reversion
- **Weighted Scoring System**: Intelligent signal combination for optimal entry timing
- **Risk Management**: 1% risk per trade with automatic position sizing

### 📊 Real-Time Analysis
- **Live price charts** for all major FX pairs (EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD)
- **Real-time signal generation** with visual indicators
- **Strategy breakdown** showing individual strategy contributions
- **Continuous market analysis** with 30-second update cycles

### 🔬 Integrated Backtesting
- **Strategy backtesting** against historical data (2019-2023)
- **Performance metrics**: Total return, Sharpe ratio, max drawdown, win rate
- **Multiple strategies**: SMA, Bollinger Bands, Momentum, Bullish Rejection Blocks
- **Parameter optimization** capabilities

### 🎨 Professional GUI
- **Tabbed chart interface** for easy instrument switching
- **Real-time position tracking** with P&L monitoring
- **Trade history logging** with detailed statistics
- **Analysis log** with live signal updates
- **Performance dashboard** with key metrics

## 🛠️ Installation

### Prerequisites
```bash
pip install tkinter matplotlib pandas numpy tpqoa requests
```

### OANDA API Setup
1. Create OANDA demo account at [oanda.com](https://www.oanda.com)
2. Get your API key from the account settings
3. Configure `config/oanda_demo.cfg` and `config/oanda_live.cfg`:
```ini
[oanda]
account_id = YOUR_ACCOUNT_ID
access_token = YOUR_ACCESS_TOKEN
account_type = demo  # or live
```

## 🚀 Usage

### Launch the Interface
```bash
python run_ultimate_interface.py
```

### Getting Started
1. **Select Account**: Choose between Demo (safe testing) or Live (real trading)
2. **Wait for Connection**: Interface will connect to your OANDA account
3. **Run Backtests**: Test strategies on historical data before live trading
4. **Start Trading**: Enable automated trading with advanced logic
5. **Monitor Performance**: Watch real-time charts, positions, and analysis

### Trading Controls
- **▶️ Start Trading**: Begins automated trading with bullish rejection blocks
- **⏹️ Stop Trading**: Safely stops all trading activity
- **🔒 Close All Positions**: Emergency position closure
- **🔬 Run Backtest**: Test strategies on historical data

## 🧠 Trading Strategy Details

### Bullish Rejection Blocks
The core strategy identifies reversal patterns based on:
- **Long upper wicks** in downtrends (bullish rejection)
- **Long lower wicks** in uptrends (bearish rejection)
- **Wick-to-body ratios** exceeding configurable thresholds
- **Trend context** analysis for confirmation

### Multi-Strategy Integration
Combines four strategies with weighted scoring:
- **Bullish Rejection Blocks** (40% weight): Primary reversal detection
- **Trend Following** (30% weight): Moving average crossovers
- **Momentum** (20% weight): RSI-based overbought/oversold
- **Mean Reversion** (10% weight): Bollinger Band bounces

### Risk Management
- **1% risk per trade** based on account balance
- **0.5% stop loss** automatic position closure
- **1% take profit** target for winning trades
- **Maximum 1 position** at any time
- **Position sizing** based on volatility and risk parameters

## 📈 Performance Monitoring

### Real-Time Metrics
- **Balance**: Current account balance
- **Total Trades**: Number of completed trades
- **Win Rate**: Percentage of profitable trades
- **Total P&L**: Cumulative profit/loss
- **Avg Win/Loss**: Average profit/loss per trade

### Chart Analysis
- **Price candles** with 5-minute granularity
- **Signal indicators** (green BUY, red SELL lines)
- **Real-time updates** every 30 seconds
- **Multi-instrument tabs** for comprehensive view

## 🔧 Configuration

### Strategy Parameters
Modify strategy weights and parameters in `UltimateTradingInterface.py`:

```python
self._strategies = {
    'bullish_rejection': {'enabled': True, 'weight': 0.4, 'lookback': 20, 'wick_threshold': 0.6},
    'trend_following': {'enabled': True, 'weight': 0.3},
    'momentum': {'enabled': True, 'weight': 0.2},
    'mean_reversion': {'enabled': True, 'weight': 0.1}
}
```

### Risk Parameters
Adjust risk management settings:

```python
self._risk_per_trade = 0.01  # 1% risk per trade
self._stop_loss_pct = 0.5    # 0.5% stop loss
self._take_profit_pct = 1.0  # 1% take profit
```

## ⚠️ Important Notes

### Demo vs Live Trading
- **Demo Account**: Safe testing environment with virtual funds
- **Live Account**: Real money trading - use with caution
- Always test strategies on demo before live trading

### Risk Warning
- This software is for educational and research purposes
- Past performance does not guarantee future results
- Always trade with money you can afford to lose
- Consider consulting financial advisors

### Technical Requirements
- **Python 3.7+** required
- **Stable internet connection** for API access
- **OANDA account** with API access
- **Windows/Linux/Mac** compatible

## 🐛 Troubleshooting

### Connection Issues
- Verify API credentials in config files
- Check internet connection
- Ensure OANDA account has API access enabled

### GUI Issues
- Install all required dependencies
- Ensure matplotlib backend is compatible
- Check Python version compatibility

### Trading Issues
- Verify account has sufficient margin
- Check market hours (FX markets closed on weekends)
- Monitor account balance and margin requirements

## 📝 License

This project is for educational purposes. Use at your own risk.

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the interface.

---

**Happy Trading!** 🎯📈
