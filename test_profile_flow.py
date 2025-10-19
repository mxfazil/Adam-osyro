#!/usr/bin/env python3
"""
Test script to verify the profile summary flow
"""

import requests
import json
import time
import os
from tavily_direct import TavilyDirect

def test_profile_flow():
    """Test the complete profile flow"""
    
    # Initialize Tavily client directly
    tavily_client = TavilyDirect()
    
    # Test 1: Check if quick_user_summary works
    print("🔍 Testing quick_user_summary...")
    try:
        profile_data = tavily_client.quick_user_summary("Elon Musk", "Tesla")
        print("✅ quick_user_summary returned data:")
        print(json.dumps(profile_data, indent=2))
        print()
        
        # Check structure for chat template
        required_fields = ['summary', 'professional_info', 'social_links', 'recent_activity']
        missing_fields = []
        
        for field in required_fields:
            if field not in profile_data:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
        else:
            print("✅ All required fields present for chat template")
            
    except Exception as e:
        print(f"❌ quick_user_summary failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("-" * 60)
    
    # Test 2: Check the debug endpoint
    print("🔍 Testing debug endpoint...")
    try:
        response = requests.get("http://127.0.0.1:8000/debug/tavily-search", 
                               params={"q": "Elon Musk Tesla", "max_results": 1},
                               timeout=10)
        
        if response.status_code == 200:
            debug_data = response.json()
            print("✅ Debug endpoint works:")
            print(json.dumps(debug_data, indent=2))
        else:
            print(f"❌ Debug endpoint failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Debug endpoint test failed: {e}")
    
    print("-" * 60)
    
    # Test 3: Try to access a chat session to see template rendering
    print("🔍 Testing form submission flow...")
    try:
        # Submit form data
        form_data = {
            "name": "Elon Musk",
            "company": "Tesla", 
            "email": "test@example.com",
            "phone": "555-0123",
            "source": "manual"
        }
        
        response = requests.post("http://127.0.0.1:8000/process-info", 
                               data=form_data,
                               allow_redirects=False,
                               timeout=15)
        
        if response.status_code == 303:
            redirect_url = response.headers.get('Location')
            print(f"✅ Form submitted, redirecting to: {redirect_url}")
            
            # Follow redirect to see chat interface
            if redirect_url:
                chat_response = requests.get(f"http://127.0.0.1:8000{redirect_url}", timeout=10)
                if chat_response.status_code == 200:
                    print("✅ Chat interface loaded")
                    # Check if profile summary elements are in the HTML
                    html_content = chat_response.text
                    if "Profile Summary" in html_content:
                        print("✅ Profile Summary section found in template")
                    else:
                        print("❌ Profile Summary section not found in template")
                        
                    if "Quick Profile Summary" in html_content:
                        print("✅ Web info section found in template")
                    else:
                        print("❌ Web info section not found in template")
                else:
                    print(f"❌ Chat interface failed to load: {chat_response.status_code}")
        else:
            print(f"❌ Form submission failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Form submission test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting profile flow test...")
    test_profile_flow()
    print("✅ Test completed!")