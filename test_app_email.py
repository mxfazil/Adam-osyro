"""
Test if email service works in app context
"""

import os
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

print("=" * 60)
print("APP EMAIL SERVICE TEST")
print("=" * 60)

# Check env vars
print("\n1. Environment Variables:")
print(f"SENDGRID_API_KEY: {'✅ Found' if os.getenv('SENDGRID_API_KEY') else '❌ Missing'}")
print(f"SENDGRID_FROM_EMAIL: {os.getenv('SENDGRID_FROM_EMAIL')}")
print(f"SENDGRID_FROM_NAME: {os.getenv('SENDGRID_FROM_NAME')}")
print(f"SENDGRID_REPLY_TO_EMAIL: {os.getenv('SENDGRID_REPLY_TO_EMAIL')}")

# Try to initialize like the app does
print("\n2. Initializing Email Service (like app does):")
from email_service import create_email_service

sendgrid_api_key = os.getenv("SENDGRID_API_KEY")

if sendgrid_api_key and sendgrid_api_key != "your-sendgrid-api-key-here":
    try:
        email_service = create_email_service(sendgrid_api_key)
        print("✅ Email service initialized successfully")
        
        # Try to send test email
        test_email = input("\nEnter email to test: ").strip()
        if test_email:
            print(f"\n📧 Sending test email to {test_email}...")
            result = email_service.send_welcome_email(
                test_email,
                "Test User",
                "Test Company"
            )
            
            if result["success"]:
                print(f"✅ Email sent! Status: {result['status_code']}")
                print(f"   Message ID: {result.get('message_id')}")
            else:
                print(f"❌ Failed: {result['message']}")
                if 'traceback' in result:
                    print(result['traceback'])
        
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        import traceback
        print(traceback.format_exc())
else:
    print("❌ SendGrid API key not found or invalid")

print("\n" + "=" * 60)
