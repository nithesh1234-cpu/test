#!/usr/bin/env python3
"""
Simple API Test Script
Run this to test basic API functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api():
    print("🧪 Testing Chat API...")
    print("=" * 50)
    
    # Test 1: Health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running!")
        return False
    
    # Test 2: User registration
    print("\n2. Testing user registration...")
    test_user = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/register",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ User registration passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ User registration failed: {response.status_code}")
            print(f"   Error: {response.json()}")
    except Exception as e:
        print(f"❌ Registration test error: {e}")
    
    # Test 3: User login
    print("\n3. Testing user login...")
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ User login passed")
            login_response = response.json()
            print(f"   Token received: {login_response['access_token'][:20]}...")
            
            # Store token for next tests
            token = login_response['access_token']
            
            # Test 4: Get current user
            print("\n4. Testing get current user...")
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{BASE_URL}/users/me", headers=headers)
            
            if response.status_code == 200:
                print("✅ Get current user passed")
                print(f"   User: {response.json()}")
            else:
                print(f"❌ Get current user failed: {response.status_code}")
            
            # Test 5: Create chat room
            print("\n5. Testing chat room creation...")
            room_data = {
                "name": "Test Room",
                "description": "A test chat room",
                "is_private": False
            }
            
            response = requests.post(
                f"{BASE_URL}/chat-rooms",
                json=room_data,
                headers=headers
            )
            
            if response.status_code == 200:
                print("✅ Chat room creation passed")
                room_response = response.json()
                print(f"   Room created: {room_response}")
                
                # Test 6: Get room messages
                print("\n6. Testing get room messages...")
                room_id = room_response.get('room_id', 1)
                response = requests.get(
                    f"{BASE_URL}/chat-rooms/{room_id}/messages",
                    headers=headers
                )
                
                if response.status_code == 200:
                    print("✅ Get room messages passed")
                    messages = response.json()
                    print(f"   Messages count: {len(messages)}")
                else:
                    print(f"❌ Get room messages failed: {response.status_code}")
            else:
                print(f"❌ Chat room creation failed: {response.status_code}")
                print(f"   Error: {response.json()}")
                
        else:
            print(f"❌ User login failed: {response.status_code}")
            print(f"   Error: {response.json()}")
    except Exception as e:
        print(f"❌ Login test error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 API testing completed!")
    print("\n📚 Next steps:")
    print("1. Open frontend/index.html in your browser")
    print("2. Register a new user or login with test@example.com / testpass123")
    print("3. Create a chat room and start chatting!")
    print("4. Open multiple browser tabs to test real-time messaging")
    
    return True

if __name__ == "__main__":
    test_api()