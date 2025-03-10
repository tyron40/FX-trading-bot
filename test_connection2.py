import requests

headers = {
    'Authorization': f'Bearer bee66320545953c2207819939ac67f0-8d65c577151e1820ea316f73d400026a',
    'Content-Type': 'application/json'
}

try:
    # Try a direct HTTP request to the API
    response = requests.get(
        'https://api-fxpractice.oanda.com/v3/accounts/101-001-17388471-001/instruments',
        headers=headers
    )
    
    print("Status Code:", response.status_code)
    print("Response:", response.text)
    
except Exception as e:
    print("Error:", str(e))
