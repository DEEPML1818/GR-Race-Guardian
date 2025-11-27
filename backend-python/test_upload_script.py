import requests

url = 'http://127.0.0.1:8000/replay/telemetry/barber'
files = {'file': open('test_upload.csv', 'rb')}

try:
    response = requests.post(url, files=files)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
except Exception as e:
    print(f"Error: {e}")
