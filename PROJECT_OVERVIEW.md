# 📊 FXBot - Complete Project Overview

## 🎯 Project Purpose

**FXBot** is a comprehensive **Forex (Foreign Exchange) algorithmic trading platform** built in Python that enables users to:
- **Backtest** trading strategies on historical data
- **Execute live trades** automatically using the OANDA v20 API
- **Analyze markets** using multiple technical indicators and strategies
- **Manage risk** with sophisticated position sizing and stop-loss mechanisms
- **Visualize performance** through professional GUI interfaces

---

## 🏗️ Architecture Overview

### Core Technology Stack
```
├── Python 3.7+
├── OANDA v20 API (via tpqoa wrapper)
├── pandas/numpy (data analysis)
├── matplotlib (visualization)
├── tkinter (GUI)
├── scikit-learn (ML strategies)
└── feedparser/requests (news/sentiment)
```

### Project Structure
```
FXBot/
├── 📁 config/                    # OANDA API configurations
│   ├── oanda_demo.cfg           # Demo account credentials
│   ├── oanda_live.cfg           # Live account credentials
│   └── oanda_practice.cfg       # Practice account credentials
│
├── 📁 tpqoa/                     # OANDA API wrapper (submodule)
│   └── tpqoa/tpqoa.py           # Core API wrapper class
│
├── 📁 backtesting/               # Backtesting engine
│   ├── Backtester.py            # Base backtesting framework
│   ├── IterativeBase.py         # Iterative backtesting base
│   ├── IterativeBacktest.py     # Strategy-specific backtests
│   ├── SMABacktest.py           # SMA strategy backtest
│   ├── BollingerBandsBacktest.py
│   ├── MomentumBacktest.py
│   ├── ContrarianBacktest.py
│   └── MLClassificationBacktest.py
│
├── 📁 livetrading/               # Live trading implementations
│   ├── LiveTrader.py            # Base live trader class
│   ├── FemtoTrader.py           # Lightweight trader
│   ├── AutoTrader.py            # Automated trader
│   ├── BasicTrader.py           # Simple trader
│   ├── MicroTrader.py           # Micro-sized trader
│   ├── MiniTrader.py            # Mini-sized trader
│   ├── NanoTrader.py            # Nano-sized trader
│   ├── PicoTrader.py            # Pico-sized trader
│   └── [Strategy]Live.py        # Strategy-specific live traders
│
├── 📁 helpers/                   # Utility modules
│   ├── technical_analysis.py    # Advanced TA (trendlines, patterns)
│   ├── market_analyzer.py       # Market analysis utilities
│   ├── enhanced_market_analyzer.py
│   ├── super_market_analyzer.py
│   ├── rss_market_analyzer.py   # News sentiment analysis
│   └── helpers.py               # General utilities
│
├── 🎨 GUI Applications
│   ├── UltimateTradingInterface.py  # Most advanced GUI
│   ├── UltimateTrader.py            # Multi-strategy trader
│   ├── UltimateTrader_safe.py       # Safe version
│   ├── advanced_trading_gui.py      # Advanced GUI
│   ├── multi_instrument_gui.py      # Multi-instrument GUI
│   ├── trading_gui.py               # Basic GUI
│   └── chart_visualizer.py          # Chart visualization
│
├── 🚀 Runner Scripts
│   ├── run_ultimate_interface.py    # Launch ultimate interface
│   ├── run_ultimate_trader.py       # Launch ultimate trader
│   ├── run_trader_advanced.py       # Advanced trader runner
│   ├── run_trader_rss.py            # RSS-based trader
│   └── run_trader_trendlines.py     # Trendline trader
│
├── 🧪 Test Files
│   ├── test_connection.py
│   ├── test_ultimate_trader.py
│   ├── test_femto_trader_simple.py
│   └── test_analysis_methods.py
│
└── 📝 Documentation
    ├── README.md                    # Main documentation
    ├── README_UltimateTrader.md     # Ultimate Trader docs
    ├── README_UltimateInterface.md  # Ultimate Interface docs
    └── TODO_ENHANCEMENTS.md         # Planned enhancements
```

---

## 🧠 Core Components Explained

### 1. **tpqoa Wrapper** (`tpqoa/tpqoa/tpqoa.py`)
**Purpose**: Python wrapper for OANDA v20 API

**Key Features**:
- Account management (demo/practice/live)
- Price streaming (real-time tick data)
- Order execution (market/limit/stop orders)
- Historical data retrieval
- Position management
- Transaction history

**Key Methods**:
```python
get_prices(instrument)           # Get current bid/ask
stream_data(instrument)          # Stream real-time prices
create_order(instrument, units)  # Execute trades
get_history(instrument, ...)     # Get historical data
get_account_summary()            # Account balance/margin
```

### 2. **Backtesting Engine** (`backtesting/`)

#### **IterativeBase.py**
Base class for iterative (event-driven) backtesting:
- Simulates real trading tick-by-tick
- Tracks positions, balance, P&L
- Calculates performance metrics

#### **IterativeBacktest.py**
Implements specific strategy backtests:
- **SMA Crossover**: Moving average crossovers
- **Bollinger Bands**: Mean reversion strategy
- **Momentum**: Trend-following based on returns
- **Contrarian**: Counter-trend strategy
- **Bullish Rejection Blocks**: Candlestick reversal patterns

**Performance Metrics Calculated**:
- Total return %
- Annual return %
- Sharpe ratio
- Maximum drawdown
- Win rate
- Total trades

### 3. **Live Trading System** (`livetrading/`)

#### **Evolution of Traders** (from simple to complex):
1. **BasicTrader**: Simple buy/hold
2. **PicoTrader**: Minimal features
3. **NanoTrader**: Basic strategy
4. **MicroTrader**: Enhanced features
5. **MiniTrader**: More sophisticated
6. **FemtoTrader**: Lightweight but powerful
7. **AutoTrader**: Fully automated
8. **UltimateTrader**: Most advanced

#### **Key Features**:
- Real-time price streaming
- Automated signal generation
- Position management
- Risk management (stop-loss, take-profit)
- Multi-instrument support
- Performance tracking

### 4. **Trading Strategies**

#### **Technical Analysis Strategies**:

**A. SMA (Simple Moving Average) Crossover**
```
Signal: BUY when short MA > long MA
Signal: SELL when short MA < long MA
```

**B. Bollinger Bands**
```
Upper Band = SMA + (2 × StdDev)
Lower Band = SMA - (2 × StdDev)
Signal: BUY when price < lower band (oversold)
Signal: SELL when price > upper band (overbought)
```

**C. Momentum**
```
Signal: BUY when rolling returns > 0
Signal: SELL when rolling returns < 0
```

**D. Contrarian**
```
Signal: BUY when rolling returns < 0 (buy dips)
Signal: SELL when rolling returns > 0 (sell rallies)
```

**E. Bullish Rejection Blocks** (Advanced)
```
Identifies candlestick reversal patterns:
- Long upper wick + close near low = Bullish reversal
- Long lower wick + close near high = Bearish reversal
Considers trend context for confirmation
```

**F. Trendline Analysis** (`helpers/technical_analysis.py`)
```
- Detects swing highs/lows
- Constructs support/resistance trendlines
- Identifies breakouts and retests
- Recognizes candlestick patterns
```

**G. Sentiment Analysis** (`helpers/rss_market_analyzer.py`)
```
- Analyzes news feeds
- Sentiment scoring
- Market psychology indicators
```

### 5. **Ultimate Trading Interface** (`UltimateTradingInterface.py`)

**The Most Advanced Implementation** - Combines everything:

#### **Features**:
1. **Account Toggle**: Switch between demo/live accounts
2. **Multi-Strategy Analysis**: 
   - Bullish Rejection Blocks (40% weight)
   - Trend Following (30% weight)
   - Momentum (20% weight)
   - Mean Reversion (10% weight)
3. **Integrated Backtesting**: Test before trading
4. **Real-time Charts**: Live price visualization
5. **Risk Management**: 1% risk per trade, auto stop-loss
6. **Performance Tracking**: Win rate, Sharpe ratio, P&L

#### **Architecture**:
```python
UltimateTradingInterface
├── AdvancedTrader (extends tpqoa)
│   ├── Multi-strategy analysis
│   ├── Position management
│   ├── Risk calculation
│   └── Performance tracking
│
├── BacktestingEngine
│   ├── Strategy backtesting
│   ├── Parameter optimization
│   └── Performance metrics
│
└── GUI (tkinter)
    ├── Control panel
    ├── Live charts (matplotlib)
    ├── Position display
    ├── Performance metrics
    └── Trade history
```

#### **Trading Logic Flow**:
```
1. Get market data (5-min candles)
2. Analyze with multiple strategies:
   - Bullish rejection blocks
   - Trend following (SMA)
   - Momentum (RSI)
   - Mean reversion (Bollinger)
3. Calculate weighted score
4. Generate signal (BUY/SELL/HOLD)
5. If signal strong enough:
   - Calculate position size (1% risk)
   - Execute trade
   - Set stop-loss (0.5%)
   - Set take-profit (1%)
6. Monitor positions
7. Exit on stop/target/strategy reversal
```

---

## 🎮 How to Use the System

### **Setup**:
1. Install dependencies: `pip install -r requirements.txt`
2. Create OANDA account (demo recommended)
3. Get API credentials
4. Configure `config/oanda_demo.cfg`:
   ```ini
   [oanda]
   account_id = YOUR_ACCOUNT_ID
   access_token = YOUR_API_TOKEN
   account_type = demo
   ```

### **Run Backtests**:
```python
from backtesting.IterativeBacktest import IterativeBacktest

bt = IterativeBacktest("config/oanda_demo.cfg", "EUR_USD", 
                       "2019-01-01", "2023-01-01", 10000)
bt.test_sma(20, 50)  # Test SMA strategy
performance = bt.get_performance()
```

### **Run Live Trading** (Simple):
```python
from livetrading.FemtoTrader import FemtoTrader

trader = FemtoTrader("config/oanda_demo.cfg")
trader.start_trading("EUR_USD", timeframe="M5", units=100)
```

### **Run Ultimate Interface** (Recommended):
```bash
python run_ultimate_interface.py
```

**GUI Controls**:
- Select Demo/Live account
- Set timeframe (M1, M5, M15, H1, etc.)
- Set risk % and max positions
- Run backtests to validate strategies
- Start/Stop trading
- Monitor positions and performance

---

## 🛡️ Risk Management

### **Position Sizing**:
```python
risk_per_trade = 1.5% of account balance
position_size = (account_balance × risk_pct) / stop_loss_distance
max_position_size = 10% of account balance
```

### **Exit Strategies**:
- **Stop Loss**: 0.5% automatic exit
- **Take Profit**: 1% profit target
- **Strategy Exit**: Signal reversal
- **Time Exit**: Max holding period

### **Portfolio Limits**:
- Max 5 concurrent positions
- Max 7.5% total exposure
- Diversification across instruments

---

## 📊 Supported Instruments

**Major Currency Pairs**:
- EUR_USD (Euro/US Dollar)
- GBP_USD (British Pound/US Dollar)
- USD_JPY (US Dollar/Japanese Yen)
- USD_CHF (US Dollar/Swiss Franc)
- AUD_USD (Australian Dollar/US Dollar)

**Timeframes**:
- M1 (1 minute)
- M5 (5 minutes)
- M15 (15 minutes)
- M30 (30 minutes)
- H1 (1 hour)
- H4 (4 hours)
- D (Daily)

---

## 🔧 Configuration Files

### **OANDA Config** (`config/oanda_*.cfg`):
```ini
[oanda]
account_id = 123-456-7890123-001
access_token = abc123def456...
account_type = demo  # or 'live'
```

### **Settings** (`settings.json`):
```json
{
  "default_instrument": "EUR_USD",
  "default_timeframe": "M5",
  "risk_per_trade": 1.0,
  "max_positions": 3
}
```

---

## 🧪 Testing

### **Test Files**:
- `test_connection.py`: Verify OANDA API connection
- `test_ultimate_trader.py`: Test ultimate trader functionality
- `test_femto_trader_simple.py`: Test FemtoTrader
- `test_analysis_methods.py`: Test analysis methods

### **Run Tests**:
```bash
python test_connection.py
python test_ultimate_trader.py
```

---

## 📈 Performance Metrics

### **Calculated Metrics**:
- **Total Return**: Overall profit/loss %
- **Annual Return**: Annualized return %
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest peak-to-trough decline
- **Win Rate**: % of profitable trades
- **Avg Win/Loss**: Average profit/loss per trade
- **Total Trades**: Number of completed trades

---

## 🚀 Evolution of the Project

### **Version History** (inferred from files):
1. **v1.0**: Basic trading (`main.py`, `BasicTrader`)
2. **v2.0**: Multiple strategies (`SMABacktest`, `BollingerBands`)
3. **v3.0**: Advanced traders (`FemtoTrader`, `AutoTrader`)
4. **v4.0**: GUI interfaces (`trading_gui.py`)
5. **v5.0**: Advanced analysis (`technical_analysis.py`, trendlines)
6. **v6.0**: Ultimate implementations (`UltimateTrader`, `UltimateInterface`)
7. **v7.0**: Enhancements (RSS sentiment, ML strategies)

---

## 🎯 Key Innovations

### **1. Bullish Rejection Blocks Strategy**
Advanced candlestick pattern recognition for reversal detection:
- Analyzes wick-to-body ratios
- Considers trend context
- Identifies high-probability reversals

### **2. Multi-Strategy Weighted Scoring**
Combines multiple strategies with configurable weights:
```python
strategies = {
    'bullish_rejection': 40%,
    'trend_following': 30%,
    'momentum': 20%,
    'mean_reversion': 10%
}
```

### **3. Integrated Backtesting**
Test strategies before live trading within the same interface

### **4. Account Toggle**
Seamlessly switch between demo and live accounts

### **5. Real-time Analysis**
Continuous market analysis with 30-second update cycles

---

## ⚠️ Important Notes

### **Risk Warning**:
- Forex trading involves substantial risk
- Past performance ≠ future results
- Use demo account for testing
- Never trade money you can't afford to lose

### **Best Practices**:
1. **Always start with demo account**
2. **Backtest strategies thoroughly**
3. **Start with small position sizes**
4. **Monitor performance regularly**
5. **Adjust strategies based on results**
6. **Keep detailed trade logs**

---

## 🔮 Planned Enhancements (from TODO)

1. **Timeframe Selection**: Dynamic timeframe switching
2. **Trade Size Controls**: Advanced position sizing
3. **OpenAI Integration**: AI-powered trading recommendations
4. **Enhanced UI/UX**: Improved interface design
5. **Additional Strategies**: More trading algorithms
6. **Portfolio Optimization**: Advanced position allocation

---

## 📚 Key Files to Understand

### **For Beginners**:
1. `README.md` - Project overview
2. `main.py` - Simple entry point
3. `livetrading/BasicTrader.py` - Simple trader
4. `backtesting/SMABacktest.py` - Simple backtest

### **For Advanced Users**:
1. `UltimateTradingInterface.py` - Complete system
2. `helpers/technical_analysis.py` - Advanced TA
3. `backtesting/IterativeBacktest.py` - Strategy backtests
4. `tpqoa/tpqoa/tpqoa.py` - API wrapper

### **For Developers**:
1. `backtesting/IterativeBase.py` - Backtesting framework
2. `livetrading/LiveTrader.py` - Live trading base
3. `helpers/market_analyzer.py` - Analysis utilities

---

## 🎓 Learning Path

### **Level 1: Beginner**
1. Understand forex basics
2. Run backtests with `IterativeBacktest`
3. Test connection with `test_connection.py`
4. Try `BasicTrader` on demo account

### **Level 2: Intermediate**
1. Explore different strategies
2. Modify strategy parameters
3. Run `FemtoTrader` with custom settings
4. Analyze performance metrics

### **Level 3: Advanced**
1. Use `UltimateTradingInterface`
2. Implement custom strategies
3. Optimize parameters
4. Combine multiple strategies

### **Level 4: Expert**
1. Develop new strategies
2. Integrate ML models
3. Build custom analyzers
4. Contribute to project

---

## 🤝 Contributing

The project welcomes contributions:
- New trading strategies
- Performance improvements
- Bug fixes
- Documentation enhancements
- Testing improvements

---

## 📄 License

Educational and research purposes only. See LICENSE file.

---

## 🎯 Summary

**FXBot** is a comprehensive, production-ready forex trading platform that combines:
- ✅ Professional-grade backtesting
- ✅ Multiple trading strategies
- ✅ Real-time automated trading
- ✅ Advanced technical analysis
- ✅ Risk management
- ✅ Performance tracking
- ✅ User-friendly GUI
- ✅ Demo/Live account support

**Perfect for**: Algorithmic traders, quant developers, forex enthusiasts, and anyone interested in automated trading systems.

**Start with**: `run_ultimate_interface.py` for the complete experience!

---

*Last Updated: 2024*
*Project Status: Active Development*
