"""
Direct trade execution - bypasses account check
"""

from tpqoa.tpqoa import tpqoa

def execute_trade_now():
    """Execute trade directly"""
    print("\n🚀 EXECUTING TRADE DIRECTLY...")
    
    try:
        # Connect
        trader = tpqoa("config/oanda_demo.cfg")
        print("✅ Connected to OANDA")
        
        # Get price
        instrument = "EUR_USD"
        _, bid, ask = trader.get_prices(instrument)
        print(f"📊 {instrument}: BID={bid:.5f}, ASK={ask:.5f}")
        
        # Execute trade
        print(f"\n📝 Executing BUY order for {instrument}...")
        print(f"   Units: 100")
        
        order = trader.create_order(
            instrument=instrument,
            units=100,
            suppress=True,
            ret=True
        )
        
        if order:
            print("\n✅ TRADE EXECUTED!")
            print(f"Order: {order}")
            
            # Check positions
            print("\n📊 Checking positions...")
            positions = trader.get_positions()
            print(f"Open positions: {len(positions)}")
            
            for pos in positions:
                print(f"\nPosition: {pos.get('instrument')}")
                print(f"  Long: {pos.get('long', {}).get('units', 0)}")
                print(f"  Short: {pos.get('short', {}).get('units', 0)}")
            
            print("\n✅ CHECK OANDA WEBSITE NOW!")
            print("   https://trade.oanda.com")
            print("   Look for EUR_USD position")
            
            return True
        else:
            print("❌ No order returned")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    execute_trade_now()
