"""
Quick test script to verify SendGrid configuration
Run this to check if your SendGrid setup is working
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_sendgrid_config():
    """Test SendGrid configuration"""
    print("=" * 60)
    print("SendGrid Configuration Test")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("SENDGRID_API_KEY")
    if api_key:
        print("✅ SENDGRID_API_KEY found")
        print(f"   Key starts with: {api_key[:10]}...")
        if api_key.startswith("SG."):
            print("   ✅ Key format looks correct")
        else:
            print("   ⚠️  Warning: Key should start with 'SG.'")
    else:
        print("❌ SENDGRID_API_KEY not found in .env")
        print("   Add: SENDGRID_API_KEY=SG.your_api_key_here")
    
    # Check from email
    from_email = os.getenv("SENDGRID_FROM_EMAIL")
    if from_email:
        print(f"✅ SENDGRID_FROM_EMAIL found: {from_email}")
        if "@" in from_email:
            print("   ✅ Email format looks valid")
        else:
            print("   ⚠️  Warning: Email format may be invalid")
    else:
        print("❌ SENDGRID_FROM_EMAIL not found in .env")
        print("   Add: SENDGRID_FROM_EMAIL=noreply@yourdomain.com")
    
    # Check from name
    from_name = os.getenv("SENDGRID_FROM_NAME")
    if from_name:
        print(f"✅ SENDGRID_FROM_NAME found: {from_name}")
    else:
        print("⚠️  SENDGRID_FROM_NAME not found (optional)")
        print("   Add: SENDGRID_FROM_NAME=Your Company Name")
    
    print("\n" + "=" * 60)
    
    # Test connection if all configs are present
    if api_key and from_email:
        print("Testing SendGrid API connection...")
        print("=" * 60)
        
        try:
            from email_service import create_email_service
            
            service = create_email_service()
            result = service.test_connection()
            
            if result["success"]:
                print("✅ SendGrid connection successful!")
                print(f"   Status: {result['message']}")
            else:
                print("❌ SendGrid connection failed")
                print(f"   Error: {result['message']}")
        except Exception as e:
            print(f"❌ Error testing connection: {e}")
            print("\nPossible issues:")
            print("1. Invalid API key")
            print("2. API key doesn't have 'Mail Send' permission")
            print("3. Network connectivity issue")
    else:
        print("\n⚠️  Cannot test connection - missing configuration")
        print("Please add the required environment variables to .env")
    
    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    if not api_key or not from_email:
        print("1. Add SendGrid credentials to .env file")
        print("2. Verify sender email in SendGrid dashboard")
        print("3. Run this test again: python test_sendgrid.py")
    else:
        print("1. ✅ Configuration looks good!")
        print("2. Test sending an email:")
        print("   python -c \"from email_service import create_email_service; s=create_email_service(); print(s.send_welcome_email('your-email@example.com', 'Test User'))\"")
        print("3. Start your application: python streamlined_app.py")
    print("=" * 60)

if __name__ == "__main__":
    test_sendgrid_config()
