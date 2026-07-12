"""
Test Both Demo and Live OANDA Accounts
Comprehensive verification before trading
"""

import sys
import time
from tpqoa.tpqoa import tpqoa

def test_account(config_file, account_name):
    """Test a single account configuration"""
    print(f"\n{'='*70}")
    print(f"Testing {account_name} Account")
    print(f"{'='*70}")
    
    results = {'tests': 0, 'passed': 0, 'details': []}
    
    # Test 1: Connection
    print(f"\n1️⃣  Testing Connection...")
    results['tests'] += 1
    try:
        start = time.time()
        api = tpqoa(config_file)
        elapsed = time.time() - start
        print(f"   ✅ Connected ({elapsed:.2f}s)")
        results['passed'] += 1
        results['details'].append(('Connection', True, f'{elapsed:.2f}s'))
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['details'].append(('Connection', False, str(e)))
        return results
    
    # Test 2: Historical Data
    print(f"\n2️⃣  Testing Historical Data...")
    results['tests'] += 1
    try:
        start = time.time()
        df = api.get_history(
            instrument='EUR_USD',
            start='2024-01-01',
            end='2024-01-02',
            granularity='H1',
            price='M'
        )
        elapsed = time.time() - start
        
        if df is not None and len(df) > 0:
            print(f"   ✅ Retrieved {len(df)} candles ({elapsed:.2f}s)")
            results['passed'] += 1
            results['details'].append(('Historical Data', True, f'{len(df)} candles, {elapsed:.2f}s'))
        else:
            print(f"   ⚠️  No data returned")
            results['details'].append(('Historical Data', False, 'No data'))
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['details'].append(('Historical Data', False, str(e)[:50]))
    
    # Test 3: Current Prices
    print(f"\n3️⃣  Testing Real-time Prices...")
    results['tests'] += 1
    try:
        start = time.time()
        response = api.ctx.instrument.candles(
            instrument='EUR_USD',
            granularity='M1',
            count=1,
            price='MBA'
        )
        elapsed = time.time() - start
        
        if response.status == 200:
            candles = response.body.get('candles', [])
            if candles:
                candle = candles[0]
                bid = float(candle.bid.c)
                ask = float(candle.ask.c)
                spread = ask - bid
                print(f"   ✅ EUR_USD - Bid: {bid:.5f}, Ask: {ask:.5f}")
                print(f"      Spread: {spread:.5f} ({elapsed:.2f}s)")
                results['passed'] += 1
                results['details'].append(('Real-time Prices', True, f'{elapsed:.2f}s'))
            else:
                print(f"   ⚠️  No price data")
                results['details'].append(('Real-time Prices', False, 'No data'))
        else:
            print(f"   ❌ Status: {response.status}")
            results['details'].append(('Real-time Prices', False, f'Status {response.status}'))
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['details'].append(('Real-time Prices', False, str(e)[:50]))
    
    # Test 4: Account Summary (optional - may have permission issues)
    print(f"\n4️⃣  Testing Account Info...")
    results['tests'] += 1
    try:
        summary = api.get_account_summary()
        balance = summary.get('balance', 'N/A')
        currency = summary.get('currency', 'N/A')
        print(f"   ✅ Balance: {balance} {currency}")
        results['passed'] += 1
        results['details'].append(('Account Info', True, f'{balance} {currency}'))
    except Exception as e:
        print(f"   ⚠️  Limited permissions (not critical): {str(e)[:60]}")
        results['details'].append(('Account Info', False, 'Permission issue'))
    
    return results

def main():
    """Test both accounts"""
    print("\n" + "="*70)
    print("FXBot - Dual Account Verification")
    print("Testing both Demo and Live OANDA accounts")
    print("="*70)
    
    # Test Demo Account
    demo_results = test_account('config/oanda_demo.cfg', 'DEMO')
    
    # Test Live Account
    live_results = test_account('config/oanda_live.cfg', 'LIVE')
    
    # Summary
    print(f"\n{'='*70}")
    print("FINAL SUMMARY")
    print(f"{'='*70}")
    
    demo_score = (demo_results['passed'] / demo_results['tests'] * 100) if demo_results['tests'] > 0 else 0
    live_score = (live_results['passed'] / live_results['tests'] * 100) if live_results['tests'] > 0 else 0
    
    print(f"\n📊 DEMO Account: {demo_results['passed']}/{demo_results['tests']} tests passed ({demo_score:.0f}%)")
    for test_name, passed, detail in demo_results['details']:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}: {detail}")
    
    print(f"\n📊 LIVE Account: {live_results['passed']}/{live_results['tests']} tests passed ({live_score:.0f}%)")
    for test_name, passed, detail in live_results['details']:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}: {detail}")
    
    # Critical tests check
    demo_critical = sum(1 for name, passed, _ in demo_results['details'] 
                       if passed and name in ['Connection', 'Historical Data', 'Real-time Prices'])
    live_critical = sum(1 for name, passed, _ in live_results['details'] 
                       if passed and name in ['Connection', 'Historical Data', 'Real-time Prices'])
    
    print(f"\n{'='*70}")
    print("READINESS STATUS")
    print(f"{'='*70}")
    
    if demo_critical >= 3:
        print(f"\n✅ DEMO Account: READY FOR TRADING")
        print(f"   All critical functions working")
    else:
        print(f"\n⚠️  DEMO Account: NOT READY")
        print(f"   Only {demo_critical}/3 critical tests passed")
    
    if live_critical >= 3:
        print(f"\n✅ LIVE Account: READY FOR TRADING")
        print(f"   All critical functions working")
        print(f"   ⚠️  WARNING: This uses REAL MONEY!")
    else:
        print(f"\n⚠️  LIVE Account: NOT READY")
        print(f"   Only {live_critical}/3 critical tests passed")
    
    print(f"\n{'='*70}")
    
    if demo_critical >= 3 and live_critical >= 3:
        print("\n🎉 SUCCESS! Both accounts are fully operational!")
        print("\nYou can now:")
        print("  • Use DEMO account for safe testing")
        print("  • Switch to LIVE account when ready (REAL MONEY!)")
        print("\nLaunch the interface:")
        print("  python UltimateTradingInterface.py")
        return 0
    elif demo_critical >= 3:
        print("\n✅ DEMO account ready! Start with demo trading.")
        print("\n⚠️  LIVE account needs attention.")
        print("\nLaunch with demo:")
        print("  python UltimateTradingInterface.py")
        return 0
    else:
        print("\n❌ Critical issues found. Please check API credentials.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
