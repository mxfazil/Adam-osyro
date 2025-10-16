"""
SendGrid Webhook Handler for Email Event Tracking

This module handles incoming webhooks from SendGrid to track email events
like opens, clicks, bounces, etc. for the follow-up email system.
"""

import logging
import json
import hmac
import hashlib
import base64
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, Header
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class SendGridWebhookHandler:
    """Handles SendGrid webhook events for email tracking"""
    
    def __init__(self, supabase_client=None):
        """
        Initialize webhook handler
        
        Args:
            supabase_client: Supabase client for database operations
        """
        self.supabase = supabase_client
        # Get webhook verification key from environment
        self.webhook_verify_key = os.getenv("SENDGRID_WEBHOOK_VERIFY_KEY")
        
    def verify_webhook_signature(self, request_body: bytes, signature: str, timestamp: str) -> bool:
        """
        Verify SendGrid webhook signature for security
        
        Args:
            request_body: Raw request body
            signature: Signature from X-Twilio-Email-Event-Webhook-Signature header
            timestamp: Timestamp from X-Twilio-Email-Event-Webhook-Timestamp header
            
        Returns:
            True if signature is valid
        """
        if not self.webhook_verify_key:
            logger.warning("⚠️ SENDGRID_WEBHOOK_VERIFY_KEY not configured - skipping verification")
            return True
            
        try:
            # Create expected signature
            public_key = base64.b64decode(self.webhook_verify_key)
            payload = timestamp.encode('utf-8') + request_body
            expected_signature = base64.b64encode(
                hmac.new(public_key, payload, hashlib.sha256).digest()
            ).decode('utf-8')
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"❌ Webhook signature verification failed: {e}")
            return False
    
    def process_webhook_events(self, events: List[Dict]) -> Dict:
        """
        Process multiple webhook events from SendGrid
        
        Args:
            events: List of event dictionaries from SendGrid
            
        Returns:
            Processing summary
        """
        results = {
            "total_events": len(events),
            "processed": 0,
            "errors": 0,
            "event_types": {}
        }
        
        for event in events:
            try:
                event_type = event.get('event')
                if event_type not in results["event_types"]:
                    results["event_types"][event_type] = 0
                results["event_types"][event_type] += 1
                
                success = self.process_single_event(event)
                if success:
                    results["processed"] += 1
                else:
                    results["errors"] += 1
                    
            except Exception as e:
                logger.error(f"❌ Error processing event: {e}")
                results["errors"] += 1
        
        logger.info(f"📊 Webhook processing complete: {results}")
        return results
    
    def process_single_event(self, event: Dict) -> bool:
        """
        Process a single SendGrid event
        
        Args:
            event: Single event dictionary from SendGrid
            
        Returns:
            True if processed successfully
        """
        try:
            event_type = event.get('event')
            message_id = event.get('sg_message_id')
            email = event.get('email')
            timestamp = event.get('timestamp')
            
            if not message_id:
                logger.warning(f"⚠️ No message_id in event: {event_type}")
                return False
            
            # Convert timestamp to datetime
            event_time = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
            
            logger.info(f"📧 Processing {event_type} event for {email} (ID: {message_id})")
            
            # Update email tracking based on event type
            if event_type == 'delivered':
                return self.update_email_tracking(message_id, delivered_at=event_time)
            elif event_type == 'open':
                # When email is opened, immediately check if we should trigger property email
                result = self.update_email_tracking(message_id, opened_at=event_time)
                
                # IMMEDIATE property email trigger on open (more reliable than reply detection)
                logger.info(f"📖 Welcome email opened by {email} - triggering property email immediately")
                self.check_and_send_property_email_immediately(event)
                
                return result
            elif event_type == 'click':
                return self.update_email_tracking(message_id, clicked_at=event_time)
            elif event_type == 'bounce':
                return self.update_email_tracking(message_id, bounced_at=event_time)
            elif event_type == 'unsubscribe':
                return self.update_email_tracking(message_id, unsubscribed_at=event_time)
            elif event_type == 'reply':
                # Handle email reply - trigger property availability email
                logger.info(f"📬 REPLY EVENT DETECTED for {email}!")
                logger.info(f"📬 Full reply event data: {json.dumps(event, indent=2)}")
                self.handle_email_reply(event)
                return self.update_email_tracking(message_id, replied_at=event_time)
            elif event_type == 'inbound':
                # Alternative reply detection - SendGrid sometimes uses 'inbound' for replies
                logger.info(f"📬 INBOUND EMAIL DETECTED for {email} - treating as reply!")
                logger.info(f"📬 Full inbound event data: {json.dumps(event, indent=2)}")
                self.handle_email_reply(event)
                return self.update_email_tracking(message_id, replied_at=event_time)
            else:
                logger.info(f"ℹ️ Ignoring event type: {event_type}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error processing single event: {e}")
            return False
    
    def update_email_tracking(self, message_id: str, **kwargs) -> bool:
        """
        Update email tracking record with event data
        
        Args:
            message_id: SendGrid message ID
            **kwargs: Fields to update (opened_at, clicked_at, etc.)
            
        Returns:
            True if updated successfully
        """
        if not self.supabase:
            logger.error("❌ Supabase client not available")
            return False
            
        try:
            # Find the email tracking record
            result = self.supabase.table("email_tracking")\
                .select("*")\
                .eq("message_id", message_id)\
                .execute()
            
            if not result.data:
                logger.warning(f"⚠️ No email tracking record found for message_id: {message_id}")
                return False
            
            # Update the record
            update_data = {k: v.isoformat() if hasattr(v, 'isoformat') else v 
                          for k, v in kwargs.items()}
            
            update_result = self.supabase.table("email_tracking")\
                .update(update_data)\
                .eq("message_id", message_id)\
                .execute()
            
            if update_result.data:
                logger.info(f"✅ Updated email tracking for {message_id}: {kwargs}")
                
                # Special handling for email opens - update business card record too
                if 'opened_at' in kwargs:
                    self.update_business_card_email_status(message_id)
                
                return True
            else:
                logger.error(f"❌ Failed to update email tracking for {message_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating email tracking: {e}")
            return False
    
    def update_business_card_email_status(self, message_id: str) -> bool:
        """
        Update business card email status when email is opened
        
        Args:
            message_id: SendGrid message ID
            
        Returns:
            True if updated successfully
        """
        try:
            # Get the business card ID from email tracking
            tracking_result = self.supabase.table("email_tracking")\
                .select("business_card_id")\
                .eq("message_id", message_id)\
                .execute()
            
            if not tracking_result.data:
                return False
            
            business_card_id = tracking_result.data[0]["business_card_id"]
            
            # Update business card with email opened status
            self.supabase.table("business_cards")\
                .update({"email_opened": True})\
                .eq("id", business_card_id)\
                .execute()
            
            logger.info(f"✅ Updated business card {business_card_id} - email opened")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating business card email status: {e}")
            return False

    def handle_email_reply(self, event: Dict) -> None:
        """
        Handle email reply events and trigger property availability emails
        
        Args:
            event: SendGrid reply event data
        """
        try:
            message_id = event.get('sg_message_id')
            email = event.get('email')
            reply_text = event.get('text', '')  # Reply content if available
            
            logger.info(f"📬 Email reply detected from {email} (ID: {message_id})")
            
            if not self.supabase:
                logger.error("❌ Supabase client not available for reply handling")
                return
            
            # Find the original email tracking record
            tracking_result = self.supabase.table("email_tracking")\
                .select("*, business_cards!business_card_id(id, name, email, company)")\
                .eq("message_id", message_id)\
                .eq("email_type", "welcome")\
                .execute()
            
            if not tracking_result.data:
                logger.warning(f"⚠️ No welcome email tracking found for reply from {email}")
                return
            
            tracking_record = tracking_result.data[0]
            business_card = tracking_record.get("business_cards")
            
            if not business_card:
                logger.error(f"❌ No business card found for reply from {email}")
                return
            
            # Check if we've already sent a property email to avoid duplicates
            property_email_check = self.supabase.table("email_tracking")\
                .select("id")\
                .eq("email_address", email)\
                .eq("email_type", "property_availability")\
                .execute()
            
            if property_email_check.data:
                logger.info(f"ℹ️ Property email already sent to {email}, skipping duplicate")
                return
            
            # Import email service here to avoid circular imports
            try:
                from email_service import create_email_service
                email_service = create_email_service(supabase_client=self.supabase)
                
                # Send property availability email
                result = email_service.send_property_availability_email(
                    to_email=email,
                    name=business_card.get("name", "Valued Client"),
                    company=business_card.get("company"),
                    business_card_id=business_card.get("id")
                )
                
                if result.get("success"):
                    logger.info(f"🏢 ✅ Property availability email sent to {email}")
                    
                    # Update the original email tracking to mark reply handled
                    self.supabase.table("email_tracking")\
                        .update({"property_email_sent": True})\
                        .eq("message_id", message_id)\
                        .execute()
                else:
                    logger.error(f"❌ Failed to send property email to {email}: {result.get('message')}")
                    
            except Exception as email_error:
                logger.error(f"❌ Error sending property email: {email_error}")
                
        except Exception as e:
            logger.error(f"❌ Error handling email reply: {e}")

    def parse_webhook_events(self, request_body: bytes) -> List[Dict]:
        """
        Parse SendGrid webhook events from request body
        
        Args:
            request_body: Raw request body from webhook
            
        Returns:
            List of parsed event dictionaries
        """
        try:
            events_data = json.loads(request_body.decode('utf-8'))
            
            # SendGrid sends events as an array
            if isinstance(events_data, list):
                logger.info(f"📧 Parsed {len(events_data)} webhook events")
                return events_data
            else:
                # Single event wrapped in array
                logger.info(f"📧 Parsed single webhook event")
                return [events_data]
                
        except Exception as e:
            logger.error(f"❌ Error parsing webhook events: {e}")
            return []

    async def process_webhook_event(self, event: Dict) -> Dict:
        """
        Process a single webhook event (async wrapper for synchronous processing)
        
        Args:
            event: Single event dictionary from SendGrid
            
        Returns:
            Processing result dictionary
        """
        try:
            # Call the synchronous method
            success = self.process_single_event(event)
            
            return {
                "event_type": event.get('event'),
                "email": event.get('email'),
                "message_id": event.get('sg_message_id'),
                "success": success,
                "timestamp": event.get('timestamp')
            }
            
        except Exception as e:
            logger.error(f"❌ Error in async event processing: {e}")
            return {
                "event_type": event.get('event', 'unknown'),
                "email": event.get('email', 'unknown'),
                "success": False,
                "error": str(e)
            }


# Factory function

    def check_and_send_property_email(self, event: Dict) -> None:
        """
        Check if we should send property email based on email open event
        Alternative trigger method when reply detection isn't working
        
        Args:
            event: SendGrid open event data
        """
        try:
            message_id = event.get('sg_message_id')
            email = event.get('email')
            
            logger.info(f"📖 Email opened by {email} (ID: {message_id}) - checking for property email trigger")
            
            if not self.supabase:
                logger.error("❌ Supabase client not available for property email check")
                return
            
            # Find the email tracking record
            tracking_result = self.supabase.table("email_tracking")\
                .select("*, business_cards!business_card_id(id, name, email, company)")\
                .eq("message_id", message_id)\
                .eq("email_type", "welcome")\
                .execute()
            
            if not tracking_result.data:
                logger.info(f"ℹ️ No welcome email tracking found for opened email from {email}")
                return
            
            tracking_record = tracking_result.data[0]
            business_card = tracking_record.get("business_cards")
            
            if not business_card:
                logger.error(f"❌ No business card found for opened email from {email}")
                return
            
            # Check if property email was already sent
            if tracking_record.get("property_email_sent"):
                logger.info(f"ℹ️ Property email already sent for {email}, skipping")
                return
            
            # Check if property email already exists in tracking table
            property_email_check = self.supabase.table("email_tracking")\
                .select("id")\
                .eq("email_address", email)\
                .eq("email_type", "property_availability")\
                .execute()
            
            if property_email_check.data:
                logger.info(f"ℹ️ Property email already exists in tracking for {email}, marking original as sent")
                # Mark the original email as having property email sent
                self.supabase.table("email_tracking")\
                    .update({"property_email_sent": True})\
                    .eq("id", tracking_record["id"])\
                    .execute()
                return
            
            # Import email service and send property email
            try:
                from email_service import create_email_service
                email_service = create_email_service(supabase_client=self.supabase)
                
                logger.info(f"🏢 Sending property email to {email} (triggered by email open)")
                
                # Send property availability email
                result = email_service.send_property_availability_email(
                    to_email=email,
                    name=business_card.get("name", "Valued Client"),
                    company=business_card.get("company"),
                    business_card_id=business_card.get("id")
                )
                
                if result.get("success"):
                    logger.info(f"🏢 ✅ Property availability email sent to {email} (auto-triggered)")
                    
                    # Update the original email tracking to mark property email sent
                    self.supabase.table("email_tracking")\
                        .update({"property_email_sent": True})\
                        .eq("id", tracking_record["id"])\
                        .execute()
                else:
                    logger.error(f"❌ Failed to send property email to {email}: {result.get('message')}")
                    
            except Exception as email_error:
                logger.error(f"❌ Error sending property email to {email}: {email_error}")
                
        except Exception as e:
            logger.error(f"❌ Error checking for property email trigger: {e}")

    def check_and_send_property_email_immediately(self, event: Dict) -> None:
        """
        IMMEDIATE property email trigger when welcome email is opened
        More reliable than waiting for replies
        
        Args:
            event: SendGrid open event data
        """
        try:
            message_id = event.get('sg_message_id')
            email = event.get('email')
            
            logger.info(f"🚀 IMMEDIATE property email trigger for {email} (welcome email opened)")
            
            if not self.supabase:
                logger.error("❌ Supabase client not available for immediate property email")
                return
            
            # Find the email tracking record for welcome email
            tracking_result = self.supabase.table("email_tracking")\
                .select("*, business_cards!business_card_id(id, name, email, company)")\
                .eq("message_id", message_id)\
                .eq("email_type", "welcome")\
                .execute()
            
            if not tracking_result.data:
                logger.info(f"ℹ️ No welcome email tracking found for {email}")
                return
            
            tracking_record = tracking_result.data[0]
            business_card = tracking_record.get("business_cards")
            
            if not business_card:
                logger.error(f"❌ No business card found for {email}")
                return
            
            # Check if property email was already sent
            if tracking_record.get("property_email_sent"):
                logger.info(f"ℹ️ Property email already sent for {email}, skipping")
                return
            
            # Double-check if property email already exists in tracking table
            property_email_check = self.supabase.table("email_tracking")\
                .select("id")\
                .eq("email_address", email)\
                .eq("email_type", "property_availability")\
                .execute()
            
            if property_email_check.data:
                logger.info(f"ℹ️ Property email record already exists for {email}, marking original as sent")
                self.supabase.table("email_tracking")\
                    .update({"property_email_sent": True})\
                    .eq("id", tracking_record["id"])\
                    .execute()
                return
            
            # Send property email immediately
            try:
                from email_service import create_email_service
                email_service = create_email_service(supabase_client=self.supabase)
                
                logger.info(f"🏢 Sending property email to {email} IMMEDIATELY (welcome email opened)")
                
                result = email_service.send_property_availability_email(
                    to_email=email,
                    name=business_card.get("name", "Valued Client"),
                    company=business_card.get("company"),
                    business_card_id=business_card.get("id")
                )
                
                if result.get("success"):
                    logger.info(f"🏢 ✅ IMMEDIATE property email sent to {email}!")
                    
                    # Mark the original welcome email as having property email sent
                    self.supabase.table("email_tracking")\
                        .update({"property_email_sent": True})\
                        .eq("id", tracking_record["id"])\
                        .execute()
                    
                    logger.info(f"✅ Property email tracking updated for {email}")
                else:
                    logger.error(f"❌ Failed to send immediate property email to {email}: {result.get('message')}")
                    
            except Exception as email_error:
                logger.error(f"❌ Error sending immediate property email to {email}: {email_error}")
                import traceback
                logger.error(f"❌ Full traceback: {traceback.format_exc()}")
                
        except Exception as e:
            logger.error(f"❌ Error in immediate property email trigger: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")

    def schedule_delayed_property_email(self, event: Dict) -> None:
        """
        Schedule property email to be sent 5 minutes after email is opened
        This gives users time to reply, but ensures they get property email either way
        
        Args:
            event: SendGrid open event data
        """
        try:
            message_id = event.get('sg_message_id')
            email = event.get('email')
            
            logger.info(f"⏰ Scheduling delayed property email for {email} (5 minutes after open)")
            
            if not self.supabase:
                logger.error("❌ Supabase client not available for scheduling")
                return
            
            # Mark this email as having a property email scheduled
            self.supabase.table("email_tracking")\
                .update({
                    "property_email_scheduled_at": datetime.now().isoformat()
                })\
                .eq("message_id", message_id)\
                .execute()
            
            # Import threading to run delayed task
            import threading
            import time
            
            def delayed_property_email():
                time.sleep(300)  # Wait 5 minutes
                
                # Check if user replied in the meantime
                try:
                    tracking_check = self.supabase.table("email_tracking")\
                        .select("replied_at, property_email_sent")\
                        .eq("message_id", message_id)\
                        .execute()
                    
                    if tracking_check.data:
                        record = tracking_check.data[0]
                        
                        # If user replied, don't send (reply should have triggered it already)
                        if record.get("replied_at"):
                            logger.info(f"ℹ️ User {email} replied - property email should have been sent via reply handler")
                            return
                        
                        # If property email already sent, skip
                        if record.get("property_email_sent"):
                            logger.info(f"ℹ️ Property email already sent to {email}")
                            return
                    
                    # Send property email after delay
                    logger.info(f"⏰ Sending delayed property email to {email}")
                    self.check_and_send_property_email(event)
                    
                except Exception as e:
                    logger.error(f"❌ Error in delayed property email for {email}: {e}")
            
            # Start background thread for delayed sending
            thread = threading.Thread(target=delayed_property_email, daemon=True)
            thread.start()
            
        except Exception as e:
            logger.error(f"❌ Error scheduling delayed property email: {e}")

# Factory function
def create_webhook_handler(supabase_client=None) -> SendGridWebhookHandler:
    """
    Create webhook handler instance
    
    Args:
        supabase_client: Supabase client
        
    Returns:
        SendGridWebhookHandler instance
    """
    return SendGridWebhookHandler(supabase_client)

# Example webhook event structure for reference
EXAMPLE_WEBHOOK_EVENTS = [
    {
        "email": "example@test.com",
        "timestamp": 1513299569,
        "smtp-id": "<14c5d75ce93.dfd.64b469@ismtpd-555>",
        "event": "processed",
        "category": "cat facts",
        "sg_event_id": "sg_event_id",
        "sg_message_id": "sg_message_id"
    },
    {
        "email": "example@test.com",
        "timestamp": 1513299569,
        "smtp-id": "<14c5d75ce93.dfd.64b469@ismtpd-555>",
        "event": "open",
        "category": "cat facts",
        "sg_event_id": "sg_event_id",
        "sg_message_id": "sg_message_id",
        "useragent": "Mozilla/4.0",
        "ip": "255.255.255.255"
    }
]