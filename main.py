"""
Streamlined OCR to Chat Application
Direct workflow: OCR → Web Scraping → Chat Interface with Profile Summary
"""

import os
import json
import uuid
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from fastapi import FastAPI, Form, File, UploadFile, Request, HTTPException, Depends, status, Query, Header
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)
from pydantic import BaseModel, Field

# Import existing modules
from ocr import (
    supabase, 
    verify_api_key, 
    extract_fields_with_llama,
    BusinessCardCreate,
    BusinessCardResponse,
    APIResponse
)

# Import enhanced modules
from tavily_direct import TavilyDirect, create_scraper
from chatbot import GeminiChatbot, create_chatbot
from email_service import EmailService, create_email_service
from webhook_handler import SendGridWebhookHandler, create_webhook_handler
from followup_scheduler import FollowUpEmailScheduler, create_followup_scheduler

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    initialize_services()
    logger.info("🚀 Streamlined OCR Chat application started")
    logger.info(f"🌐 Web Interface: http://127.0.0.1:8000/")
    logger.info(f"📚 API Documentation: http://127.0.0.1:8000/docs")
    yield
    # Shutdown
    logger.info("Application shutting down...")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Streamlined Business Card OCR with AI Chat",
    description="Upload business card → Get AI analysis → Chat with profile information",
    version="2.0.0",
    lifespan=lifespan
)

# Templates
templates = Jinja2Templates(directory="templates")

logger = logging.getLogger(__name__)

# Global instances
web_scraper: Optional[TavilyDirect] = None
ai_chatbot: Optional[GeminiChatbot] = None
email_service: Optional[EmailService] = None
webhook_handler: Optional[SendGridWebhookHandler] = None
followup_scheduler: Optional[FollowUpEmailScheduler] = None

# Session storage for profiles
user_sessions: Dict[str, Dict] = {}

def initialize_services():
    """Initialize web scraper, chatbot, email services, webhook handler, and follow-up scheduler"""
    global web_scraper, ai_chatbot, email_service, webhook_handler, followup_scheduler
    
    # Initialize web scraper
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    logger.info(f"🔍 Tavily API key found: {'Yes' if tavily_api_key else 'No'}")
    logger.info(f"🔍 Tavily key starts with: {tavily_api_key[:10] + '...' if tavily_api_key else 'None'}")
    
    if tavily_api_key and tavily_api_key != "your-tavily-api-key-here":
        try:
            web_scraper = create_scraper(tavily_api_key)
            logger.info("✅ Tavily web scraper initialized successfully")
        except Exception as scraper_error:
            logger.error(f"❌ Failed to initialize Tavily scraper: {scraper_error}")
            import traceback
            logger.error(f"❌ Tavily scraper error traceback: {traceback.format_exc()}")
            web_scraper = None
    else:
        logger.warning("⚠️ Tavily API key not valid - web scraping disabled")
        web_scraper = None
    
    # Initialize chatbot
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    logger.info(f"🤖 Gemini API key found: {'Yes' if gemini_api_key else 'No'}")
    logger.info(f"🤖 Gemini key starts with: {gemini_api_key[:10] + '...' if gemini_api_key else 'None'}")
    
    if gemini_api_key and gemini_api_key != "your-gemini-api-key-here":
        try:
            ai_chatbot = create_chatbot(gemini_api_key)
            logger.info("✅ Gemini chatbot initialized successfully")
        except Exception as chatbot_error:
            logger.error(f"❌ Failed to initialize Gemini chatbot: {chatbot_error}")
            import traceback
            logger.error(f"❌ Gemini chatbot error traceback: {traceback.format_exc()}")
            ai_chatbot = None
    else:
        logger.warning("⚠️ Gemini API key not valid - chatbot disabled")
        ai_chatbot = None
    
    # Initialize email service
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    logger.info(f"📧 SendGrid API key found: {'Yes' if sendgrid_api_key else 'No'}")
    
    if sendgrid_api_key and sendgrid_api_key != "your-sendgrid-api-key-here":
        try:
            from ocr import supabase  # Import supabase for email tracking
            email_service = create_email_service(sendgrid_api_key, supabase_client=supabase)
            logger.info("✅ SendGrid email service initialized successfully")
        except Exception as email_error:
            logger.error(f"❌ Failed to initialize SendGrid: {email_error}")
            import traceback
            logger.error(f"❌ SendGrid error traceback: {traceback.format_exc()}")
            email_service = None
    else:
        logger.warning("⚠️ SendGrid API key not valid - email service disabled")
        email_service = None

    # Initialize webhook handler (needs Supabase)
    try:
        from ocr import supabase  # Import supabase from ocr module
        webhook_handler = create_webhook_handler(supabase)
        logger.info("✅ SendGrid webhook handler initialized successfully")
    except Exception as webhook_error:
        logger.error(f"❌ Failed to initialize webhook handler: {webhook_error}")
        webhook_handler = None

    # Initialize follow-up scheduler (needs email service and supabase)
    if email_service:
        try:
            from ocr import supabase  # Import supabase from ocr module
            followup_scheduler = create_followup_scheduler(email_service, supabase)
            # Start the scheduler with 2-minute threshold
            followup_scheduler.start_scheduler()
            logger.info("✅ Follow-up email scheduler initialized and started")
        except Exception as scheduler_error:
            logger.error(f"❌ Failed to initialize follow-up scheduler: {scheduler_error}")
            followup_scheduler = None
    else:
        logger.warning("⚠️ Email service not available - follow-up scheduler disabled")
        followup_scheduler = None

# Pydantic models
class UserInfoRequest(BaseModel):
    """Request model for user information"""
    name: str = Field(..., description="Person's name")
    company: Optional[str] = Field(None, description="Company name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    source: str = Field(default="manual", description="Source: manual, ocr, or upload")

class ChatRequest(BaseModel):
    """Request model for chat"""
    message: str = Field(..., description="User message")
    session_id: str = Field(..., description="Session ID")

class ScrapeRequest(BaseModel):
    """Request model for web scraping"""
    name: str = Field(..., description="Person's name")
    company: Optional[str] = Field(None, description="Company name")

# Main landing page
@app.get("/", response_class=HTMLResponse, tags=["Web Interface"])
async def home(request: Request):
    """Main landing page with streamlined interface"""
    return templates.TemplateResponse("streamlined_form.html", {"request": request})

@app.post("/scrape-info", tags=["Web Interface"])
async def scrape_info(request: ScrapeRequest):
    """
    Scrape web information for a person and company using TavilyDirect
    """
    try:
        if not web_scraper:
            raise HTTPException(status_code=503, detail="Web scraper not available")
        
        if not request.name.strip():
            raise HTTPException(status_code=400, detail="Name is required")
        
        logger.info(f"🔍 Scraping information for {request.name}")

        # The TavilyDirect client uses requests (blocking). Run it in a thread
        # to avoid blocking the FastAPI event loop and to surface errors cleanly.
        try:
            web_info = await asyncio.to_thread(
                web_scraper.scrape_company_info,
                request.name,
                request.company if request.company else None
            )
        except Exception as ex:
            import traceback
            tb = traceback.format_exc()
            logger.error(f"❌ Tavily scraping call failed: {ex}\n{tb}")
            # Return useful debug info (without leaking secrets)
            return JSONResponse({
                "success": False,
                "message": "Tavily scraping failed",
                "error": str(ex),
                "trace": tb.splitlines()[-3:]
            }, status_code=500)
        
        return JSONResponse({
            "success": True,
            "web_info": web_info,
            "message": "Web information gathered successfully"
        })
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"❌ Web scraping error: {e}\n{tb}")
        return JSONResponse({
            "success": False,
            "message": f"Failed to gather web information: {str(e)}",
            "trace": tb.splitlines()[-3:]
        }, status_code=500)


@app.get("/debug/tavily-search", tags=["Debug"])
async def debug_tavily_search(q: str = "OpenAI", max_results: int = 2):
    """Debug endpoint to directly call TavilyDirect (bypasses Pydantic model parsing).

    Use this to quickly verify the Tavily client is reachable and the API key works.
    """
    try:
        if not web_scraper:
            raise HTTPException(status_code=503, detail="Web scraper not available")

        # Run the blocking request in a thread
        result = await asyncio.to_thread(web_scraper.search, q, max_results)

        return JSONResponse({"success": True, "query": q, "results_count": len(result.get('results', [])), "result": result})
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"❌ Debug Tavily search failed: {e}\n{tb}")
        return JSONResponse({"success": False, "message": str(e), "trace": tb.splitlines()[-3:]}, status_code=500)

# Process user information and redirect to chat
@app.post("/process-info", tags=["Web Interface"])
async def process_user_info(
    name: str = Form(...),
    company: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    source: str = Form("manual")
):
    """
    Process user information, perform web scraping, and redirect to chat
    """
    try:
        # Create session ID
        session_id = str(uuid.uuid4())
        
        # Basic user info
        user_info = {
            "name": name.strip(),
            "company": company.strip(),
            "email": email.strip(),
            "phone": phone.strip(),
            "source": source
        }
        
        # Initialize session data
        session_data = {
            "user_info": user_info,
            "web_info": None,
            "chat_history": [],
            "created_at": datetime.now().isoformat()
        }
        
        # Perform web scraping if available
        if web_scraper and name.strip():
            try:
                logger.info(f"🔍 Quick scraping information for {name}")
                # Use the new ultra-fast method
                web_info = web_scraper.quick_user_summary(name, company if company else None)
                session_data["web_info"] = web_info
                logger.info(f"✅ Quick web scraping completed for {name}")
            except Exception as e:
                logger.error(f"❌ Web scraping failed: {e}")
                session_data["web_info"] = {"error": str(e)}
        
        # Store session
        user_sessions[session_id] = session_data
        
        # Generate initial AI greeting if chatbot is available
        if ai_chatbot:
            try:
                context = {
                    "business_card": user_info,
                    "web_info": session_data.get("web_info")
                }
                
                initial_message = f"Hello! I've gathered information about {name}"
                if company:
                    initial_message += f" from {company}"
                initial_message += ". How can I help you with networking and professional insights?"
                
                # Create chat session
                ai_chatbot.create_session(session_id, context)
                
                # Add initial greeting to chat history
                session_data["chat_history"].append({
                    "role": "assistant",
                    "content": initial_message,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Error initializing chat: {e}")
        
        # Redirect to chat interface
        return RedirectResponse(url=f"/chat/{session_id}", status_code=303)
        
    except Exception as e:
        logger.error(f"❌ Error processing user info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# OCR extraction endpoint for form
@app.post("/extract", tags=["Web Interface"])
async def extract_card(
    file: UploadFile = File(None),
    camera_image: str = Form(None)
):
    """
    Extract information from business card image and return JSON response
    """
    try:
        from PIL import Image
        import io
        import base64
        
        # Handle both file upload and camera capture
        if file is not None:
            # File upload
            if not file.content_type.startswith("image/"):
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": "File must be an image"}
                )
            
            contents = await file.read()
            image = Image.open(io.BytesIO(contents))
            
        elif camera_image is not None:
            # Camera capture (base64 encoded)
            try:
                # Remove data URL prefix if present
                if camera_image.startswith('data:'):
                    camera_image = camera_image.split(',')[1]
                
                image_data = base64.b64decode(camera_image)
                image = Image.open(io.BytesIO(image_data))
            except Exception as e:
                logger.error(f"Failed to decode camera image: {e}")
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": "Invalid camera image data"}
                )
        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "No image provided"}
            )
        
        # Extract OCR fields
        logger.info("🔍 Extracting OCR from business card")
        ocr_fields = extract_fields_with_llama(image)
        
        # Return extracted fields
        return JSONResponse(content={
            "success": True,
            "fields": {
                "name": ocr_fields.get("name", ""),
                "email": ocr_fields.get("email", ""),
                "phone": ocr_fields.get("phone", ""),
                "company": ocr_fields.get("company", "")
            }
        })
        
    except Exception as e:
        logger.error(f"❌ OCR extraction failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"OCR extraction failed: {str(e)}"}
        )

# OCR upload endpoint
@app.post("/upload-card", tags=["Web Interface"])
async def upload_business_card(file: UploadFile = File(...)):
    """
    Upload and process business card, then redirect to chat
    """
    try:
        from PIL import Image
        import io
        
        # Validate file
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and process image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Extract OCR fields
        logger.info("🔍 Extracting OCR from business card")
        ocr_fields = extract_fields_with_llama(image)
        
        # Process the extracted information
        if ocr_fields.get("name") and ocr_fields["name"] != "Not Found":
            # Create form data from OCR results
            form_data = {
                "name": ocr_fields.get("name", ""),
                "company": ocr_fields.get("company", ""),
                "email": ocr_fields.get("email", ""),
                "phone": ocr_fields.get("phone", ""),
                "source": "ocr"
            }
            
            # Create session and process
            session_id = str(uuid.uuid4())
            session_data = {
                "user_info": form_data,
                "ocr_fields": ocr_fields,
                "web_info": None,
                "chat_history": [],
                "created_at": datetime.now().isoformat()
            }
            
            # Perform web scraping
            if web_scraper:
                try:
                    web_info = web_scraper.get_comprehensive_info(
                        form_data["name"], 
                        form_data["company"] if form_data["company"] else None
                    )
                    session_data["web_info"] = web_info
                except Exception as e:
                    logger.error(f"❌ Web scraping failed: {e}")
                    session_data["web_info"] = {"error": str(e)}
            
            # Store session
            user_sessions[session_id] = session_data
            
            # Initialize chat
            if ai_chatbot:
                try:
                    context = {
                        "business_card": form_data,
                        "ocr_fields": ocr_fields,
                        "web_info": session_data.get("web_info")
                    }
                    
                    ai_chatbot.create_session(session_id, context)
                    
                    initial_message = f"I've analyzed the business card for {form_data['name']}"
                    if form_data['company']:
                        initial_message += f" from {form_data['company']}"
                    initial_message += ". I've also gathered additional information from the web. What would you like to know?"
                    
                    session_data["chat_history"].append({
                        "role": "assistant",
                        "content": initial_message,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"❌ Error initializing chat: {e}")
            
            return RedirectResponse(url=f"/chat/{session_id}", status_code=303)
        else:
            # OCR failed to extract name
            return JSONResponse({
                "success": False,
                "message": "Could not extract name from business card. Please try a clearer image or enter information manually.",
                "ocr_fields": ocr_fields
            }, status_code=400)
            
    except Exception as e:
        logger.error(f"❌ Error processing business card: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Chat interface
@app.get("/chat/{session_id}", response_class=HTMLResponse, tags=["Web Interface"])
async def chat_interface(request: Request, session_id: str):
    """
    Chat interface with profile summary sidebar
    """
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = user_sessions[session_id]
    
    return templates.TemplateResponse("chat_interface.html", {
        "request": request,
        "session_id": session_id,
        "session_data": session_data
    })

# Chat test endpoint
@app.get("/api/chat/test", tags=["API"])
async def test_chat():
    """
    Test endpoint to verify chat service is working
    """
    try:
        if not ai_chatbot:
            return {
                "status": "error",
                "message": "AI chatbot not initialized",
                "gemini_api_key_configured": bool(os.getenv('GEMINI_API_KEY'))
            }
        
        # Test chat generation
        test_response = ai_chatbot.generate_response(
            "test-session",
            "Say 'Hello! Chat is working perfectly!'",
            {}
        )
        
        return {
            "status": "success",
            "message": "Chat service is operational",
            "test_response": test_response.get("response", "No response"),
            "model": ai_chatbot.model_name if hasattr(ai_chatbot, 'model_name') else "unknown"
        }
        
    except Exception as e:
        logger.error(f"❌ Chat test error: {str(e)}")
        return {
            "status": "error",
            "message": "Chat test failed",
            "error": str(e),
            "gemini_api_key_configured": bool(os.getenv('GEMINI_API_KEY'))
        }

# Chat API endpoint
@app.post("/api/chat", tags=["API"])
async def send_chat_message(request: ChatRequest):
    """
    Send message to AI chatbot
    """
    try:
        if not ai_chatbot:
            raise HTTPException(status_code=503, detail="AI chatbot not available")
        
        if request.session_id not in user_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = user_sessions[request.session_id]
        
        # Add user message to history
        session_data["chat_history"].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Get context
        context = {
            "business_card": session_data["user_info"],
            "web_info": session_data.get("web_info")
        }
        if "ocr_fields" in session_data:
            context["ocr_fields"] = session_data["ocr_fields"]
        
        # Generate AI response
        response_data = ai_chatbot.generate_response(
            request.session_id,
            request.message,
            context
        )
        
        if response_data.get("success"):
            # Add AI response to history
            session_data["chat_history"].append({
                "role": "assistant",
                "content": response_data["response"],
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "response": response_data["response"],
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "response": "Sorry, I encountered an error. Please try again.",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        # Add more detailed error logging
        import traceback
        logger.error(f"❌ Chat error traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "response": f"Sorry, I encountered an error: {str(e)}. Please try again.",
            "timestamp": datetime.now().isoformat()
        }

@app.post("/save", tags=["Web Interface"])
async def save_card(
    name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    company: str = Form("")
):
    """
    Save confirmed business card data to Supabase
    Used by the web interface
    """
    try:
        if not supabase:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        if not name.strip():
            raise HTTPException(status_code=400, detail="Name is required")
        
        data = {
            "name": name.strip(),
            "email": email.strip(),
            "phone": phone.strip(),
            "company": company.strip()
        }
        
        logger.info(f"Saving to Supabase: {data}")
        result = supabase.table("business_cards").insert(data).execute()
        card_id = result.data[0]['id']
        logger.info(f"Successfully saved card with ID: {card_id}")
        
        # Send welcome email if email service is available and email is provided
        email_sent = False
        if email_service and email.strip():
            try:
                email_result = email_service.send_welcome_email(
                    email.strip(), 
                    name.strip(), 
                    company.strip() if company.strip() else None,
                    business_card_id=card_id
                )
                email_sent = email_result["success"]
                if email_sent:
                    logger.info(f"📧 Welcome email sent to {email}")
                    if email_result.get("tracking_created"):
                        logger.info(f"📊 Email tracking record created for follow-up")
                else:
                    logger.warning(f"⚠️ Failed to send email: {email_result['message']}")
            except Exception as e:
                logger.error(f"❌ Email sending error: {e}")
        
        return JSONResponse({
            "success": True, 
            "message": "Business card saved successfully" + (" and welcome email sent" if email_sent else ""), 
            "data": {
                "id": card_id,
                "email_sent": email_sent
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving to Supabase: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save: {str(e)}")

@app.post("/save-web-info", tags=["Web Interface"])
async def save_web_info(
    name: str = Form(...),
    company: str = Form(""),
    web_info: str = Form(...)  # JSON string of web-scraped data
):
    """
    Save web-scraped information to Supabase
    """
    try:
        if not supabase:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Parse the web info JSON
        try:
            web_info_data = json.loads(web_info)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON in web_info: {str(e)}")
        
        # Prepare data for Supabase
        data = {
            "name": name.strip(),
            "company": company.strip(),
            "web_info": web_info_data,
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Saving web info to Supabase for {name}")
        logger.info(f"Web info data: {web_info_data}")
        result = supabase.table("web_scraped_data").insert(data).execute()
        logger.info(f"Successfully saved web info with ID: {result.data[0]['id']}")
        
        return JSONResponse({
            "success": True, 
            "message": "Web-scraped information saved successfully", 
            "data": {"id": result.data[0]['id']}
        })
        
    except HTTPException as http_error:
        logger.error(f"HTTP error saving web info to Supabase: {http_error.detail}")
        raise
    except Exception as e:
        logger.error(f"Error saving web info to Supabase: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to save web info: {str(e)}")

@app.post("/save-all", tags=["Web Interface"])
async def save_all(
    name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    company: str = Form(""),
    web_info: str = Form("")  # JSON string of web-scraped data
):
    """
    Save both business card and web-scraped information to Supabase (OPTIMIZED)
    """
    try:
        if not supabase:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Validate required fields
        if not name.strip():
            raise HTTPException(status_code=400, detail="Name is required")
        
        # Prepare business card data
        card_data = {
            "name": name.strip(),
            "email": email.strip(),
            "phone": phone.strip(),
            "company": company.strip()
        }
        
        logger.info(f"Saving business card to Supabase: {card_data}")
        
        # Save business card first (required for ID)
        card_result = supabase.table("business_cards").insert(card_data).execute()
        card_id = card_result.data[0]['id']
        logger.info(f"✅ Business card saved with ID: {card_id}")
        
        # Immediately return success to user while processing continues in background
        import asyncio
        
        # Start background tasks for web info and email (non-blocking)
        asyncio.create_task(process_web_info_background(name, company, web_info, card_id))
        if email_service and email.strip():
            asyncio.create_task(send_welcome_email_background(email.strip(), name.strip(), company.strip(), card_id))
        
        # Return immediately - much faster response!
        return JSONResponse({
            "success": True, 
            "message": "Business card saved successfully! Web scraping and email processing in progress...", 
            "data": {
                "card_id": card_id,
                "status": "processing"
            }
        })
        
    except HTTPException as http_error:
        logger.error(f"HTTP error saving to Supabase: {http_error.detail}")
        raise
    except Exception as e:
        logger.error(f"Error saving to Supabase: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to save information: {str(e)}")


# Background task for web info processing
async def process_web_info_background(name: str, company: str, web_info: str, card_id: int):
    """Process web info in background for faster response.

    Use asyncio.to_thread to run blocking Supabase calls off the event loop.
    """
    if not web_info.strip():
        return

    try:
        web_info_data = json.loads(web_info)
        web_data = {
            "name": name.strip(),
            "company": company.strip(),
            "web_info": web_info_data,
            "created_at": datetime.now().isoformat()
        }

        logger.info(f"📊 Background: Saving web info for {name}")

        # Run blocking Supabase insert in a thread
        def _insert():
            return supabase.table("web_scraped_data").insert(web_data).execute()

        web_result = await asyncio.to_thread(_insert)
        web_info_id = web_result.data[0]['id']
        logger.info(f"✅ Background: Web info saved with ID: {web_info_id}")

    except json.JSONDecodeError as e:
        logger.error(f"❌ Background: Invalid JSON in web_info: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Background: Error saving web info: {e}")


# Background task for email sending
async def send_welcome_email_background(email: str, name: str, company: str, card_id: int):
    """Send welcome email in background for faster response"""
    try:
        logger.info(f"📧 Background: Sending welcome email to {email}")
        # Run the blocking send_welcome_email in a thread to avoid blocking the event loop
        def _send():
            return email_service.send_welcome_email(
                email,
                name,
                company if company else None,
                business_card_id=card_id
            )

        email_result = await asyncio.to_thread(_send)
        
        if email_result["success"]:
            logger.info(f"✅ Background: Welcome email sent to {email}")
            if email_result.get("tracking_created"):
                logger.info(f"📊 Background: Email tracking record created")
        else:
            logger.warning(f"⚠️ Background: Failed to send email: {email_result['message']}")
            
    except Exception as e:
        logger.error(f"❌ Background: Email sending error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

# Get session data API
@app.get("/api/session/{session_id}", tags=["API"])
async def get_session_data(session_id: str):
    """
    Get session data for profile display
    """
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return user_sessions[session_id]

# Quick status endpoint to check background processing
@app.get("/api/status/{card_id}", tags=["API"])
async def get_processing_status(card_id: int):
    """
    Check if background processing is complete for a business card
    """
    try:
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Check if web info exists for this card
        web_info_result = supabase.table("web_scraped_data")\
            .select("id")\
            .eq("name", "")\
            .execute()
        
        # Check if email tracking exists for this card  
        email_result = supabase.table("email_tracking")\
            .select("id, sent_at")\
            .eq("business_card_id", card_id)\
            .execute()
        
        return JSONResponse({
            "card_id": card_id,
            "web_info_processed": len(web_info_result.data) > 0,
            "email_sent": len(email_result.data) > 0,
            "status": "complete" if len(email_result.data) > 0 else "processing"
        })
        
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        return JSONResponse({"status": "error", "message": str(e)})

# Bulk email endpoint
@app.post("/api/send-bulk-emails", tags=["API"])
async def send_bulk_emails(api_key: str = Depends(verify_api_key)):
    """
    Send welcome emails to all contacts in database
    Requires API authentication
    """
    try:
        if not email_service:
            raise HTTPException(status_code=503, detail="Email service not available")
        
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Fetch all contacts with emails
        result = supabase.table("business_cards")\
            .select("name, email, company")\
            .not_.is_("email", "null")\
            .neq("email", "")\
            .execute()
        
        contacts = result.data
        
        if not contacts:
            return JSONResponse({
                "success": True,
                "message": "No contacts with emails found",
                "results": {"total": 0, "sent": 0, "failed": 0}
            })
        
        # Send batch emails
        results = email_service.send_batch_emails(contacts)
        
        return JSONResponse({
            "success": True,
            "message": f"Sent {results['sent']}/{results['total']} emails",
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Bulk email error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# SendGrid Webhook Endpoint
@app.post("/webhook/sendgrid", tags=["Webhooks"])
async def sendgrid_webhook(
    request: Request,
    x_twilio_email_event_webhook_signature: str = Header(None),
    x_twilio_email_event_webhook_timestamp: str = Header(None)
):
    """
    Handle SendGrid webhook events for email tracking
    """
    try:
        if not webhook_handler:
            raise HTTPException(status_code=503, detail="Webhook handler not available")
        
        # Get raw request body
        body = await request.body()
        
        # Verify webhook signature (optional but recommended)
        if x_twilio_email_event_webhook_signature and x_twilio_email_event_webhook_timestamp:
            signature_valid = webhook_handler.verify_webhook_signature(
                body, x_twilio_email_event_webhook_signature, x_twilio_email_event_webhook_timestamp
            )
            if not signature_valid:
                logger.warning("⚠️ Invalid webhook signature")
                # Continue processing anyway for development
        
        # Parse webhook events
        events = webhook_handler.parse_webhook_events(body)
        
        # Process each event
        results = []
        for event in events:
            result = await webhook_handler.process_webhook_event(event)
            results.append(result)
        
        return {
            "success": True,
            "processed_events": len(events),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"❌ Webhook processing error: {e}")
        import traceback
        logger.error(f"❌ Webhook error traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check
@app.get("/api/health", tags=["API"])
async def health_check():
    """
    Health check with service status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "web_scraper": web_scraper is not None,
            "ai_chatbot": ai_chatbot is not None,
            "email_service": email_service is not None,
            "webhook_handler": webhook_handler is not None,
            "followup_scheduler": followup_scheduler is not None,
            "supabase": supabase is not None
        },
        "email_tracking": {
            "enabled": email_service is not None and webhook_handler is not None,
            "scheduler_running": followup_scheduler is not None and getattr(followup_scheduler, 'is_running', False)
        },
        "version": "2.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    initialize_services()
    uvicorn.run(app, host="0.0.0.0", port=8000)