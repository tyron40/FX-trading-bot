from tpqoa import tpqoa
import v20

try:
    oanda = tpqoa("oanda.cfg")
    print("Successfully connected to OANDA")
    
    # Try to get instruments and print full response
    ctx = v20.Context(
        hostname='api-fxpractice.oanda.com',
        port=443,
        token=oanda.access_token,
        poll_timeout=10
    )
    resp = ctx.account.instruments(oanda.account_id)
    print("\nFull response:", resp.raw_body)
    
except Exception as e:
    print("\nError:", str(e))
    if hasattr(e, 'raw_body'):
        print("\nFull error response:", e.raw_body)
