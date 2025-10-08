"""
Email Service Module using SendGrid
Sends automated emails to business card contacts
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, ReplyTo, Asm, GroupId, GroupsToDisplay

load_dotenv()

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending automated emails using SendGrid"""
    
    def __init__(self, api_key: str = None, from_email: str = None, from_name: str = None, reply_to_email: str = None):
        """
        Initialize SendGrid email service
        
        Args:
            api_key: SendGrid API key (defaults to env var)
            from_email: Sender email (defaults to env var)
            from_name: Sender name (defaults to env var)
            reply_to_email: Reply-to email (defaults to env var or from_email)
        """
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        self.from_email = from_email or os.getenv("SENDGRID_FROM_EMAIL")
        self.from_name = from_name or os.getenv("SENDGRID_FROM_NAME", "Business Card OCR")
        self.reply_to_email = reply_to_email or os.getenv("SENDGRID_REPLY_TO_EMAIL", self.from_email)
        self.unsubscribe_group_id = os.getenv("SENDGRID_UNSUBSCRIBE_GROUP_ID")  # Optional
        
        if not self.api_key:
            raise ValueError("SENDGRID_API_KEY not found in environment")
        
        if not self.from_email:
            raise ValueError("SENDGRID_FROM_EMAIL not found in environment")
        
        self.client = SendGridAPIClient(self.api_key)
        logger.info(f"SendGrid email service initialized with sender: {self.from_email}")
    
    def send_welcome_email(self, to_email: str, name: str, company: str = None) -> Dict:
        """
        Send welcome email to new contact
        
        Args:
            to_email: Recipient email
            name: Recipient name
            company: Optional company name
            
        Returns:
            Response dict with success status
        """
        try:
            # Create email content - less promotional subject
            subject = f"Thank you for connecting, {name}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                </head>
                <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
                    <table role="presentation" style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td align="center" style="padding: 40px 0;">
                                <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                                    <!-- Header -->
                                    <tr>
                                        <td style="padding: 40px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                                Welcome to Our Network!
                                            </h1>
                                        </td>
                                    </tr>
                                    
                                    <!-- Body -->
                                    <tr>
                                        <td style="padding: 40px 30px;">
                                            <h2 style="margin: 0 0 20px 0; color: #333333; font-size: 24px;">
                                                Hello {name}!
                                            </h2>
                                            
                                            <p style="margin: 0 0 15px 0; color: #666666; font-size: 16px; line-height: 1.6;">
                                                Thank you for connecting with us. Your business card information has been successfully saved in our system.
                                            </p>
                                            
                                            {f'<p style="margin: 0 0 15px 0; color: #666666; font-size: 16px; line-height: 1.6;">We look forward to staying connected with you and <strong>{company}</strong>.</p>' if company else ''}
                                            
                                            <!-- Info Box -->
                                            <table role="presentation" style="width: 100%; border-collapse: collapse; margin: 30px 0; background-color: #f8f9fa; border-radius: 8px;">
                                                <tr>
                                                    <td style="padding: 25px;">
                                                        <h3 style="margin: 0 0 15px 0; color: #667eea; font-size: 18px;">
                                                            What's Next?
                                                        </h3>
                                                        <ul style="margin: 0; padding-left: 20px; color: #666666; font-size: 15px; line-height: 1.8;">
                                                            <li>Your information is securely stored and protected</li>
                                                            <li>You'll receive relevant updates and insights</li>
                                                            <li>Stay connected with our professional network</li>
                                                            <li>Access exclusive networking opportunities</li>
                                                        </ul>
                                                    </td>
                                                </tr>
                                            </table>
                                            
                                            <p style="margin: 0 0 15px 0; color: #666666; font-size: 16px; line-height: 1.6;">
                                                If you have any questions or need assistance, please don't hesitate to reach out to us.
                                            </p>
                                            
                                            <p style="margin: 30px 0 0 0; color: #666666; font-size: 16px; line-height: 1.6;">
                                                Best regards,<br>
                                                <strong style="color: #333333;">{self.from_name}</strong>
                                            </p>
                                        </td>
                                    </tr>
                                    
                                    <!-- Footer -->
                                    <tr>
                                        <td style="padding: 30px; background-color: #f8f9fa; border-top: 1px solid #e9ecef;">
                                            <p style="margin: 0 0 10px 0; color: #999999; font-size: 12px; line-height: 1.5; text-align: center;">
                                                This email was sent because your business card was scanned into our system.<br>
                                                © {datetime.now().year} {self.from_name}. All rights reserved.
                                            </p>
                                            <p style="margin: 0; color: #999999; font-size: 11px; text-align: center;">
                                                <a href="{{{{unsubscribe}}}}" style="color: #667eea; text-decoration: none;">Unsubscribe</a> | 
                                                <a href="{{{{unsubscribe_preferences}}}}" style="color: #667eea; text-decoration: none;">Email Preferences</a>
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
            </html>
            """
            
            # Create plain text version
            plain_text = f"""
            Hello {name}!
            
            Thank you for connecting with us. Your business card information has been successfully saved in our system.
            
            {f'We look forward to staying connected with you and {company}.' if company else ''}
            
            What's Next?
            - Your information is securely stored and protected
            - You'll receive relevant updates and insights
            - Stay connected with our professional network
            - Access exclusive networking opportunities
            
            If you have any questions or need assistance, please don't hesitate to reach out to us.
            
            Best regards,
            {self.from_name}
            
            ---
            This email was sent because your business card was scanned into our system.
            © {datetime.now().year} {self.from_name}. All rights reserved.
            
            To unsubscribe, visit: {{{{unsubscribe}}}}
            Manage email preferences: {{{{unsubscribe_preferences}}}}
            """
            
            # Create message
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=subject,
                plain_text_content=Content("text/plain", plain_text),
                html_content=Content("text/html", html_content)
            )
            
            # Add reply-to for better deliverability
            if self.reply_to_email and self.reply_to_email != self.from_email:
                message.reply_to = ReplyTo(self.reply_to_email)
            
            # Add unsubscribe group if configured
            if self.unsubscribe_group_id:
                message.asm = Asm(GroupId(int(self.unsubscribe_group_id)))
            
            # Add tracking settings for better engagement metrics
            message.tracking_settings = {
                "click_tracking": {"enable": True, "enable_text": False},
                "open_tracking": {"enable": True},
                "subscription_tracking": {
                    "enable": True,
                    "text": "If you would like to unsubscribe and stop receiving these emails click here: <% unsubscribe %>.",
                    "html": "<p>If you would like to unsubscribe and stop receiving these emails <% click here %>.</p>"
                }
            }
            
            # Send email
            response = self.client.send(message)
            
            logger.info(f"Welcome email sent to {to_email}: Status {response.status_code}")
            
            return {
                "success": True,
                "message": "Email sent successfully",
                "status_code": response.status_code,
                "to": to_email,
                "message_id": response.headers.get('X-Message-Id')
            }
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return {
                "success": False,
                "message": str(e),
                "to": to_email
            }
    
    def send_batch_emails(self, contacts: List[Dict]) -> Dict:
        """
        Send emails to multiple contacts
        
        Args:
            contacts: List of dicts with 'email', 'name', and optional 'company' keys
            
        Returns:
            Summary of sent emails
        """
        results = {
            "total": len(contacts),
            "sent": 0,
            "failed": 0,
            "details": []
        }
        
        for contact in contacts:
            email = contact.get("email")
            name = contact.get("name", "there")
            company = contact.get("company")
            
            if not email or not email.strip():
                results["failed"] += 1
                results["details"].append({
                    "name": name,
                    "email": None,
                    "status": "failed",
                    "reason": "No email provided"
                })
                continue
            
            result = self.send_welcome_email(email.strip(), name, company)
            
            if result["success"]:
                results["sent"] += 1
                results["details"].append({
                    "name": name,
                    "email": email,
                    "status": "sent",
                    "message_id": result.get("message_id"),
                    "status_code": result.get("status_code")
                })
            else:
                results["failed"] += 1
                results["details"].append({
                    "name": name,
                    "email": email,
                    "status": "failed",
                    "reason": result["message"]
                })
        
        logger.info(f"Batch email complete: {results['sent']}/{results['total']} sent")
        return results
    
    def send_custom_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str,
        plain_text: str = None,
        name: str = None
    ) -> Dict:
        """
        Send custom email
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email content
            plain_text: Plain text version (optional, will be extracted from HTML if not provided)
            name: Optional recipient name
            
        Returns:
            Response dict
        """
        try:
            # If no plain text provided, create a simple version
            if not plain_text:
                # Strip HTML tags for plain text (basic)
                import re
                plain_text = re.sub('<[^<]+?>', '', html_content)
            
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=subject,
                plain_text_content=Content("text/plain", plain_text),
                html_content=Content("text/html", html_content)
            )
            
            # Add reply-to
            if self.reply_to_email and self.reply_to_email != self.from_email:
                message.reply_to = ReplyTo(self.reply_to_email)
            
            # Add unsubscribe group if configured
            if self.unsubscribe_group_id:
                message.asm = Asm(GroupId(int(self.unsubscribe_group_id)))
            
            response = self.client.send(message)
            logger.info(f"Custom email sent to {to_email}: Status {response.status_code}")
            
            return {
                "success": True,
                "message": "Email sent successfully",
                "status_code": response.status_code,
                "message_id": response.headers.get('X-Message-Id')
            }
            
        except Exception as e:
            logger.error(f"Failed to send custom email: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def send_follow_up_email(self, to_email: str, name: str, company: str = None, days_since_scan: int = 7) -> Dict:
        """
        Send follow-up email after initial contact
        
        Args:
            to_email: Recipient email
            name: Recipient name
            company: Optional company name
            days_since_scan: Number of days since card was scanned
            
        Returns:
            Response dict
        """
        subject = f"Following up with you, {name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #667eea;">Hello {name}!</h2>
                    
                    <p>It's been {days_since_scan} days since we connected, and I wanted to reach out to see how things are going{f' at {company}' if company else ''}.</p>
                    
                    <p>I'd love to:</p>
                    <ul>
                        <li>Learn more about your current projects</li>
                        <li>Explore potential collaboration opportunities</li>
                        <li>Share insights that might be valuable to you</li>
                    </ul>
                    
                    <p>Would you be available for a brief call or meeting in the coming weeks?</p>
                    
                    <p style="margin-top: 30px;">
                        Looking forward to connecting,<br>
                        <strong>{self.from_name}</strong>
                    </p>
                </div>
            </body>
        </html>
        """
        
        return self.send_custom_email(to_email, subject, html_content, name=name)
    
    def test_connection(self) -> Dict:
        """
        Test SendGrid API connection
        
        Returns:
            Dict with connection status
        """
        try:
            # Try to get API key info (this validates the key)
            response = self.client.client.api_keys.get()
            return {
                "success": True,
                "message": "SendGrid connection successful",
                "status_code": response.status_code
            }
        except Exception as e:
            logger.error(f"SendGrid connection test failed: {e}")
            return {
                "success": False,
                "message": str(e)
            }


# Factory function
def create_email_service(api_key: str = None) -> EmailService:
    """
    Create email service instance
    
    Args:
        api_key: SendGrid API key (optional, will use env var if not provided)
        
    Returns:
        EmailService instance
    """
    return EmailService(api_key)


# Example usage
if __name__ == "__main__":
    # Test the email service
    service = create_email_service()
    
    # Test connection
    connection_test = service.test_connection()
    print("Connection test:", connection_test)
    
    # Send single email (replace with your test email)
    # result = service.send_welcome_email("test@example.com", "John Doe", "Acme Corp")
    # print("Email result:", result)
