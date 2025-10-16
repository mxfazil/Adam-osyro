"""
Follow-up Email Scheduler

This module handles checking for unopened emails and sending follow-up emails
after 24 hours. It includes both manual execution and background scheduling.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import schedule
import time
import threading
from email_service import EmailService

logger = logging.getLogger(__name__)

class FollowUpEmailScheduler:
    """Scheduler for sending follow-up emails to users who haven't opened initial emails"""
    
    def __init__(self, email_service: EmailService, supabase_client=None):
        """
        Initialize follow-up email scheduler
        
        Args:
            email_service: EmailService instance for sending emails
            supabase_client: Supabase client for database operations
        """
        self.email_service = email_service
        self.supabase = supabase_client
        self.is_running = False
        self.scheduler_thread = None
        
    def find_emails_needing_followup(self, hours_threshold: float = 0.05) -> List[Dict]:
        """
        Find welcome emails that need follow-up after specified hours (opened or not)
        
        Args:
            hours_threshold: Hours to wait before sending follow-up (default 0.05 = 3 minutes)
            
        Returns:
            List of email tracking records that need follow-up
        """
        # Store threshold for scheduler frequency adjustment
        self._current_threshold_hours = hours_threshold
        if not self.supabase:
            logger.error("❌ Supabase client not available")
            return []
            
        try:
            # Calculate the threshold timestamp
            threshold_time = datetime.now() - timedelta(hours=hours_threshold)
            
            logger.info(f"🕐 Current time: {datetime.now().isoformat()}")
            logger.info(f"🔍 Looking for emails sent before: {threshold_time.isoformat()}")
            
            # Query for ALL welcome emails past threshold (opened or not)
            # The key change: removed .is_("opened_at", "null") filter
            result = self.supabase.table("email_tracking")\
                .select("""
                    id,
                    business_card_id,
                    email_address,
                    message_id,
                    sent_at,
                    opened_at,
                    follow_up_scheduled,
                    business_cards!business_card_id (
                        name,
                        company
                    )
                """)\
                .eq("email_type", "welcome")\
                .eq("follow_up_scheduled", False)\
                .is_("bounced_at", "null")\
                .lt("sent_at", threshold_time.isoformat())\
                .execute()
            
            emails_needing_followup = result.data if result.data else []
            
            # Log details about found emails
            if emails_needing_followup:
                logger.info(f"📧 Found emails ready for follow-up:")
                for email in emails_needing_followup:
                    logger.info(f"   📤 {email['email_address']} sent at {email['sent_at']}")
            else:
                logger.info(f"📭 No emails found meeting criteria")
            
            logger.info(f"📊 Found {len(emails_needing_followup)} emails needing follow-up (opened or not)")
            return emails_needing_followup
            
        except Exception as e:
            logger.error(f"❌ Error finding unopened emails: {e}")
            return []
    
    def send_followup_batch(self, hours_threshold: float = 0.05) -> Dict:
        """
        Send follow-up emails to all qualifying recipients
        
        Args:
            hours_threshold: Hours to wait before sending follow-up (default 0.05 = 3 minutes)
            
        Returns:
            Summary of follow-up emails sent
        """
        # Store threshold for scheduler frequency adjustment
        self._current_threshold_hours = hours_threshold
        logger.info(f"🔄 Starting follow-up email batch (threshold: {hours_threshold}h)")
        
        # Find emails that need follow-up
        unopened_emails = self.find_emails_needing_followup(hours_threshold)
        
        results = {
            "total_candidates": len(unopened_emails),
            "sent": 0,
            "failed": 0,
            "details": []
        }
        
        for email_record in unopened_emails:
            try:
                business_card_id = email_record["business_card_id"]
                email_address = email_record["email_address"]
                business_card = email_record.get("business_cards")
                
                # If business card data is not available from the join, fetch it separately
                if not business_card:
                    logger.warning(f"⚠️ Business card not found in join, fetching separately for ID {business_card_id}")
                    card_result = self.supabase.table("business_cards")\
                        .select("*")\
                        .eq("id", business_card_id)\
                        .limit(1)\
                        .execute()
                    
                    if card_result.data:
                        business_card = card_result.data[0]
                    else:
                        logger.error(f"❌ Could not find business card with ID {business_card_id}")
                        results["failed"] += 1
                        results["details"].append({
                            "name": "Unknown",
                            "email": email_address,
                            "status": "failed",
                            "reason": f"Business card not found (ID: {business_card_id})"
                        })
                        continue
                
                name = business_card.get("name", "Unknown")
                company = business_card.get("company")
                
                # Send follow-up email
                follow_up_result = self.email_service.send_follow_up_welcome_email(
                    to_email=email_address,
                    name=name,
                    company=company,
                    business_card_id=business_card_id
                )
                
                if follow_up_result["success"]:
                    results["sent"] += 1
                    results["details"].append({
                        "name": name,
                        "email": email_address,
                        "status": "sent",
                        "message_id": follow_up_result.get("message_id"),
                        "original_sent_at": email_record["sent_at"]
                    })
                    logger.info(f"✅ Follow-up sent to {name} ({email_address})")
                else:
                    results["failed"] += 1
                    results["details"].append({
                        "name": name,
                        "email": email_address,
                        "status": "failed",
                        "reason": follow_up_result["message"]
                    })
                    logger.error(f"❌ Failed to send follow-up to {email_address}: {follow_up_result['message']}")
                
                # Small delay to avoid overwhelming SendGrid
                time.sleep(1)
                
            except Exception as e:
                results["failed"] += 1
                logger.error(f"❌ Error processing follow-up for {email_record.get('email_address', 'unknown')}: {e}")
        
        logger.info(f"📧 Follow-up batch complete: {results['sent']}/{results['total_candidates']} sent")
        return results
    
    def schedule_daily_followups(self, hour: int = 10, minute: int = 0):
        """
        Schedule follow-up email checks - frequency depends on threshold
        
        Args:
            hour: Hour to run daily check (0-23, default 10 AM) - only used for 24h+ thresholds
            minute: Minute to run daily check (0-59, default 0) - only used for 24h+ thresholds
        """
        # Clear any existing schedule
        schedule.clear()
        
        # For very short thresholds (< 1 hour), check every 1 minute for precision
        # For short thresholds (< 24 hours), check every 5 minutes  
        # For long thresholds (24+ hours), check daily
        if hasattr(self, '_current_threshold_hours') and self._current_threshold_hours:
            if self._current_threshold_hours < 1:
                # Very short threshold - check every 1 minute for precise timing
                schedule.every(1).minute.do(self.run_scheduled_followups)
                logger.info(f"📅 Scheduled follow-up checks every 1 minute (threshold: {self._current_threshold_hours}h)")
            elif self._current_threshold_hours < 24:
                # Short threshold - check every 5 minutes
                schedule.every(5).minutes.do(self.run_scheduled_followups)
                logger.info(f"📅 Scheduled follow-up checks every 5 minutes (threshold: {self._current_threshold_hours}h)")
            else:
                # Normal threshold - check daily
                schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self.run_scheduled_followups)
                logger.info(f"📅 Scheduled daily follow-up checks at {hour:02d}:{minute:02d}")
        else:
            # Default to daily check if no threshold is set
            schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self.run_scheduled_followups)
            logger.info(f"📅 Scheduled daily follow-up checks at {hour:02d}:{minute:02d}")
    
    def run_scheduled_followups(self):
        """Run the scheduled follow-up email check"""
        try:
            # Use stored threshold, default to 3 minutes if not set
            threshold = getattr(self, '_current_threshold_hours', 0.05)
            logger.info(f"⏰ Running scheduled follow-up email check (threshold: {threshold}h)...")
            results = self.send_followup_batch(threshold)
            
            # Log summary
            if results["sent"] > 0:
                logger.info(f"📧 Scheduled follow-up complete: {results['sent']} emails sent")
            else:
                logger.info("📧 Scheduled follow-up complete: No emails needed follow-up")
                
        except Exception as e:
            logger.error(f"❌ Error in scheduled follow-up: {e}")
    
    def start_scheduler(self, hour: int = 10, minute: int = 0):
        """
        Start the background scheduler
        
        Args:
            hour: Hour to run daily check (default 10 AM)
            minute: Minute to run daily check (default 0)
        """
        if self.is_running:
            logger.warning("⚠️ Scheduler already running")
            return
        
        # Set initial threshold for 2-minute follow-ups
        self._current_threshold_hours = 0.05
        self.schedule_daily_followups(hour, minute)
        self.is_running = True
        
        def run_scheduler():
            logger.info("🚀 Follow-up email scheduler started")
            while self.is_running:
                schedule.run_pending()
                time.sleep(10)  # Check every 10 seconds for faster response
            logger.info("⏹️ Follow-up email scheduler stopped")
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        # Log appropriate message based on threshold
        if hasattr(self, '_current_threshold_hours') and self._current_threshold_hours < 1:
            logger.info(f"✅ Follow-up email scheduler started (every 3 minutes, threshold: {self._current_threshold_hours}h)")
        elif hasattr(self, '_current_threshold_hours') and self._current_threshold_hours < 24:
            logger.info(f"✅ Follow-up email scheduler started (every 5 minutes, threshold: {self._current_threshold_hours}h)")
        else:
            logger.info(f"✅ Follow-up email scheduler started (daily at {hour:02d}:{minute:02d})")
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        if not self.is_running:
            logger.warning("⚠️ Scheduler not running")
            return
        
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logger.info("⏹️ Follow-up email scheduler stopped")
    
    def get_follow_up_statistics(self) -> Dict:
        """
        Get statistics about follow-up emails
        
        Returns:
            Dictionary with follow-up email statistics
        """
        if not self.supabase:
            return {"error": "Supabase client not available"}
        
        try:
            # Get overall email statistics
            total_emails = self.supabase.table("email_tracking")\
                .select("*", count="exact")\
                .eq("email_type", "welcome")\
                .execute()
            
            opened_emails = self.supabase.table("email_tracking")\
                .select("*", count="exact")\
                .eq("email_type", "welcome")\
                .not_.is_("opened_at", "null")\
                .execute()
            
            follow_ups_sent = self.supabase.table("email_tracking")\
                .select("*", count="exact")\
                .eq("follow_up_scheduled", True)\
                .execute()
            
            # Calculate candidates for follow-up (using current threshold, default 2 minutes)
            threshold_hours = getattr(self, '_current_threshold_hours', 0.05)
            threshold_time = datetime.now() - timedelta(hours=threshold_hours)
            follow_up_candidates = self.supabase.table("email_tracking")\
                .select("*", count="exact")\
                .eq("email_type", "welcome")\
                .is_("opened_at", "null")\
                .eq("follow_up_scheduled", False)\
                .is_("bounced_at", "null")\
                .lt("sent_at", threshold_time.isoformat())\
                .execute()
            
            total_count = total_emails.count or 0
            opened_count = opened_emails.count or 0
            follow_ups_count = follow_ups_sent.count or 0
            candidates_count = follow_up_candidates.count or 0
            
            open_rate = (opened_count / total_count * 100) if total_count > 0 else 0
            
            return {
                "total_welcome_emails": total_count,
                "opened_emails": opened_count,
                "open_rate_percent": round(open_rate, 2),
                "follow_ups_sent": follow_ups_count,
                "pending_follow_ups": candidates_count,
                "scheduler_running": self.is_running
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting follow-up statistics: {e}")
            return {"error": str(e)}

# Factory function
def create_followup_scheduler(email_service: EmailService, supabase_client=None) -> FollowUpEmailScheduler:
    """
    Create follow-up email scheduler instance
    
    Args:
        email_service: EmailService instance
        supabase_client: Supabase client
        
    Returns:
        FollowUpEmailScheduler instance
    """
    return FollowUpEmailScheduler(email_service, supabase_client)

# Manual execution example
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from email_service import create_email_service
    
    load_dotenv()
    
    print("Follow-up Email Scheduler - Manual Run")
    print("=" * 50)
    
    # This would need actual supabase client in real usage
    # email_service = create_email_service()
    # scheduler = create_followup_scheduler(email_service, supabase_client)
    # results = scheduler.send_followup_batch()
    # print(f"Results: {results}")
    
    print("Note: Configure supabase client and run with proper initialization")