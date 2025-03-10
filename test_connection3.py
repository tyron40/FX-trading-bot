import requests

headers = {
    'Authorization': f'Bearer bee66320545953c2207819939ac67f0-8d65c577151e1820ea316f73d400026a',
    'Accept-Datetime-Format': 'RFC3339'
}

try:
    # Try getting account details first
    account_response = requests.get(
        'https://api-fxpractice.oanda.com/v3/accounts/101-001-17388471-001',
        headers=headers
    )
    print("\nAccount Response:")
    print("Status Code:", account_response.status_code)
    print("Response:", account_response.text)
    
    # Try getting available instruments
    instruments_response = requests.get(
        'https://api-fxpractice.oanda.com/v3/accounts',
        headers=headers
    )
    print("\nInstruments Response:")
    print("Status Code:", instruments_response.status_code)
    print("Response:", instruments_response.text)
    
except Exception as e:
    print("Error:", str(e))
