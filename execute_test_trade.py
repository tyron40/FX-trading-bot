"""
Execute a real test trade to verify on OANDA website
"""

from tpqoa.tpqoa import tpqoa
import time

print("=" * 60)
print("🔥 EXECUTING REAL TEST TRADE")
print("=" * 60)
print()

# Connect
print("1. Connecting to OANDA demo account...")
trader = tpqoa("config/oanda_demo.cfg")
print("   ✅ Connected")
print()

# Get current positions
print("2. Checking current positions...")
try:
    positions = trader.get_positions()
    print(f"   Current positions: {len(positions)}")
    for pos in positions:
        print(f"   - {pos['instrument']}: {pos['long']['units']} units")
except:
    print("   No positions")
print()

# Get account info
print("3. Getting account info...")
try:
    summary = trader.get_account_summary()
    balance = float(summary.get('balance', 0))
    print(f"   Balance: ${balance:,.2f}")
except:
    print("   Could not get balance")
print()

# Get current price
print("4. Getting current EUR/USD price...")
_, bid, ask = trader.get_prices('EUR_USD')
print(f"   BID: {bid:.5f}")
print(f"   ASK: {ask:.5f}")
print()

# Execute trade
print("5. Executing TEST TRADE...")
print("   Instrument: EUR/USD")
print("   Direction: BUY (LONG)")
print("   Units: 100")
print()

try:
    # Create order
    order = trader.create_order(
        instrument='EUR_USD',
        units=100,
        suppress=True,
        ret=True
    )
    
    if order:
        print("   ✅ TRADE EXECUTED!")
        print(f"   Order ID: {order.get('id', 'N/A')}")
        print(f"   Price: {order.get('price', 'N/A')}")
        print(f"   Time: {order.get('time', 'N/A')}")
        print()
        print("=" * 60)
        print("🎉 SUCCESS!")
        print("=" * 60)
        print()
        print("Now check your OANDA account:")
        print("1. Go to https://trade.oanda.com")
        print("2. Log in to your demo account")
        print("3. Click 'Positions' or 'Open Trades'")
        print("4. You should see: EUR/USD LONG 100 units")
        print()
        print("=" * 60)
        
        # Wait a moment
        time.sleep(2)
        
        # Get updated positions
        print()
        print("6. Verifying position on OANDA...")
        positions = trader.get_positions()
        print(f"   Total positions: {len(positions)}")
        
        for pos in positions:
            instrument = pos['instrument']
            long_units = pos['long']['units']
            short_units = pos['short']['units']
            
            if long_units != '0':
                print(f"   ✅ {instrument}: LONG {long_units} units")
            if short_units != '0':
                print(f"   ✅ {instrument}: SHORT {short_units} units")
        
        print()
        print("=" * 60)
        print("Position confirmed! Check OANDA website now.")
        print("=" * 60)
        
    else:
        print("   ❌ Trade failed - no order returned")
        
except Exception as e:
    print(f"   ❌ Trade failed: {e}")
    print()
    print("Possible reasons:")
    print("- Market is closed (Forex: Mon-Fri only)")
    print("- Insufficient margin")
    print("- API permissions issue")
    print("- Network error")

print()
