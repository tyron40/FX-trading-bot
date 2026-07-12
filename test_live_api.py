"""
Test LIVE account API - CAREFUL: This uses REAL money!
"""

from tpqoa.tpqoa import tpqoa

def test_live_account():
    """Test live account connection and permissions"""
    print("\n" + "="*60)
    print("⚠️  TESTING LIVE ACCOUNT API")
    print("⚠️  THIS USES REAL MONEY - BE CAREFUL!")
    print("="*60)
    
    try:
        # Connect to LIVE account
        print("\n1️⃣ Connecting to LIVE account...")
        trader = tpqoa("config/oanda_live.cfg")
        print("   ✅ Connected!")
        
        # Test account access
        print("\n2️⃣ Testing account access...")
        try:
            summary = trader.get_account_summary(detailed=True)
            balance = float(summary.get('balance', 0))
            print(f"   ✅ Account access: OK")
            print(f"   💰 Balance: ${balance:,.2f}")
        except Exception as e:
            print(f"   ⚠️  Account summary failed: {e}")
            print("   Trying alternative method...")
        
        # Test price access
        print("\n3️⃣ Testing price data access...")
        try:
            instrument = "EUR_USD"
            _, bid, ask = trader.get_prices(instrument)
            print(f"   ✅ Price access: OK")
            print(f"   📊 {instrument}: BID={bid:.5f}, ASK={ask:.5f}")
        except Exception as e:
            print(f"   ❌ Price access failed: {e}")
        
        # Test positions access
        print("\n4️⃣ Testing positions access...")
        try:
            positions = trader.get_positions()
            print(f"   ✅ Positions access: OK")
            print(f"   📊 Open positions: {len(positions)}")
            
            if positions:
                for pos in positions:
                    inst = pos.get('instrument', 'N/A')
                    long_units = pos.get('long', {}).get('units', '0')
                    short_units = pos.get('short', {}).get('units', '0')
                    print(f"      - {inst}: Long={long_units}, Short={short_units}")
        except Exception as e:
            print(f"   ❌ Positions access failed: {e}")
        
        # Test historical data
        print("\n5️⃣ Testing historical data access...")
        try:
            response = trader.ctx.instrument.candles(
                "EUR_USD", granularity="M5", count=10, price="MBA"
            )
            if response.status == 200:
                candles = response.body.get('candles', [])
                print(f"   ✅ Historical data: OK")
                print(f"   📊 Retrieved {len(candles)} candles")
            else:
                print(f"   ❌ Historical data failed: Status {response.status}")
        except Exception as e:
            print(f"   ❌ Historical data failed: {e}")
        
        print("\n" + "="*60)
        print("✅ LIVE API TEST COMPLETE")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n⚠️  WARNING: This will test your LIVE account API")
    print("⚠️  No trades will be executed in this test")
    print("⚠️  Only checking permissions and data access")
    
    input("\nPress ENTER to continue or Ctrl+C to cancel...")
    
    test_live_account()
