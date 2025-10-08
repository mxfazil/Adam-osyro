"""
Quick Email Debug Script
Tests SendGrid configuration and sends a test email
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("EMAIL SERVICE DEBUG")
print("=" * 60)

# Check environment variables
print("\n1. Checking Environment Variables:")
print("-" * 60)

sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
from_email = os.getenv("SENDGRID_FROM_EMAIL")
from_name = os.getenv("SENDGRID_FROM_NAME")
reply_to = os.getenv("SENDGRID_REPLY_TO_EMAIL")

print(f"SENDGRID_API_KEY: {'✅ Found' if sendgrid_api_key else '❌ Missing'}")
if sendgrid_api_key:
    print(f"  - Starts with: {sendgrid_api_key[:10]}...")
    print(f"  - Length: {len(sendgrid_api_key)} characters")

print(f"SENDGRID_FROM_EMAIL: {'✅ ' + from_email if from_email else '❌ Missing'}")
print(f"SENDGRID_FROM_NAME: {'✅ ' + from_name if from_name else '❌ Missing'}")
print(f"SENDGRID_REPLY_TO_EMAIL: {'✅ ' + reply_to if reply_to else '⚠️ Not set (optional)'}")

if not sendgrid_api_key or not from_email:
    print("\n❌ ERROR: Missing required environment variables!")
    print("Please check your .env file")
    exit(1)

# Try to initialize email service
print("\n2. Initializing Email Service:")
print("-" * 60)

try:
    from email_service import create_email_service
    service = create_email_service()
    print("✅ Email service initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize email service: {e}")
    import traceback
    print(traceback.format_exc())
    exit(1)

# Test connection
print("\n3. Testing SendGrid Connection:")
print("-" * 60)

try:
    connection_result = service.test_connection()
    if connection_result["success"]:
        print(f"✅ Connection successful! Status: {connection_result['status_code']}")
    else:
        print(f"❌ Connection failed: {connection_result['message']}")
        exit(1)
except Exception as e:
    print(f"❌ Connection test error: {e}")
    import traceback
    print(traceback.format_exc())
    exit(1)

# Ask for test email
print("\n4. Send Test Email:")
print("-" * 60)
test_email = input("Enter your email address to send a test email: ").strip()

if not test_email or '@' not in test_email:
    print("❌ Invalid email address")
    exit(1)

print(f"\n📧 Sending test email to: {test_email}")
print("Please wait...")

try:
    result = service.send_welcome_email(
        to_email=test_email,
        name="Test User",
        company="Test Company"
    )
    
    print("\n" + "=" * 60)
    print("RESULT:")
    print("=" * 60)
    
    if result["success"]:
        print("✅ EMAIL SENT SUCCESSFULLY!")
        print(f"   Status Code: {result['status_code']}")
        print(f"   Message ID: {result.get('message_id', 'N/A')}")
        print(f"   Recipient: {result['to']}")
        print("\n📬 Check your email inbox (and spam folder)")
        print("📊 Also check SendGrid Dashboard → Activity Feed")
    else:
        print("❌ EMAIL FAILED TO SEND")
        print(f"   Error: {result['message']}")
        print("\n🔍 Full error details:")
        import traceback
        print(result.get('traceback', 'No traceback available'))
        
except Exception as e:
    print(f"❌ Error sending email: {e}")
    import traceback
    print("\n🔍 Full traceback:")
    print(traceback.format_exc())

print("\n" + "=" * 60)
print("Debug complete!")
print("=" * 60)
