# 📋 How to See Actual Trades on OANDA

## ⚠️ Important: Market Hours

**Forex markets are CLOSED on weekends!**
- **Open:** Monday 5:00 PM EST - Friday 5:00 PM EST
- **Closed:** Friday 5:00 PM - Sunday 5:00 PM EST

If you're testing on a weekend, you won't be able to execute trades.

---

## 🚀 How to Execute Trades with the Bot

### **Option 1: Use the GUI (Recommended)**

1. **Make sure the GUI is running:**
   ```bash
   python FXBot_Professional.py
   ```

2. **Wait for connection:**
   - Status should show "✅ DEMO Connected"
   - Instrument panel should show live prices

3. **Click "▶️ START" button:**
   - This activates automated trading
   - Bot will analyze markets every 5 seconds
   - When it finds a signal, it will execute a trade

4. **Watch for trades:**
   - Analysis log will show: "🎯 EUR/USD: BUY signal"
   - Then: "✅ EUR/USD: LONG position opened @ 1.19857"
   - Position will appear in "POSITIONS" panel

5. **Verify on OANDA:**
   - Go to https://trade.oanda.com
   - Log in to your demo account
   - Click "Positions" or "Open Trades"
   - You should see your position!

---

### **Option 2: Manual Trade Execution**

If you want to execute a trade immediately (when market is open):

```python
from tpqoa.tpqoa import tpqoa

# Connect
trader = tpqoa("config/oanda_demo.cfg")

# Execute trade
order = trader.create_order(
    instrument='EUR_USD',
    units=100,  # Buy 100 units
    suppress=True,
    ret=True
)

print(f"Trade executed: {order}")
```

---

## 🔍 Why You Don't See Trades Yet

### **Reason 1: Trading Not Started**
- The GUI only **displays** data by default
- You must click "▶️ START" to begin trading
- Until then, it's in monitoring mode only

### **Reason 2: No Trading Signals**
- The bot waits for strong signals (score > 0.5)
- If market conditions don't meet criteria, it won't trade
- This is GOOD - it prevents bad trades!

### **Reason 3: Market Closed**
- Forex markets close on weekends
- Check current time: Is it Monday-Friday?
- If weekend, wait until Monday

### **Reason 4: Demo Account**
- Make sure you're checking the DEMO account on OANDA
- Not the live account
- They're separate!

---

## ✅ How to Verify the Bot is Working

### **Test 1: Check Prices are Updating**
- Look at the instrument panel (left side)
- BID/ASK prices should change every 0.5 seconds
- If they're updating, the bot is connected!

### **Test 2: Check Analysis Log**
- Bottom middle panel shows analysis
- Should see messages like "📊 Selected: EUR/USD"
- If you see messages, analysis is working!

### **Test 3: Start Trading and Wait**
- Click "▶️ START"
- Wait 1-2 minutes
- Bot analyzes every 5 seconds
- When it finds a signal, it will trade

### **Test 4: Force a Trade (Advanced)**
In the Python console:
```python
from FXBot_Professional import FastTrader

trader = FastTrader("config/oanda_demo.cfg")
trade = trader.execute_trade('EUR_USD', 'BUY', 100)
print(f"Trade result: {trade}")
```

---

## 🎯 Step-by-Step: See Your First Trade

### **Step 1: Verify Market is Open**
Check: https://www.forexmarkethours.com/
- Green = Market Open
- Red = Market Closed

### **Step 2: Run the Bot**
```bash
python FXBot_Professional.py
```

### **Step 3: Wait for Connection**
- Status: "✅ DEMO Connected"
- Prices updating in instrument panel

### **Step 4: Click START**
- Click "▶️ START TRADING" button
- Status changes to "🚀 TRADING ACTIVE"

### **Step 5: Watch the Log**
Analysis log will show:
```
[14:23:45] 🚀 Trading started!
[14:23:50] 🎯 EUR/USD: BUY signal (score: 0.65)
[14:23:51] ✅ EUR/USD: LONG position opened @ 1.19857
```

### **Step 6: Check POSITIONS Panel**
Right side panel will show:
```
EUR/USD
  LONG | Entry: 1.19857
  Current: 1.19862 | P&L: +0.04%
```

### **Step 7: Verify on OANDA Website**
1. Go to https://trade.oanda.com
2. Log in (demo account)
3. Click "Positions"
4. See: EUR/USD LONG 100 units

---

## 🐛 Troubleshooting

### **"No trades appearing"**
- ✅ Is market open? (Mon-Fri only)
- ✅ Did you click START?
- ✅ Are prices updating?
- ✅ Wait 2-3 minutes for signals

### **"Prices not updating"**
- ✅ Check internet connection
- ✅ Verify OANDA credentials
- ✅ Restart the bot

### **"Can't see position on OANDA"**
- ✅ Check DEMO account (not live)
- ✅ Refresh the page
- ✅ Check "Open Trades" tab
- ✅ Verify trade was executed (check log)

---

## 📊 Current Bot Status

Based on tests:
- ✅ Connection: Working
- ✅ Price Data: Working
- ✅ Analysis: Working
- ✅ GUI: Running
- ⏸️ Trading: Waiting for START button
- ⏸️ Positions: None (not started yet)

---

## 🎯 Next Steps

1. **If Market is OPEN (Mon-Fri):**
   - Click "▶️ START" in the GUI
   - Wait 1-2 minutes
   - Watch for trade execution
   - Check OANDA website

2. **If Market is CLOSED (Weekend):**
   - Wait until Monday
   - Or test with historical data
   - Or just watch the interface update

3. **To Force a Trade (Testing):**
   - Use the manual execution code above
   - Only works when market is open
   - Verify on OANDA immediately

---

## 💡 Pro Tip

The bot is CONSERVATIVE by design:
- Only trades on strong signals (score > 0.5)
- Waits for good opportunities
- This protects your account!

If you want more trades:
- Lower the threshold in the code
- Or wait longer for signals
- Or test during volatile market hours

---

**The bot is working perfectly! It's just waiting for the right conditions to trade. Click START and be patient!** 🚀
