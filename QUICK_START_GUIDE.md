# 🚀 FXBot Quick Start Guide

## ⚡ Get Trading in 5 Minutes!

This guide will get you from zero to running your first automated forex trading bot.

---

## 📋 Prerequisites Checklist

- [ ] Python 3.7 or higher installed
- [ ] pip package manager
- [ ] OANDA account (free demo account recommended)
- [ ] Internet connection
- [ ] Basic understanding of forex trading

---

## 🎯 Step-by-Step Setup

### **Step 1: Clone the Repository**

```bash
git clone --recurse-submodules -j8 https://github.com/tyron40/FX-trading-bot.git
cd FX-trading-bot
```

> **Note**: The `--recurse-submodules` flag is important! It includes the tpqoa submodule.

---

### **Step 2: Install Dependencies**

```bash
pip install -r requirements.txt
```

**Required packages**:
- v20 (OANDA API)
- pandas
- numpy
- matplotlib
- scikit-learn
- yfinance

---

### **Step 3: Create OANDA Account**

1. **Go to**: [https://www.oanda.com](https://www.oanda.com)
2. **Sign up** for a free practice account
3. **Navigate to**: Account Settings → API Access
4. **Generate** an API token
5. **Copy** your Account ID and API Token

**Important**: Start with a **DEMO/PRACTICE** account, not live!

---

### **Step 4: Configure API Credentials**

Create a file: `config/oanda_demo.cfg`

```ini
[oanda]
account_id = 101-004-1234567-001
access_token = abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
account_type = demo
```

**Replace with your actual credentials!**

---

### **Step 5: Test Connection**

```bash
python test_connection.py
```

**Expected output**:
```
✅ Connection successful!
Account ID: 101-004-1234567-001
Balance: $100,000.00
Currency: USD
```

If you see errors, double-check your credentials in `config/oanda_demo.cfg`.

---

## 🎮 Choose Your Adventure

### **Option A: Ultimate Trading Interface** (Recommended for Beginners)

**Best for**: Complete trading experience with GUI

```bash
python run_ultimate_interface.py
```

**What you get**:
- ✅ Professional GUI interface
- ✅ Real-time charts for 5 currency pairs
- ✅ Integrated backtesting
- ✅ Multi-strategy analysis
- ✅ Live position tracking
- ✅ Performance metrics

**How to use**:
1. Interface opens automatically
2. Select "Demo" account (should be default)
3. Click "Run Backtest" to test strategies
4. Review backtest results
5. Click "Start Trading" to go live (on demo!)
6. Monitor positions and performance

---

### **Option B: Simple Backtest** (Learn the Strategies)

**Best for**: Understanding how strategies work

```python
# Create file: my_first_backtest.py
from backtesting.IterativeBacktest import IterativeBacktest

# Initialize backtester
bt = IterativeBacktest(
    conf_file="config/oanda_demo.cfg",
    instrument="EUR_USD",
    start="2022-01-01",
    end="2023-01-01",
    amount=10000
)

# Test SMA strategy
bt.test_sma(smas=20, smal=50)

# Get results
performance = bt.get_performance()
print(f"Total Return: {performance['total_return']:.2f}%")
print(f"Sharpe Ratio: {performance['sharpe_ratio']:.2f}")
print(f"Win Rate: {performance['win_rate']:.1%}")
```

Run it:
```bash
python my_first_backtest.py
```

---

### **Option C: Simple Live Trading** (Advanced Users)

**Best for**: Quick automated trading

```python
# Create file: my_first_trader.py
from livetrading.FemtoTrader import FemtoTrader

# Initialize trader
trader = FemtoTrader(
    conf_file="config/oanda_demo.cfg",
    instrument="EUR_USD",
    bar_length="5min",
    units=100
)

# Start trading
print("Starting automated trading...")
trader.start_trading()

# Let it run (Ctrl+C to stop)
```

Run it:
```bash
python my_first_trader.py
```

**⚠️ Warning**: This will start live trading on your demo account!

---

## 📊 Understanding the Results

### **Backtest Metrics Explained**

```
Total Return: 15.5%        # Overall profit/loss
Annual Return: 12.3%       # Annualized return
Sharpe Ratio: 1.8          # Risk-adjusted return (>1 is good)
Max Drawdown: -8.2%        # Worst peak-to-trough decline
Win Rate: 58.3%            # Percentage of winning trades
Total Trades: 127          # Number of trades executed
```

**Good Strategy Indicators**:
- ✅ Positive total return
- ✅ Sharpe ratio > 1.0
- ✅ Win rate > 50%
- ✅ Max drawdown < 20%

---

## 🎯 Your First Trading Session

### **Recommended Workflow**:

1. **Test Connection** ✅
   ```bash
   python test_connection.py
   ```

2. **Run Backtests** 📊
   ```bash
   python run_ultimate_interface.py
   # Click "Run Backtest" button
   ```

3. **Analyze Results** 🔍
   - Review performance metrics
   - Check win rate
   - Examine drawdown
   - Compare strategies

4. **Start Demo Trading** 🚀
   - Click "Start Trading"
   - Monitor for 1-2 hours
   - Observe position management
   - Check P&L

5. **Review Performance** 📈
   - Check trade history
   - Analyze winning/losing trades
   - Adjust parameters if needed

---

## 🛠️ Common Issues & Solutions

### **Issue 1: "Module not found" error**

**Solution**:
```bash
pip install -r requirements.txt --upgrade
```

---

### **Issue 2: "Invalid credentials" error**

**Solution**:
1. Verify credentials in `config/oanda_demo.cfg`
2. Ensure no extra spaces
3. Check account type is "demo" not "practice" or "live"
4. Regenerate API token if needed

---

### **Issue 3: "No data returned" error**

**Solution**:
- Check internet connection
- Verify instrument name (use underscore: EUR_USD not EUR/USD)
- Ensure market is open (Forex: 24/5, closed weekends)

---

### **Issue 4: GUI doesn't open**

**Solution**:
```bash
# Install tkinter
# Ubuntu/Debian:
sudo apt-get install python3-tk

# macOS:
brew install python-tk

# Windows: Usually included with Python
```

---

## 📚 Next Steps

### **Beginner Path** 🌱

1. ✅ Run backtests on different strategies
2. ✅ Compare SMA vs Bollinger Bands vs Momentum
3. ✅ Test different timeframes (M5, M15, H1)
4. ✅ Experiment with different currency pairs
5. ✅ Run demo trading for 1 week

### **Intermediate Path** 🌿

1. ✅ Modify strategy parameters
2. ✅ Combine multiple strategies
3. ✅ Implement custom risk management
4. ✅ Track performance over time
5. ✅ Optimize parameters using backtests

### **Advanced Path** 🌳

1. ✅ Create custom strategies
2. ✅ Implement machine learning models
3. ✅ Build custom analyzers
4. ✅ Integrate news sentiment
5. ✅ Develop portfolio optimization

---

## 🎓 Learning Resources

### **Understanding Strategies**

**SMA (Simple Moving Average)**:
- Read: `backtesting/SMABacktest.py`
- Concept: Buy when short MA crosses above long MA
- Best for: Trending markets

**Bollinger Bands**:
- Read: `backtesting/BollingerBandsBacktest.py`
- Concept: Buy oversold, sell overbought
- Best for: Ranging markets

**Bullish Rejection Blocks**:
- Read: `backtesting/IterativeBacktest.py` (test_bullish_rejection_blocks)
- Concept: Candlestick reversal patterns
- Best for: Reversal trading

### **Key Files to Study**

1. **For Strategy Understanding**:
   - `backtesting/IterativeBacktest.py`
   - `helpers/technical_analysis.py`

2. **For Live Trading**:
   - `livetrading/FemtoTrader.py`
   - `UltimateTradingInterface.py`

3. **For API Usage**:
   - `tpqoa/tpqoa/tpqoa.py`

---

## 🔒 Safety Reminders

### **Golden Rules**:

1. **ALWAYS start with demo account** 🛡️
2. **NEVER trade money you can't afford to lose** 💰
3. **Test strategies thoroughly before live trading** 🧪
4. **Start with small position sizes** 📏
5. **Monitor your bot regularly** 👀
6. **Keep detailed logs** 📝
7. **Understand the risks** ⚠️

### **Risk Management Checklist**:

- [ ] Using demo account
- [ ] Position size < 1% of balance
- [ ] Stop loss set on all trades
- [ ] Maximum 3-5 concurrent positions
- [ ] Daily loss limit defined
- [ ] Regular performance reviews scheduled

---

## 🎯 Quick Reference Commands

```bash
# Test connection
python test_connection.py

# Run ultimate interface (GUI)
python run_ultimate_interface.py

# Run ultimate trader (no GUI)
python run_ultimate_trader.py

# Run simple backtest
python -c "from backtesting.IterativeBacktest import IterativeBacktest; \
bt = IterativeBacktest('config/oanda_demo.cfg', 'EUR_USD', '2022-01-01', '2023-01-01', 10000); \
bt.test_sma(20, 50); print(bt.get_performance())"

# Test specific trader
python test_femto_trader_simple.py

# Run with RSS sentiment
python run_trader_rss.py

# Run with trendline analysis
python run_trader_trendlines.py
```

---

## 📞 Getting Help

### **If you're stuck**:

1. **Check documentation**:
   - `README.md`
   - `PROJECT_OVERVIEW.md`
   - `ARCHITECTURE_DIAGRAM.md`

2. **Review examples**:
   - Test files in root directory
   - Example traders in `livetrading/`

3. **Common solutions**:
   - Restart the application
   - Check API credentials
   - Verify internet connection
   - Update dependencies

4. **Debug mode**:
   ```python
   # Add to your script
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

---

## 🎉 Success Checklist

After completing this guide, you should be able to:

- [x] Connect to OANDA API
- [x] Run backtests on historical data
- [x] Understand strategy performance metrics
- [x] Launch the Ultimate Trading Interface
- [x] Start automated demo trading
- [x] Monitor positions and P&L
- [x] Analyze trading performance

---

## 🚀 You're Ready!

**Congratulations!** You now have a working forex trading bot. 

**Remember**:
- Start small
- Learn continuously
- Test thoroughly
- Trade responsibly

**Happy Trading!** 📈💰🎯

---

## 📖 What's Next?

1. **Read**: `PROJECT_OVERVIEW.md` for complete understanding
2. **Study**: `ARCHITECTURE_DIAGRAM.md` for system design
3. **Explore**: Different strategies and parameters
4. **Experiment**: Create your own custom strategies
5. **Optimize**: Fine-tune for better performance

---

*Last Updated: 2024*
*Difficulty: Beginner-Friendly*
*Time to Complete: 5-10 minutes*
