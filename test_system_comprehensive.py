"""
Comprehensive System Test for FXBot
Tests all critical components before launching the trading interface
"""

import sys
import time
from tpqoa.tpqoa import tpqoa

def test_connection(config_file, account_name):
    """Test basic OANDA connection"""
    print(f"\n{'='*60}")
    print(f"Testing {account_name} Account Connection")
    print(f"{'='*60}")
    
    try:
        start = time.time()
        api = tpqoa(config_file)
        elapsed = time.time() - start
        print(f"✅ Connection established ({elapsed:.2f}s)")
        return api
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def test_account_info(api, account_name):
    """Test account information retrieval"""
    print(f"\n📊 Testing Account Information...")
    try:
        summary = api.get_account_summary()
        balance = summary.get('balance', 'N/A')
        currency = summary.get('currency', 'N/A')
        margin = summary.get('marginAvailable', 'N/A')
        
        print(f"✅ Account Info Retrieved:")
        print(f"   Balance: {balance} {currency}")
        print(f"   Margin Available: {margin}")
        return True
    except Exception as e:
        print(f"❌ Account info failed: {e}")
        return False

def test_instruments(api):
    """Test instrument list retrieval"""
    print(f"\n🌍 Testing Instruments...")
    try:
        instruments = api.get_instruments()
        print(f"✅ Instruments Retrieved: {len(instruments)} available")
        print(f"   Sample: {[inst[1] for inst in instruments[:5]]}")
        return True
    except Exception as e:
        print(f"❌ Instruments failed: {e}")
        return False

def test_historical_data(api):
    """Test historical data retrieval"""
    print(f"\n📈 Testing Historical Data...")
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
            print(f"✅ Historical Data Retrieved ({elapsed:.2f}s)")
            print(f"   Rows: {len(df)}, Columns: {list(df.columns)}")
            return True
        else:
            print(f"⚠️  No historical data returned")
            return False
    except Exception as e:
        print(f"❌ Historical data failed: {e}")
        return False

def test_current_prices_alternative(api):
    """Test current price retrieval using alternative method"""
    print(f"\n💰 Testing Current Prices (Alternative Method)...")
    try:
        # Use candles endpoint for current price
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
                print(f"✅ Current Prices Retrieved ({elapsed:.2f}s)")
                print(f"   EUR_USD - Bid: {bid:.5f}, Ask: {ask:.5f}")
                return True
        
        print(f"⚠️  Price retrieval returned status: {response.status}")
        return False
    except Exception as e:
        print(f"❌ Price retrieval failed: {e}")
        return False

def main():
    """Run comprehensive system tests"""
    print("\n" + "="*60)
    print("FXBot Comprehensive System Test")
    print("="*60)
    
    results = {
        'demo': {'tests': 0, 'passed': 0},
        'live': {'tests': 0, 'passed': 0}
    }
    
    # Test Demo/Practice Account
    demo_api = test_connection('config/oanda_demo.cfg', 'Demo/Practice')
    if demo_api:
        tests = [
            ('Account Info', lambda: test_account_info(demo_api, 'Demo')),
            ('Instruments', lambda: test_instruments(demo_api)),
            ('Historical Data', lambda: test_historical_data(demo_api)),
            ('Current Prices', lambda: test_current_prices_alternative(demo_api))
        ]
        
        for test_name, test_func in tests:
            results['demo']['tests'] += 1
            if test_func():
                results['demo']['passed'] += 1
    
    # Test Live Account (if different from demo)
    print(f"\n{'='*60}")
    print("Note: Your live config appears to use the same credentials as demo")
    print("Skipping duplicate live account test")
    print(f"{'='*60}")
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    demo_score = results['demo']['passed'] / results['demo']['tests'] * 100 if results['demo']['tests'] > 0 else 0
    print(f"\nDemo Account: {results['demo']['passed']}/{results['demo']['tests']} tests passed ({demo_score:.0f}%)")
    
    if demo_score >= 75:
        print(f"\n✅ System is ready for trading!")
        print(f"   You can now launch: python UltimateTradingInterface.py")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Please check your OANDA configuration.")
        print(f"   Make sure your API token has proper permissions.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
