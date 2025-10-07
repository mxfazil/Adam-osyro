# SendGrid Email Integration Guide

## Overview
This guide explains how to use the SendGrid email integration in your Business Card OCR application.

## Setup Steps

### 1. Install SendGrid Package
```bash
pip install sendgrid
```

### 2. Configure Environment Variables
Add these to your `.env` file:

```env
# SendGrid Configuration
SENDGRID_API_KEY=SG.your_actual_api_key_here
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
SENDGRID_FROM_NAME=Business Card OCR Team
```

**Important Notes:**
- Replace `SG.your_actual_api_key_here` with your actual SendGrid API key
- The `SENDGRID_FROM_EMAIL` must be a verified sender in your SendGrid account
- To verify a sender:
  1. Log in to SendGrid Dashboard
  2. Go to Settings → Sender Authentication
  3. Verify your domain or single sender email

### 3. Test SendGrid Connection
Run this command to test your SendGrid setup:

```bash
python email_service.py
```

This will test the connection and show if your API key is valid.

## Features

### 1. Automatic Welcome Emails
When a business card is saved via the `/save` endpoint, a welcome email is automatically sent if:
- Email service is initialized
- The contact has an email address

**Example Response:**
```json
{
  "success": true,
  "message": "Business card saved successfully and welcome email sent",
  "data": {
    "id": 123,
    "email_sent": true
  }
}
```

### 2. Bulk Email Sending
Send welcome emails to all contacts in your database.

**Endpoint:** `POST /api/send-bulk-emails`  
**Authentication:** Required (Bearer token)

**Example:**
```bash
curl -X POST http://localhost:8000/api/send-bulk-emails \
  -H "Authorization: Bearer your-api-key-here"
```

**Response:**
```json
{
  "success": true,
  "message": "Sent 45/50 emails",
  "results": {
    "total": 50,
    "sent": 45,
    "failed": 5,
    "details": [
      {
        "name": "John Doe",
        "email": "john@example.com",
        "status": "sent",
        "message_id": "abc123",
        "status_code": 202
      }
    ]
  }
}
```

### 3. Custom Email Templates
The email service includes several email types:

#### Welcome Email
Sent automatically when a card is saved.

#### Follow-up Email
Send follow-up emails after initial contact:

```python
from email_service import create_email_service

service = create_email_service()
result = service.send_follow_up_email(
    to_email="contact@example.com",
    name="John Doe",
    company="Acme Corp",
    days_since_scan=7
)
```

#### Custom Email
Send completely custom emails:

```python
result = service.send_custom_email(
    to_email="contact@example.com",
    subject="Your Custom Subject",
    html_content="<h1>Your HTML content</h1>",
    plain_text="Your plain text version"
)
```

## Email Service API

### Methods

#### `send_welcome_email(to_email, name, company=None)`
Send welcome email to a new contact.

**Parameters:**
- `to_email` (str): Recipient email address
- `name` (str): Recipient name
- `company` (str, optional): Company name

**Returns:**
```python
{
    "success": True,
    "message": "Email sent successfully",
    "status_code": 202,
    "to": "john@example.com",
    "message_id": "abc123"
}
```

#### `send_batch_emails(contacts)`
Send emails to multiple contacts.

**Parameters:**
- `contacts` (list): List of dicts with `email`, `name`, and optional `company` keys

**Returns:**
```python
{
    "total": 10,
    "sent": 9,
    "failed": 1,
    "details": [...]
}
```

#### `send_follow_up_email(to_email, name, company=None, days_since_scan=7)`
Send follow-up email after initial contact.

#### `send_custom_email(to_email, subject, html_content, plain_text=None, name=None)`
Send custom email with your own content.

#### `test_connection()`
Test SendGrid API connection.

**Returns:**
```python
{
    "success": True,
    "message": "SendGrid connection successful",
    "status_code": 200
}
```

## Usage Examples

### Python Script
```python
from email_service import create_email_service

# Initialize service
service = create_email_service()

# Test connection
connection_test = service.test_connection()
print(connection_test)

# Send single email
result = service.send_welcome_email(
    to_email="john@example.com",
    name="John Doe",
    company="Acme Corp"
)
print(result)

# Send batch emails
contacts = [
    {"email": "john@example.com", "name": "John Doe", "company": "Acme"},
    {"email": "jane@example.com", "name": "Jane Smith", "company": "TechCo"}
]
results = service.send_batch_emails(contacts)
print(f"Sent {results['sent']}/{results['total']} emails")
```

### API Call (cURL)
```bash
# Send bulk emails
curl -X POST http://localhost:8000/api/send-bulk-emails \
  -H "Authorization: Bearer your-api-key-here"
```

### API Call (Python requests)
```python
import requests

url = "http://localhost:8000/api/send-bulk-emails"
headers = {"Authorization": "Bearer your-api-key-here"}

response = requests.post(url, headers=headers)
print(response.json())
```

## Monitoring and Logs

### Application Logs
The email service logs all activities:

```
✅ SendGrid email service initialized successfully
📧 Welcome email sent to john@example.com
⚠️ Failed to send email: Invalid email address
❌ Email sending error: API key invalid
```

### SendGrid Dashboard
Monitor your emails in the SendGrid dashboard:
1. Log in to SendGrid
2. Go to Activity → Activity Feed
3. View sent emails, delivery status, opens, clicks, etc.

## Troubleshooting

### Email Not Sending
**Problem:** Emails are not being sent

**Solutions:**
1. Check if `SENDGRID_API_KEY` is set in `.env`
2. Verify API key is valid (run `python email_service.py`)
3. Check logs for error messages
4. Verify sender email is authenticated in SendGrid

### Invalid Sender Email
**Problem:** Error: "The from email does not match a verified Sender Identity"

**Solution:**
1. Go to SendGrid Dashboard → Settings → Sender Authentication
2. Verify your domain or single sender email
3. Update `SENDGRID_FROM_EMAIL` in `.env` to match verified sender

### API Key Invalid
**Problem:** Error: "Unauthorized"

**Solution:**
1. Check if API key starts with `SG.`
2. Verify API key has "Mail Send" permissions
3. Generate new API key if needed:
   - SendGrid Dashboard → Settings → API Keys
   - Create API Key with "Mail Send" permission

### Rate Limiting
**Problem:** Too many emails being rejected

**Solution:**
1. Check your SendGrid plan limits
2. Implement delays between batch emails if needed
3. Use the batch email endpoint which handles this automatically

## Best Practices

### 1. Email Verification
Always verify sender emails in SendGrid before using them.

### 2. Content Guidelines
- Keep subject lines under 50 characters
- Include both HTML and plain text versions
- Make emails mobile-responsive
- Include unsubscribe links for marketing emails

### 3. Deliverability
- Authenticate your domain (SPF, DKIM, DMARC)
- Avoid spam trigger words
- Monitor bounce rates
- Clean your email list regularly

### 4. Testing
Test emails before sending to production:
```python
# Send test email to yourself
service.send_welcome_email(
    to_email="your-email@example.com",
    name="Test User",
    company="Test Company"
)
```

### 5. Error Handling
Always check the response:
```python
result = service.send_welcome_email(email, name, company)
if result["success"]:
    print(f"Email sent: {result['message_id']}")
else:
    print(f"Failed: {result['message']}")
```

## Security Notes

1. **Never commit `.env` file** - It contains your API key
2. **Use environment variables** - Don't hardcode API keys
3. **Rotate API keys regularly** - Generate new keys periodically
4. **Limit API key permissions** - Only grant "Mail Send" permission
5. **Monitor usage** - Check SendGrid dashboard for unusual activity

## Support

### SendGrid Resources
- Documentation: https://docs.sendgrid.com/
- API Reference: https://docs.sendgrid.com/api-reference/
- Support: https://support.sendgrid.com/

### Application Support
- Check logs in console output
- Review `email_service.py` for implementation details
- Test connection with `python email_service.py`

## Next Steps

1. ✅ Install SendGrid package
2. ✅ Configure `.env` with API key and sender email
3. ✅ Verify sender in SendGrid dashboard
4. ✅ Test connection with `python email_service.py`
5. ✅ Run application: `python streamlined_app.py`
6. ✅ Test by saving a business card with email
7. ✅ Monitor SendGrid dashboard for delivery status

---

**Questions?** Check the SendGrid documentation or review the `email_service.py` implementation.
