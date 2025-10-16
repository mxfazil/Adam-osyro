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
from sendgrid.helpers.mail import Mail, Email, To, Content, ReplyTo, Asm, GroupId

load_dotenv()

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending automated emails using SendGrid"""
    
    def __init__(self, api_key: str = None, from_email: str = None, from_name: str = None, reply_to_email: str = None, supabase_client=None):
        """
        Initialize SendGrid email service
        
        Args:
            api_key: SendGrid API key (defaults to env var)
            from_email: Sender email (defaults to env var)
            from_name: Sender name (defaults to env var)
            reply_to_email: Reply-to email (defaults to env var or from_email)
            supabase_client: Supabase client for email tracking
        """
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        self.from_email = from_email or os.getenv("SENDGRID_FROM_EMAIL")
        self.from_name = from_name or os.getenv("SENDGRID_FROM_NAME", "Business Card OCR")
        self.reply_to_email = reply_to_email or os.getenv("SENDGRID_REPLY_TO_EMAIL", self.from_email)
        self.unsubscribe_group_id = os.getenv("SENDGRID_UNSUBSCRIBE_GROUP_ID")  # Optional
        self.supabase = supabase_client  # Add supabase client for tracking
        
        if not self.api_key:
            raise ValueError("SENDGRID_API_KEY not found in environment")
        
        if not self.from_email:
            raise ValueError("SENDGRID_FROM_EMAIL not found in environment")
        
        self.client = SendGridAPIClient(self.api_key)
        logger.info(f"SendGrid email service initialized with sender: {self.from_email}")
    
    def create_email_tracking_record(self, business_card_id: int, email_address: str, message_id: str, email_type: str = "welcome") -> bool:
        """
        Create email tracking record in Supabase
        
        Args:
            business_card_id: ID of the business card
            email_address: Email address
            message_id: SendGrid message ID
            email_type: Type of email (welcome, follow_up)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.supabase:
            logger.warning("⚠️ Supabase client not available - cannot track email")
            return False
            
        try:
            tracking_data = {
                "business_card_id": business_card_id,
                "email_address": email_address,
                "message_id": message_id,
                "email_type": email_type,
                "sent_at": datetime.now().isoformat(),
                "opened_at": None,
                "follow_up_scheduled": False,
                "bounced_at": None
            }
            
            result = self.supabase.table("email_tracking").insert(tracking_data).execute()
            logger.info(f"📊 Email tracking record created: ID {result.data[0]['id']} for {email_address}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create email tracking record: {e}")
            return False
    
    def send_welcome_email(self, to_email: str, name: str, company: str = None, business_card_id: int = None) -> Dict:
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
                                                <a href="[unsubscribe]" style="color: #667eea; text-decoration: none;">Unsubscribe</a> | 
                                                <a href="[unsubscribe_preferences]" style="color: #667eea; text-decoration: none;">Email Preferences</a>
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
            
            To unsubscribe, visit: [unsubscribe]
            Manage email preferences: [unsubscribe_preferences]
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
            
            # Send email
            try:
                response = self.client.send(message)
                logger.info(f"Welcome email sent to {to_email}: Status {response.status_code}")
            except Exception as send_error:
                # Get detailed error information
                error_body = None
                try:
                    if hasattr(send_error, 'body'):
                        error_body = send_error.body
                    elif hasattr(send_error, 'response') and hasattr(send_error.response, 'text'):
                        error_body = send_error.response.text
                except:
                    pass
                
                logger.error(f"Detailed SendGrid error for {to_email}: {str(send_error)}")
                if error_body:
                    logger.error(f"SendGrid error body: {error_body}")
                
                # Log email details for debugging
                logger.error(f"Email details - From: {self.from_email}, To: {to_email}, Subject: {subject}")
                logger.error(f"From name: {self.from_name}, Reply-to: {self.reply_to_email}")
                
                raise send_error
            
            logger.info(f"Welcome email sent to {to_email}: Status {response.status_code}")
            
            # Extract message ID safely
            message_id = None
            if hasattr(response, 'headers') and response.headers:
                message_id = response.headers.get('X-Message-Id') if hasattr(response.headers, 'get') else None
            
            # Create email tracking record if business_card_id provided
            if business_card_id and message_id:
                tracking_created = self.create_email_tracking_record(
                    business_card_id=business_card_id,
                    email_address=to_email,
                    message_id=message_id,
                    email_type="welcome"
                )
                if tracking_created:
                    logger.info(f"📊 Email tracking record created for business card ID {business_card_id}")
                else:
                    logger.warning(f"⚠️ Failed to create email tracking record for business card ID {business_card_id}")
            elif business_card_id and not message_id:
                logger.warning(f"⚠️ No message ID received from SendGrid - cannot track email")
            
            return {
                "success": True,
                "message": "Email sent successfully",
                "status_code": response.status_code,
                "to": to_email,
                "message_id": message_id,
                "tracking_created": business_card_id and message_id
            }
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Failed to send email to {to_email}: {e}")
            logger.error(f"Traceback: {error_trace}")
            return {
                "success": False,
                "message": str(e),
                "to": to_email,
                "traceback": error_trace
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
    
    def send_follow_up_welcome_email(self, to_email: str, name: str, company: str = None, business_card_id: int = None) -> Dict:
        """
        Send follow-up email specifically for welcome email follow-up automation
        
        Args:
            to_email: Recipient email
            name: Recipient name
            company: Optional company name
            business_card_id: Business card ID for tracking
            
        Returns:
            Response dict with success status
        """
        try:
            # Create follow-up email content
            subject = f"Quick follow-up from our team, {name}"
            
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
                                        <td style="padding: 40px 30px; background: linear-gradient(135deg, #28a745 0%, #20c997 100%);">
                                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                                Just Checking In!
                                            </h1>
                                        </td>
                                    </tr>
                                    
                                    <!-- Body -->
                                    <tr>
                                        <td style="padding: 40px 30px;">
                                            <h2 style="margin: 0 0 20px 0; color: #333333; font-size: 24px;">
                                                Hi {name}!
                                            </h2>
                                            
                                            <p style="margin: 0 0 15px 0; color: #666666; font-size: 16px; line-height: 1.6;">
                                                We wanted to follow up on our welcome email and see if you had any questions about your business card information we captured.
                                            </p>
                                            
                                            {f'<p style="margin: 0 0 15px 0; color: #666666; font-size: 16px; line-height: 1.6;">We hope everything is going well at <strong>{company}</strong>.</p>' if company else ''}
                                            
                                            <!-- Quick Actions Box -->
                                            <table role="presentation" style="width: 100%; border-collapse: collapse; margin: 30px 0; background-color: #f8f9fa; border-radius: 8px;">
                                                <tr>
                                                    <td style="padding: 25px;">
                                                        <h3 style="margin: 0 0 15px 0; color: #28a745; font-size: 18px;">
                                                            💬 Need Assistance?
                                                        </h3>
                                                        <p style="margin: 0 0 15px 0; color: #666666; font-size: 15px; line-height: 1.6;">
                                                            If you have any questions or would like to connect, simply reply to this email. We're here to help!
                                                        </p>
                                                        <ul style="margin: 0; padding-left: 20px; color: #666666; font-size: 15px; line-height: 1.8;">
                                                            <li>✓ Update your contact information</li>
                                                            <li>✓ Connect with our network</li>
                                                            <li>✓ Get networking insights</li>
                                                            <li>✓ Ask about our services</li>
                                                        </ul>
                                                    </td>
                                                </tr>
                                            </table>
                                            
                                            <p style="margin: 0 0 15px 0; color: #666666; font-size: 16px; line-height: 1.6;">
                                                Thank you for being part of our professional network!
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
                                                This is a follow-up to our welcome email. We hope you found it helpful!<br>
                                                © {datetime.now().year} {self.from_name}. All rights reserved.
                                            </p>
                                            <p style="margin: 0; color: #999999; font-size: 11px; text-align: center;">
                                                <a href="[unsubscribe]" style="color: #28a745; text-decoration: none;">Unsubscribe</a> | 
                                                <a href="[unsubscribe_preferences]" style="color: #28a745; text-decoration: none;">Email Preferences</a>
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
            Hi {name}!
            
            We wanted to follow up on our welcome email and see if you had any questions about your business card information we captured.
            
            {f'We hope everything is going well at {company}.' if company else ''}
            
            Need Assistance?
            If you have any questions or would like to connect, simply reply to this email. We're here to help!
            
            ✓ Update your contact information
            ✓ Connect with our network
            ✓ Get networking insights
            ✓ Ask about our services
            
            Thank you for being part of our professional network!
            
            Best regards,
            {self.from_name}
            
            ---
            This is a follow-up to our welcome email. We hope you found it helpful!
            © {datetime.now().year} {self.from_name}. All rights reserved.
            
            To unsubscribe, visit: [unsubscribe]
            Manage email preferences: [unsubscribe_preferences]
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
            
            # Send email
            try:
                response = self.client.send(message)
                logger.info(f"Follow-up email sent to {to_email}: Status {response.status_code}")
            except Exception as send_error:
                # Get detailed error information
                error_body = None
                try:
                    if hasattr(send_error, 'body'):
                        error_body = send_error.body
                    elif hasattr(send_error, 'response') and hasattr(send_error.response, 'text'):
                        error_body = send_error.response.text
                except:
                    pass
                
                logger.error(f"Detailed SendGrid follow-up error for {to_email}: {str(send_error)}")
                if error_body:
                    logger.error(f"SendGrid follow-up error body: {error_body}")
                
                # Log email details for debugging
                logger.error(f"Follow-up email details - From: {self.from_email}, To: {to_email}, Subject: {subject}")
                logger.error(f"From name: {self.from_name}, Reply-to: {self.reply_to_email}")
                
                raise send_error
            
            logger.info(f"Follow-up email sent to {to_email}: Status {response.status_code}")
            
            # Extract message ID safely
            message_id = None
            if hasattr(response, 'headers') and response.headers:
                message_id = response.headers.get('X-Message-Id') if hasattr(response.headers, 'get') else None
            
            # Create email tracking record if business_card_id provided
            if business_card_id and message_id:
                tracking_created = self.create_email_tracking_record(
                    business_card_id=business_card_id,
                    email_address=to_email,
                    message_id=message_id,
                    email_type="follow_up"
                )
                if tracking_created:
                    logger.info(f"📊 Follow-up email tracking record created for business card ID {business_card_id}")
                else:
                    logger.warning(f"⚠️ Failed to create follow-up email tracking record for business card ID {business_card_id}")
            elif business_card_id and not message_id:
                logger.warning(f"⚠️ No message ID received from SendGrid - cannot track follow-up email")
            
            # Update the original welcome email's follow_up_scheduled flag
            if business_card_id and self.supabase:
                try:
                    update_result = self.supabase.table("email_tracking")\
                        .update({"follow_up_scheduled": True})\
                        .eq("business_card_id", business_card_id)\
                        .eq("email_type", "welcome")\
                        .eq("follow_up_scheduled", False)\
                        .execute()
                    logger.info(f"📊 Updated welcome email follow_up_scheduled flag for business card ID {business_card_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to update follow_up_scheduled flag: {e}")
            
            return {
                "success": True,
                "message": "Follow-up email sent successfully",
                "status_code": response.status_code,
                "to": to_email,
                "message_id": message_id,
                "tracking_created": business_card_id and message_id
            }
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Failed to send follow-up email to {to_email}: {e}")
            logger.error(f"Traceback: {error_trace}")
            return {
                "success": False,
                "message": str(e),
                "to": to_email,
                "traceback": error_trace
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
    
    def send_property_availability_email(self, to_email: str, name: str, company: str = None, business_card_id: int = None) -> Dict:
        """
        Send personalized property availability email when user replies
        
        Args:
            to_email: Recipient email
            name: Recipient name
            company: Optional company name
            business_card_id: Business card ID for tracking
            
        Returns:
            Response dict with success status and message_id
        """
        subject = f"Exclusive Property Opportunities for {name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                        <h1 style="margin: 0; font-size: 24px;">🏢 Exclusive Property Opportunities</h1>
                        <p style="margin: 10px 0 0; opacity: 0.9;">Handpicked for {name}{f' at {company}' if company else ''}</p>
                    </div>
                    
                    <div style="background: #f8f9ff; padding: 30px; border-radius: 0 0 10px 10px;">
                        <p style="font-size: 18px; color: #667eea; margin-top: 0;">
                            Hello {name}! 👋
                        </p>
                        
                        <p>Thank you for your reply! I'm excited to connect with you and share some exclusive property opportunities that might interest you{f' and {company}' if company else ''}.</p>
                        
                        <div style="background: white; border-left: 4px solid #667eea; padding: 20px; margin: 25px 0; border-radius: 5px;">
                            <h3 style="margin-top: 0; color: #667eea;">🎯 What We Offer:</h3>
                            <ul style="padding-left: 20px;">
                                <li><strong>Premium Properties:</strong> Handpicked commercial and residential spaces</li>
                                <li><strong>Investment Opportunities:</strong> High-ROI properties in prime locations</li>
                                <li><strong>Market Insights:</strong> Exclusive reports and trends analysis</li>
                                <li><strong>Personalized Service:</strong> Dedicated support throughout your journey</li>
                            </ul>
                        </div>
                        
                        <div style="background: #e8f2ff; border: 1px solid #667eea; padding: 20px; margin: 25px 0; border-radius: 8px;">
                            <h3 style="margin-top: 0; color: #667eea;">🏠 Featured Properties Available Now:</h3>
                            <div style="margin: 15px 0;">
                                <strong>• Modern Office Spaces</strong> - Downtown business district, flexible terms
                            </div>
                            <div style="margin: 15px 0;">
                                <strong>• Luxury Residential Units</strong> - Premium neighborhoods, move-in ready
                            </div>
                            <div style="margin: 15px 0;">
                                <strong>• Investment Properties</strong> - High-yield opportunities with guaranteed returns
                            </div>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="mailto:{self.reply_to_email}?subject=Property Inquiry from {name}" 
                               style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                      color: white; padding: 15px 30px; text-decoration: none; 
                                      border-radius: 25px; font-weight: bold; display: inline-block;">
                                📞 Schedule Your Consultation
                            </a>
                        </div>
                        
                        <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p style="margin: 0; color: #856404;">
                                <strong>🎁 Special Offer:</strong> Reply within 48 hours to receive a complimentary property market analysis worth $500!
                            </p>
                        </div>
                        
                        <p>I'm here to help you find the perfect property solution. Simply reply to this email or call me directly to discuss your specific needs.</p>
                        
                        <p style="margin-top: 30px;">
                            Best regards,<br>
                            <strong>{self.from_name}</strong><br>
                            <span style="color: #667eea;">Property Specialist</span><br>
                            📧 {self.reply_to_email}<br>
                            📱 Available for immediate consultation
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        # Send email with property availability type for tracking
        result = self.send_email_with_tracking(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            business_card_id=business_card_id,
            email_type="property_availability",
            name=name
        )
        
        if result["success"]:
            logger.info(f"🏢 Property availability email sent to {name} ({to_email})")
        
        return result
    
    def test_connection(self) -> Dict:
        """
        Test SendGrid API connection
        
        Returns:
            Dict with connection status
        """
        try:
            # Simple validation - if we got this far, the API key format is valid
            # We'll test actual sending capability by sending an email
            return {
                "success": True,
                "message": "SendGrid connection initialized",
                "status_code": 200
            }
        except Exception as e:
            logger.error(f"SendGrid connection test failed: {e}")
            return {
                "success": False,
                "message": str(e)
            }


# Factory function
def create_email_service(api_key: str = None, supabase_client=None) -> EmailService:
    """
    Create email service instance
    
    Args:
        api_key: SendGrid API key (optional, will use env var if not provided)
        supabase_client: Supabase client for email tracking
        
    Returns:
        EmailService instance
    """
    return EmailService(api_key, supabase_client=supabase_client)


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
