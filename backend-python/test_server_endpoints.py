"""
Test to see what endpoints are actually available on the running server
"""
import requests

def test_available_endpoints():
    """Check what endpoints exist"""
    print("=" * 60)
    print("CHECKING AVAILABLE ENDPOINTS")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000"
    
    # Test various endpoints
    endpoints_to_test = [
        ("/replay/build", "POST"),
        ("/replay/tracks", "GET"),
        ("/tracks/available", "GET"),
        ("/docs", "GET"),  # FastAPI auto-generated docs
    ]
    
    for endpoint, method in endpoints_to_test:
        url = f"{base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=2)
            else:
                response = requests.post(url, json={}, timeout=2)
            
            status = response.status_code
            if status == 404:
                print(f"[NOT FOUND] {method} {endpoint}")
            elif status in [200, 422]:  # 422 = validation error (endpoint exists but bad data)
                print(f"[EXISTS]    {method} {endpoint} (status: {status})")
            else:
                print(f"[UNKNOWN]   {method} {endpoint} (status: {status})")
                
        except Exception as e:
            print(f"[ERROR]     {method} {endpoint} - {e}")
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS")
    print("=" * 60)
    print("\nIf /replay/build shows [NOT FOUND], the server is running")
    print("an OLD version of the code from before we added the endpoint.")
    print("\nSOLUTION: Kill the server and restart it:")
    print("  1. Find the terminal running 'python app.py'")
    print("  2. Press CTRL+C to stop it")
    print("  3. Run 'python app.py' again")
    print("  4. The endpoint should then be available")

if __name__ == "__main__":
    test_available_endpoints()
