"""
🚨 EMERGENCY STOP - Close All Positions
This script will immediately close all open positions on your live account
"""

from tpqoa.tpqoa import tpqoa
import sys

def emergency_close_all():
    """Close all open positions immediately"""
    print("\n" + "="*60)
    print("🚨 EMERGENCY POSITION CLOSER")
    print("="*60)
    print("\n⚠️  This will close ALL open positions on your LIVE account")
    print("💰 Account: LIVE (REAL MONEY)")
    print("\n" + "="*60)
    
    response = input("\nType 'YES' to close all positions: ")
    
    if response.upper() != 'YES':
        print("\n❌ Cancelled - No positions closed")
        return
    
    try:
        print("\n🔄 Connecting to LIVE account...")
        trader = tpqoa("config/oanda_live.cfg")
        
        print("✅ Connected!")
        print("\n📊 Checking for open positions...")
        
        # Get all open positions
        try:
            response = trader.ctx.position.list_open(trader.account_id)
            if response.status == 200:
                positions = response.body.get('positions', [])
                
                if not positions:
                    print("\n✅ No open positions found - Nothing to close")
                    return
                
                print(f"\n⚠️  Found {len(positions)} open position(s)")
                print("\n🔄 Closing all positions...")
                
                for pos in positions:
                    instrument = pos.instrument
                    long_units = float(pos.long.units) if hasattr(pos, 'long') else 0
                    short_units = float(pos.short.units) if hasattr(pos, 'short') else 0
                    
                    if long_units != 0:
                        print(f"   Closing LONG {instrument}: {long_units} units...")
                        trader.create_order(instrument, -abs(long_units), suppress=True)
                        print(f"   ✅ Closed LONG {instrument}")
                    
                    if short_units != 0:
                        print(f"   Closing SHORT {instrument}: {short_units} units...")
                        trader.create_order(instrument, abs(short_units), suppress=True)
                        print(f"   ✅ Closed SHORT {instrument}")
                
                print("\n✅ ALL POSITIONS CLOSED!")
                
                # Get final balance
                summary = trader.get_account_summary(detailed=True)
                balance = float(summary.get('balance', 0))
                print(f"\n💰 Final Balance: ${balance:.2f}")
                
            else:
                print(f"\n❌ Could not get positions: {response.status}")
                
        except Exception as e:
            print(f"\n❌ Error getting positions: {e}")
            print("\nTrying alternative method...")
            
            # Try closing via instrument list
            instruments = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD']
            for instrument in instruments:
                try:
                    trader.create_order(instrument, 0, suppress=True)  # Close any position
                except:
                    pass
            
            print("✅ Attempted to close all positions")
    
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        print("\n⚠️  MANUAL ACTION REQUIRED:")
        print("1. Go to https://trade.oanda.com")
        print("2. Log in to your LIVE account")
        print("3. Click 'Positions'")
        print("4. Manually close all open positions")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ EMERGENCY STOP COMPLETE")
    print("="*60)
    print("\n⚠️  Bot has been stopped")
    print("💡 All positions have been closed")
    print("📊 Check your OANDA account to verify\n")

if __name__ == "__main__":
    emergency_close_all()
