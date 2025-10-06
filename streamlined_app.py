"""
Streamlined OCR to Chat Application
Direct workflow: OCR → Web Scraping → Chat Interface with Profile Summary
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from fastapi import FastAPI, Form, File, UploadFile, Request, HTTPException, Depends, status, Query
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
from webscraper import TavilyWebScraper, create_scraper
from chatbot import AnthropicChatbot, create_chatbot

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
web_scraper: Optional[TavilyWebScraper] = None
ai_chatbot: Optional[AnthropicChatbot] = None

# Session storage for profiles
user_sessions: Dict[str, Dict] = {}

def initialize_services():
    """Initialize web scraper and chatbot services"""
    global web_scraper, ai_chatbot
    
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
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    logger.info(f"🤖 Anthropic API key found: {'Yes' if anthropic_api_key else 'No'}")
    logger.info(f"🤖 Anthropic key starts with: {anthropic_api_key[:10] + '...' if anthropic_api_key else 'None'}")
    
    if anthropic_api_key and anthropic_api_key != "your-anthropic-api-key-here":
        try:
            ai_chatbot = create_chatbot(anthropic_api_key)
            logger.info("✅ Anthropic chatbot initialized successfully")
        except Exception as chatbot_error:
            logger.error(f"❌ Failed to initialize Anthropic chatbot: {chatbot_error}")
            import traceback
            logger.error(f"❌ Anthropic chatbot error traceback: {traceback.format_exc()}")
            ai_chatbot = None
    else:
        logger.warning("⚠️ Anthropic API key not valid - chatbot disabled")
        ai_chatbot = None

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

# Main landing page
@app.get("/", response_class=HTMLResponse, tags=["Web Interface"])
async def home(request: Request):
    """Main landing page with streamlined interface"""
    return templates.TemplateResponse("streamlined_form.html", {"request": request})

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

# Get session data API
@app.get("/api/session/{session_id}", tags=["API"])
async def get_session_data(session_id: str):
    """
    Get session data for profile display
    """
    if session_id not in user_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return user_sessions[session_id]

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
            "supabase": supabase is not None
        },
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    initialize_services()
    uvicorn.run(app, host="0.0.0.0", port=8000)