from tpqoa.tpqoa import tpqoa

try:
    oanda = tpqoa("config/oanda_live.cfg")
    instruments = oanda.get_instruments()
    print("Connection successful!")
    print(f"Available instruments: {len(instruments)}")
    print("First 5 instruments:", [inst[1] for inst in instruments[:5]])
    
    # Get account summary
    summary = oanda.get_account_summary()
    print(f"\nAccount Balance: ${summary.get('balance', 'N/A')}")
    
except Exception as e:
    print("Error:", str(e))
