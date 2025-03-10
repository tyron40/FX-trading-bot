import v20

try:
    ctx = v20.Context(
        hostname='api-fxpractice.oanda.com',
        port=443,
        token='bee66320545953c2207819939ac67f0-8d65c577151e1820ea316f73d400026a'
    )
    
    # Try to get account summary
    response = ctx.account.summary("101-001-17388471-001")
    print("Connection successful!")
    print("Response:", response.raw_body)
    
except Exception as e:
    print("Error:", str(e))
