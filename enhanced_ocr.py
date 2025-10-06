"""
Enhanced OCR Application with Web Scraping and AI Chatbot
Integrates business card OCR with comprehensive information gathering and AI assistance
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, Form, File, UploadFile, Request, HTTPException, Depends, status, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Import existing modules
from ocr import (
    app as ocr_app, 
    supabase, 
    verify_api_key, 
    extract_fields_with_llama,
    BusinessCardCreate,
    BusinessCardResponse,
    APIResponse
)

# Import new modules
from webscraper import TavilyWebScraper, create_scraper
from chatbot import GeminiChatbot, create_chatbot

logger = logging.getLogger(__name__)

# Pydantic models for new features
class EnhancedBusinessCardRequest(BaseModel):
    """Request model for enhanced business card processing"""
    name: str = Field(..., description="Person's name")
    company: Optional[str] = Field(None, description="Company name")
    extract_web_info: bool = Field(True, description="Whether to extract additional web information")

class ChatRequest(BaseModel):
    """Request model for chat"""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Chat session ID")
    context: Optional[Dict] = Field(None, description="Additional context")

class WebInfoResponse(BaseModel):
    """Response model for web information"""
    success: bool
    person_info: Optional[Dict] = None
    company_info: Optional[Dict] = None
    search_timestamp: str
    message: str

class ChatResponse(BaseModel):
    """Response model for chat"""
    success: bool
    response: str
    session_id: str
    timestamp: str
    suggestions: Optional[List[str]] = None

# Global instances
web_scraper: Optional[TavilyWebScraper] = None
ai_chatbot: Optional[GeminiChatbot] = None

def initialize_enhanced_services():
    """Initialize web scraper and chatbot services"""
    global web_scraper, ai_chatbot
    
    try:
        # Initialize web scraper
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if tavily_api_key:
            web_scraper = create_scraper(tavily_api_key)
            logger.info("Tavily web scraper initialized successfully")
        else:
            logger.warning("Tavily API key not found - web scraping disabled")
        
        # Initialize chatbot
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            ai_chatbot = create_chatbot(gemini_api_key)
            logger.info("Gemini chatbot initialized successfully")
        else:
            logger.warning("Gemini API key not found - chatbot disabled")
            
    except Exception as e:
        logger.error(f"Error initializing enhanced services: {e}")

# Enhanced OCR endpoint with web scraping
@ocr_app.post("/api/v1/ocr/extract-enhanced", response_model=APIResponse, tags=["API - Enhanced OCR"])
async def api_extract_enhanced_business_card(
    file: UploadFile = File(..., description="Business card image"),
    extract_web_info: bool = Query(True, description="Extract additional web information"),
    api_key: str = Depends(verify_api_key)
):
    """
    Extract OCR information and optionally gather additional web information
    
    **Authentication:** Required (Bearer token)
    
    **Parameters:**
    - file: Business card image file
    - extract_web_info: Whether to extract additional information from web
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
        logger.info("Extracting OCR fields from business card")
        ocr_fields = extract_fields_with_llama(image)
        
        result_data = {
            "ocr_fields": ocr_fields,
            "web_info": None,
            "ai_analysis": None
        }
        
        # Extract additional web information if requested
        if extract_web_info and web_scraper and ocr_fields.get("name"):
            try:
                logger.info(f"Extracting web information for {ocr_fields['name']}")
                web_info = web_scraper.get_comprehensive_info(
                    ocr_fields["name"], 
                    ocr_fields.get("company")
                )
                result_data["web_info"] = web_info
                
                # Generate AI analysis if chatbot is available
                if ai_chatbot:
                    analysis = ai_chatbot.analyze_business_context(ocr_fields, web_info)
                    result_data["ai_analysis"] = analysis
                    
            except Exception as e:
                logger.error(f"Error extracting web information: {e}")
                result_data["web_info"] = {"error": str(e)}
        
        return APIResponse(
            success=True,
            message="Business card extracted successfully with enhanced information",
            data=result_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in enhanced OCR extraction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Web information extraction endpoint
@ocr_app.post("/api/v1/web-info/extract", response_model=WebInfoResponse, tags=["API - Web Information"])
async def api_extract_web_information(
    request: EnhancedBusinessCardRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Extract comprehensive web information for a person and company
    
    **Authentication:** Required (Bearer token)
    """
    try:
        if not web_scraper:
            raise HTTPException(status_code=503, detail="Web scraping service not available")
        
        logger.info(f"Extracting web information for {request.name}")
        
        # Extract comprehensive information
        web_info = web_scraper.get_comprehensive_info(request.name, request.company)
        
        return WebInfoResponse(
            success=web_info.get("search_successful", False),
            person_info=web_info.get("person"),
            company_info=web_info.get("company"),
            search_timestamp=web_info.get("timestamp", datetime.now().isoformat()),
            message="Web information extracted successfully" if web_info.get("search_successful") else "Web information extraction failed"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting web information: {e}")
        return WebInfoResponse(
            success=False,
            search_timestamp=datetime.now().isoformat(),
            message=f"Error: {str(e)}"
        )

# Chatbot endpoints
@ocr_app.post("/api/v1/chat/message", response_model=ChatResponse, tags=["API - AI Chatbot"])
async def api_chat_message(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Send a message to the AI chatbot
    
    **Authentication:** Required (Bearer token)
    """
    try:
        if not ai_chatbot:
            raise HTTPException(status_code=503, detail="AI chatbot service not available")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"Processing chat message for session {session_id}")
        
        # Generate response
        response_data = ai_chatbot.generate_response(
            session_id, 
            request.message, 
            request.context
        )
        
        # Generate follow-up suggestions if context is available
        suggestions = None
        if request.context and response_data.get("success"):
            try:
                suggestions = ai_chatbot.suggest_follow_up_questions(request.context)
            except Exception as e:
                logger.error(f"Error generating suggestions: {e}")
        
        return ChatResponse(
            success=response_data.get("success", False),
            response=response_data.get("response", ""),
            session_id=session_id,
            timestamp=response_data.get("timestamp", datetime.now().isoformat()),
            suggestions=suggestions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        return ChatResponse(
            success=False,
            response="I apologize, but I encountered an error while processing your message.",
            session_id=request.session_id or str(uuid.uuid4()),
            timestamp=datetime.now().isoformat()
        )

@ocr_app.get("/api/v1/chat/sessions", tags=["API - AI Chatbot"])
async def api_list_chat_sessions(api_key: str = Depends(verify_api_key)):
    """
    List all active chat sessions
    
    **Authentication:** Required (Bearer token)
    """
    try:
        if not ai_chatbot:
            raise HTTPException(status_code=503, detail="AI chatbot service not available")
        
        sessions = ai_chatbot.get_all_sessions()
        
        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error listing chat sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ocr_app.get("/api/v1/chat/sessions/{session_id}/summary", tags=["API - AI Chatbot"])
async def api_get_session_summary(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get a summary of a chat session
    
    **Authentication:** Required (Bearer token)
    """
    try:
        if not ai_chatbot:
            raise HTTPException(status_code=503, detail="AI chatbot service not available")
        
        summary = ai_chatbot.get_conversation_summary(session_id)
        
        if summary.get("error"):
            raise HTTPException(status_code=404, detail=summary["error"])
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ocr_app.delete("/api/v1/chat/sessions/{session_id}", tags=["API - AI Chatbot"])
async def api_clear_chat_session(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Clear a chat session
    
    **Authentication:** Required (Bearer token)
    """
    try:
        if not ai_chatbot:
            raise HTTPException(status_code=503, detail="AI chatbot service not available")
        
        success = ai_chatbot.clear_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "success": True,
            "message": f"Session {session_id} cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced health check
@ocr_app.get("/api/health-enhanced", tags=["API - System"])
async def api_enhanced_health_check():
    """
    Enhanced health check including all services
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "ocr": True,
            "supabase_connected": supabase is not None,
            "web_scraper_available": web_scraper is not None,
            "ai_chatbot_available": ai_chatbot is not None
        },
        "version": "2.0.0"
    }

# Enhanced web interface route
@ocr_app.get("/enhanced", response_class=HTMLResponse, tags=["Web Interface"])
async def enhanced_home(request: Request):
    """Enhanced web interface with chatbot and web scraping"""
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("enhanced_form.html", {"request": request})

# Initialize enhanced services on startup
@ocr_app.on_event("startup")
async def enhanced_startup_event():
    initialize_enhanced_services()
    logger.info("Enhanced OCR application started with web scraping and AI chatbot")

if __name__ == "__main__":
    import uvicorn
    initialize_enhanced_services()
    uvicorn.run(ocr_app, host="0.0.0.0", port=8000)