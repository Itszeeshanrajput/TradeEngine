#!/usr/bin/env python3
"""
Quick test to verify the application is working
"""

import requests
import sys
import time

def test_endpoints():
    """Test basic endpoints"""
    base_url = "http://localhost:5000"
    
    endpoints = [
        "/",
        "/analytics", 
        "/backtest",
        "/settings",
        "/api/accounts"
    ]
    
    print("Testing Forex Trading Bot endpoints...")
    print("=" * 50)
    
    all_working = True
    
    for endpoint in endpoints:
        try:
            url = base_url + endpoint
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                status = "✓ OK"
            elif response.status_code == 405:
                status = "✓ OK (Method not allowed - expected for API endpoints)"
            else:
                status = f"✗ Error {response.status_code}"
                all_working = False
                
            print(f"{endpoint:<15} {status}")
            
        except requests.exceptions.ConnectionError:
            print(f"{endpoint:<15} ✗ Connection refused - Server not running")
            all_working = False
        except requests.exceptions.Timeout:
            print(f"{endpoint:<15} ✗ Timeout")
            all_working = False
        except Exception as e:
            print(f"{endpoint:<15} ✗ Error: {e}")
            all_working = False
    
    print("=" * 50)
    if all_working:
        print("✓ All endpoints responding correctly!")
        print("Dashboard is accessible at: http://localhost:5000")
    else:
        print("✗ Some endpoints have issues")
        print("Check if the server is running with: python start_with_eventlet.py")
    
    return all_working

if __name__ == "__main__":
    test_endpoints()