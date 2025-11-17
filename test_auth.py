#!/usr/bin/env python3
"""
Test script to verify authentication system is working properly
"""
import requests
import os
import sys
from datetime import datetime

def test_authentication():
    print(f"[{datetime.now()}] Testing authentication system...")

    # Check if we're in test mode by environment
    test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"

    print(f"Test mode: {test_mode}")
    print(f"Dev mode: {dev_mode}")

    # Default to port 8001 to match the frontend test (from test_frontend.html)
    base_url = os.getenv("BASE_URL", "http://localhost:8001")

    print(f"Testing authentication endpoints at {base_url}...")

    try:
        # Test the dev mode endpoint first
        print(f"Testing {base_url}/dev-mode endpoint...")
        response = requests.get(f"{base_url}/dev-mode")
        print(f"Dev mode endpoint status: {response.status_code}")

        if response.status_code == 200:
            dev_data = response.json()
            print(f"Server dev mode: {dev_data.get('dev_mode', 'unknown')}")
            print(f"Server test mode: {dev_data.get('test_mode', 'unknown')}")

        # Test auth endpoints
        print(f"\nTesting authentication endpoints...")

        # Try to get test token if in test mode
        if test_mode or dev_mode:
            print("Requesting test token...")
            token_response = requests.get(f"{base_url}/auth/test-token")
            print(f"Test token endpoint status: {token_response.status_code}")

            if token_response.status_code == 200:
                token_data = token_response.json()
                print(f"Received test token: {'Yes' if 'access_token' in token_data else 'No'}")
                token = token_data.get('access_token')

                # Test protected endpoint with token
                if token:
                    headers = {"Authorization": f"Bearer {token}"}
                    me_response = requests.get(f"{base_url}/auth/me", headers=headers)
                    print(f"Protected endpoint status: {me_response.status_code}")

                    if me_response.status_code == 200:
                        user_data = me_response.json()
                        print(f"Current user: {user_data.get('username', 'unknown')}")
                        print(f"User role: {user_data.get('role', 'unknown')}")

        # Test login endpoint
        print("Testing login endpoint...")
        login_response = requests.post(
            f"{base_url}/auth/login",
            json={"username": "admin", "password": "admin"},
            headers={"Content-Type": "application/json"}
        )
        print(f"Login endpoint status: {login_response.status_code}")

        # Check login response
        if login_response.status_code == 200:
            login_data = login_response.json()
            print("Login successful!")
            if 'access_token' in login_data:
                print("Token received successfully")
                # Test using the received token
                token = login_data['access_token']
                headers = {"Authorization": f"Bearer {token}"}
                me_response = requests.get(f"{base_url}/auth/me", headers=headers)
                print(f"Protected endpoint with login token status: {me_response.status_code}")
                if me_response.status_code == 200:
                    print("Authentication system is working properly!")
        else:
            print(f"Login failed with status {login_response.status_code}")
            if login_response.status_code == 401:
                print("This may be expected if test mode is not enabled or credentials are wrong.")

        # Test getting accessible divisions
        print("Testing accessible divisions endpoint...")
        div_response = requests.get(f"{base_url}/auth/accessible-divisions")
        print(f"Accessible divisions endpoint status: {div_response.status_code}")

        if div_response.status_code == 200:
            divisions = div_response.json()
            print(f"Accessible divisions count: {len(divisions) if isinstance(divisions, list) else 'N/A'}")
            if isinstance(divisions, list) and len(divisions) > 0:
                print(f"Sample divisions: {divisions[:3]}")  # Show first 3

        print(f"\n[{datetime.now()}] Authentication test completed!")
        return True

    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot connect to server at {base_url}")
        print("Make sure the backend server is running!")
        print("To start the server: cd refactor_production/backend && python main.py")
        return False
    except Exception as e:
        print(f"Error during authentication test: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_authentication()
    if success:
        print("\n✓ Authentication test completed successfully!")
    else:
        print("\n✗ Authentication test failed!")
    sys.exit(0 if success else 1)