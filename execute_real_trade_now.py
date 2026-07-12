"""
Execute a REAL trade on OANDA to verify it appears on the website
"""

from tpqoa.tpqoa import tpqoa
import time

def execute_test_trade():
    """Execute a small test trade"""
    print("\n" + "="*60)
    print("🚀 EXECUTING REAL TRADE TEST")
    print("="*60)
    
    try:
        # Connect to demo account
        print("\n1️⃣ Connecting to OANDA demo account...")
        trader = tpqoa("config/oanda_demo.cfg")
        print("   ✅ Connected!")
        
        # Get account info
        print("\n2️⃣ Getting account information...")
        summary = trader.get_account_summary(detailed=True)
        balance = float(summary.get('balance', 0))
        print(f"   💰 Account Balance: ${balance:,.2f}")
        
        # Get current price
        print("\n3️⃣ Getting current EUR/USD price...")
        instrument = "EUR_USD"
        _, bid, ask = trader.get_prices(instrument)
        print(f"   📊 {instrument}: BID={bid:.5f}, ASK={ask:.5f}")
        
        # Execute a SMALL test trade
        print("\n4️⃣ Executing SMALL test trade...")
        print(f"   📝 Instrument: {instrument}")
        print(f"   📝 Direction: LONG (BUY)")
        print(f"   📝 Units: 100 (very small)")
        
        # Create the order
        order = trader.create_order(
            instrument=instrument,
            units=100,  # Small position
            suppress=True,
            ret=True
        )
        
        if order:
            print("\n   ✅ TRADE EXECUTED SUCCESSFULLY!")
            print(f"   📋 Order ID: {order.get('id', 'N/A')}")
            print(f"   💵 Entry Price: {order.get('price', 'N/A')}")
            print(f"   📊 Units: {order.get('units', 'N/A')}")
            
            # Get positions to confirm
            print("\n5️⃣ Verifying position on OANDA...")
            time.sleep(2)  # Wait for order to settle
            
            positions = trader.get_positions()
            print(f"   📊 Total Open Positions: {len(positions)}")
            
            for pos in positions:
                inst = pos.get('instrument', 'N/A')
                long_units = pos.get('long', {}).get('units', '0')
                short_units = pos.get('short', {}).get('units', '0')
                
                if inst == instrument:
                    print(f"\n   ✅ POSITION FOUND ON OANDA!")
                    print(f"   📊 Instrument: {inst}")
                    print(f"   📈 Long Units: {long_units}")
                    print(f"   📉 Short Units: {short_units}")
            
            print("\n" + "="*60)
            print("✅ SUCCESS! Trade executed and visible on OANDA!")
            print("="*60)
            print("\n📝 TO VERIFY ON OANDA WEBSITE:")
            print("   1. Go to: https://trade.oanda.com")
            print("   2. Log in to your DEMO account")
            print("   3. Click 'Positions' or 'Open Trades'")
            print("   4. You should see: EUR_USD LONG 100 units")
            print("\n" + "="*60)
            
            return True
        else:
            print("\n   ❌ Trade execution failed - no order returned")
            return False
            
    except Exception as e:
        print(f"\n   ❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = execute_test_trade()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("Check your OANDA demo account to see the trade!")
    else:
        print("\n⚠️ Test failed - check error messages above")
