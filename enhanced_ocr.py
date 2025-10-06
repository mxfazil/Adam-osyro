"""
Enhanced OCR Application with Web Scraping and AI Chatbot
Integrates business card OCR with comprehensive information gathering and AI assistance
Version 2.0.0 - Production Ready
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
from pydantic import BaseModel, Field, validator
from PIL import Image
import io

# Import base OCR application and its components
from updated import (
    app as ocr_app, 
    supabase, 
    verify_api_key,
    extract_fields_with_llama,
    BusinessCardCreate,
    BusinessCardResponse,
    APIResponse
)

# Import new enhancement modules
from webscraper import TavilyWebScraper, create_scraper
from chatbot import GeminiChatbot, create_chatbot

# Setup enhanced logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler for better visibility
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# ========================================
# PYDANTIC MODELS FOR ENHANCED FEATURES
# ========================================

class EnhancedBusinessCardRequest(BaseModel):
    """Request model for enhanced business card processing"""
    name: str = Field(..., min_length=1, max_length=200, description="Person's name")
    company: Optional[str] = Field(None, max_length=200, description="Company name")
    extract_web_info: bool = Field(True, description="Whether to extract additional web information")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('company')
    def validate_company(cls, v):
        if v:
            return v.strip()
        return v

class ChatRequest(BaseModel):
    """Request model for chat"""
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    session_id: Optional[str] = Field(None, description="Chat session ID")
    context: Optional[Dict] = Field(None, description="Additional context (e.g., business card data)")
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()

class WebInfoResponse(BaseModel):
    """Response model for web information"""
    success: bool
    person_info: Optional[Dict] = None
    company_info: Optional[Dict] = None
    search_timestamp: str
    message: str
    sources: Optional[List[str]] = None
    search_queries: Optional[List[str]] = None

class ChatResponse(BaseModel):
    """Response model for chat"""
    success: bool
    response: str
    session_id: str
    timestamp: str
    suggestions: Optional[List[str]] = None
    context_used: bool = False
    token_count: Optional[int] = None

class EnhancedHealthCheck(BaseModel):
    """Enhanced health check response"""
    status: str
    timestamp: str
    version: str
    services: Dict[str, bool]
    uptime_seconds: Optional[float] = None

class EnhancedOCRResponse(BaseModel):
    """Enhanced OCR response with web info and AI analysis"""
    success: bool
    ocr_fields: Dict
    web_info: Optional[Dict] = None
    ai_analysis: Optional[str] = None
    processing_time_ms: Optional[float] = None
    message: str

class BatchChatRequest(BaseModel):
    """Request model for batch chat processing"""
    messages: List[str] = Field(..., min_items=1, max_items=10, description="List of messages")
    session_id: Optional[str] = Field(None, description="Chat session ID")
    context: Optional[Dict] = Field(None, description="Shared context for all messages")

class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str
    message_count: int
    created_at: str
    last_activity: str
    context_available: bool

# ========================================
# GLOBAL SERVICE INSTANCES
# ========================================

web_scraper: Optional[TavilyWebScraper] = None
ai_chatbot: Optional[GeminiChatbot] = None
service_start_time: datetime = datetime.now()

# ========================================
# SERVICE INITIALIZATION
# ========================================

def initialize_enhanced_services():
    """Initialize web scraper and chatbot services with proper error handling"""
    global web_scraper, ai_chatbot
    
    logger.info("=" * 60)
    logger.info("Initializing Enhanced Services")
    logger.info("=" * 60)
    
    # Initialize Tavily web scraper
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if tavily_api_key and tavily_api_key.strip():
        try:
            web_scraper = create_scraper(tavily_api_key)
            logger.info("✓ Tavily web scraper initialized successfully")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Tavily web scraper: {e}")
            web_scraper = None
    else:
        logger.warning("⚠ Tavily API key not found - web scraping disabled")
        web_scraper = None
    
    # Initialize Gemini chatbot
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key and gemini_api_key.strip():
        try:
            ai_chatbot = create_chatbot(gemini_api_key)
            logger.info("✓ Gemini AI chatbot initialized successfully")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Gemini chatbot: {e}")
            ai_chatbot = None
    else:
        logger.warning("⚠ Gemini API key not found - chatbot disabled")
        ai_chatbot = None
    
    logger.info("=" * 60)
    logger.info(f"Web Scraper: {'ACTIVE' if web_scraper else 'INACTIVE'}")
    logger.info(f"AI Chatbot: {'ACTIVE' if ai_chatbot else 'INACTIVE'}")
    logger.info("=" * 60)

def check_service_availability(service_name: str, service_instance: Any) -> None:
    """Check if a service is available and raise error if not"""
    if service_instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service_name} service is not available. Please check configuration."
        )

# ========================================
# ENHANCED OCR ENDPOINTS
# ========================================

@ocr_app.post("/api/v1/ocr/extract-enhanced", response_model=EnhancedOCRResponse, tags=["API - Enhanced OCR"])
async def api_extract_enhanced_business_card(
    file: UploadFile = File(..., description="Business card image"),
    extract_web_info: bool = Query(True, description="Extract additional web information"),
    generate_ai_analysis: bool = Query(True, description="Generate AI analysis"),
    api_key: str = Depends(verify_api_key)
):
    """
    Extract OCR information and optionally gather additional web information with AI analysis
    
    **Authentication:** Required (Bearer token)
    
    **Parameters:**
    - file: Business card image file (JPG, PNG, JPEG)
    - extract_web_info: Whether to extract additional information from web
    - generate_ai_analysis: Whether to generate AI-powered business context analysis
    
    **Returns:**
    - OCR fields, web information, and AI analysis
    """
    start_time = datetime.now()
    
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Please upload an image file (JPG, PNG, JPEG)."
            )
        
        # Read and validate image
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded"
            )
        
        try:
            image = Image.open(io.BytesIO(contents))
        except Exception as e:
            logger.error(f"Failed to open image: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or corrupted image file"
            )
        
        # Extract OCR fields
        logger.info(f"Extracting OCR fields from business card: {file.filename}")
        ocr_fields = extract_fields_with_llama(image)
        
        if not ocr_fields or not ocr_fields.get("name"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract name from business card. Please ensure the image is clear."
            )
        
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
                logger.info("Web information extracted successfully")
                
            except Exception as e:
                logger.error(f"Error extracting web information: {e}")
                result_data["web_info"] = {
                    "error": str(e),
                    "search_successful": False
                }
        
        # Generate AI analysis if chatbot is available and web info was extracted
        if generate_ai_analysis and ai_chatbot and result_data.get("web_info"):
            try:
                logger.info("Generating AI business context analysis")
                analysis = ai_chatbot.analyze_business_context(
                    ocr_fields, 
                    result_data["web_info"]
                )
                result_data["ai_analysis"] = analysis
                logger.info("AI analysis generated successfully")
                
            except Exception as e:
                logger.error(f"Error generating AI analysis: {e}")
                result_data["ai_analysis"] = f"Analysis unavailable: {str(e)}"
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return EnhancedOCRResponse(
            success=True,
            ocr_fields=result_data["ocr_fields"],
            web_info=result_data.get("web_info"),
            ai_analysis=result_data.get("ai_analysis"),
            processing_time_ms=round(processing_time, 2),
            message="Business card extracted successfully with enhanced information"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in enhanced OCR extraction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process business card: {str(e)}"
        )

# ========================================
# WEB INFORMATION ENDPOINTS
# ========================================

@ocr_app.post("/api/v1/web-info/extract", response_model=WebInfoResponse, tags=["API - Web Information"])
async def api_extract_web_information(
    request: EnhancedBusinessCardRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Extract comprehensive web information for a person and company
    
    **Authentication:** Required (Bearer token)
    
    **Parameters:**
    - name: Person's name (required)
    - company: Company name (optional)
    - extract_web_info: Whether to perform web search (default: true)
    
    **Returns:**
    - Person information, company information, and sources
    """
    try:
        check_service_availability("Web scraping", web_scraper)
        
        logger.info(f"Extracting web information for {request.name}")
        
        # Extract comprehensive information
        web_info = web_scraper.get_comprehensive_info(request.name, request.company)
        
        # Extract sources if available
        sources = []
        if web_info.get("person", {}).get("sources"):
            sources.extend(web_info["person"]["sources"])
        if web_info.get("company", {}).get("sources"):
            sources.extend(web_info["company"]["sources"])
        
        # Extract search queries used
        search_queries = web_info.get("search_queries", [])
        
        return WebInfoResponse(
            success=web_info.get("search_successful", False),
            person_info=web_info.get("person"),
            company_info=web_info.get("company"),
            search_timestamp=web_info.get("timestamp", datetime.now().isoformat()),
            message="Web information extracted successfully" if web_info.get("search_successful") else "Partial information extracted",
            sources=sources[:10] if sources else None,  # Limit to top 10 sources
            search_queries=search_queries
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting web information: {e}", exc_info=True)
        return WebInfoResponse(
            success=False,
            search_timestamp=datetime.now().isoformat(),
            message=f"Error: {str(e)}"
        )

@ocr_app.get("/api/v1/web-info/person/{name}", response_model=WebInfoResponse, tags=["API - Web Information"])
async def api_get_person_info(
    name: str,
    company: Optional[str] = Query(None, description="Company name for better search"),
    api_key: str = Depends(verify_api_key)
):
    """
    Get web information about a person by name
    
    **Authentication:** Required (Bearer token)
    """
    try:
        check_service_availability("Web scraping", web_scraper)
        
        request = EnhancedBusinessCardRequest(name=name, company=company)
        return await api_extract_web_information(request, api_key)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting person info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# AI CHATBOT ENDPOINTS
# ========================================

@ocr_app.post("/api/v1/chat/message", response_model=ChatResponse, tags=["API - AI Chatbot"])
async def api_chat_message(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Send a message to the AI chatbot
    
    **Authentication:** Required (Bearer token)
    
    **Parameters:**
    - message: User message (required)
    - session_id: Chat session ID (optional, auto-generated if not provided)
    - context: Additional context like business card data (optional)
    
    **Returns:**
    - AI response, session ID, and optional follow-up suggestions
    """
    try:
        check_service_availability("AI chatbot", ai_chatbot)
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"Processing chat message for session {session_id}")
        
        # Generate response
        response_data = ai_chatbot.generate_response(
            session_id, 
            request.message, 
            request.context
        )
        
        if not response_data.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate AI response"
            )
        
        # Generate follow-up suggestions if context is available
        suggestions = None
        if request.context and response_data.get("success"):
            try:
                suggestions = ai_chatbot.suggest_follow_up_questions(request.context)
                logger.info(f"Generated {len(suggestions) if suggestions else 0} follow-up suggestions")
            except Exception as e:
                logger.error(f"Error generating suggestions: {e}")
        
        # Get token count if available
        token_count = response_data.get("token_count")
        
        return ChatResponse(
            success=True,
            response=response_data.get("response", ""),
            session_id=session_id,
            timestamp=response_data.get("timestamp", datetime.now().isoformat()),
            suggestions=suggestions,
            context_used=request.context is not None,
            token_count=token_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        return ChatResponse(
            success=False,
            response="I apologize, but I encountered an error while processing your message. Please try again.",
            session_id=request.session_id or str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            context_used=False
        )

@ocr_app.post("/api/v1/chat/batch", tags=["API - AI Chatbot"])
async def api_batch_chat(
    request: BatchChatRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Process multiple chat messages in a batch
    
    **Authentication:** Required (Bearer token)
    
    **Parameters:**
    - messages: List of messages (1-10 messages)
    - session_id: Chat session ID (optional)
    - context: Shared context for all messages
    """
    try:
        check_service_availability("AI chatbot", ai_chatbot)
        
        session_id = request.session_id or str(uuid.uuid4())
        responses = []
        
        for idx, message in enumerate(request.messages):
            try:
                response_data = ai_chatbot.generate_response(
                    session_id, 
                    message, 
                    request.context
                )
                responses.append({
                    "message_index": idx,
                    "success": response_data.get("success", False),
                    "response": response_data.get("response", ""),
                    "timestamp": response_data.get("timestamp", datetime.now().isoformat())
                })
            except Exception as e:
                logger.error(f"Error processing message {idx}: {e}")
                responses.append({
                    "message_index": idx,
                    "success": False,
                    "response": f"Error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
        
        return {
            "success": True,
            "session_id": session_id,
            "responses": responses,
            "total_messages": len(request.messages),
            "successful_messages": sum(1 for r in responses if r["success"]),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ocr_app.get("/api/v1/chat/sessions", tags=["API - AI Chatbot"])
async def api_list_chat_sessions(
    api_key: str = Depends(verify_api_key)
):
    """
    List all active chat sessions with details
    
    **Authentication:** Required (Bearer token)
    
    **Returns:**
    - List of session information including message count and activity
    """
    try:
        check_service_availability("AI chatbot", ai_chatbot)
        
        sessions = ai_chatbot.get_all_sessions()
        
        # Enhance session data with additional info
        session_details = []
        for session in sessions:
            session_id = session.get("session_id")
            if session_id:
                summary = ai_chatbot.get_conversation_summary(session_id)
                session_details.append(SessionInfo(
                    session_id=session_id,
                    message_count=summary.get("message_count", 0),
                    created_at=summary.get("created_at", ""),
                    last_activity=summary.get("last_activity", ""),
                    context_available=summary.get("has_context", False)
                ))
        
        return {
            "success": True,
            "sessions": session_details,
            "count": len(session_details),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing chat sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@ocr_app.get("/api/v1/chat/sessions/{session_id}", tags=["API - AI Chatbot"])
async def api_get_session(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get detailed information about a specific chat session
    
    **Authentication:** Required (Bearer token)
    """
    try:
        check_service_availability("AI chatbot", ai_chatbot)
        
        summary = ai_chatbot.get_conversation_summary(session_id)
        
        if summary.get("error"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=summary["error"]
            )
        
        return {
            "success": True,
            "session": summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}")
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
        check_service_availability("AI chatbot", ai_chatbot)
        
        summary = ai_chatbot.get_conversation_summary(session_id)
        
        if summary.get("error"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=summary["error"]
            )
        
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
    Clear/delete a chat session and its history
    
    **Authentication:** Required (Bearer token)
    """
    try:
        check_service_availability("AI chatbot", ai_chatbot)
        
        success = ai_chatbot.clear_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        logger.info(f"Session {session_id} cleared successfully")
        
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

@ocr_app.delete("/api/v1/chat/sessions", tags=["API - AI Chatbot"])
async def api_clear_all_sessions(
    api_key: str = Depends(verify_api_key)
):
    """
    Clear all chat sessions
    
    **Authentication:** Required (Bearer token)
    """
    try:
        check_service_availability("AI chatbot", ai_chatbot)
        
        sessions = ai_chatbot.get_all_sessions()
        cleared_count = 0
        
        for session in sessions:
            session_id = session.get("session_id")
            if session_id and ai_chatbot.clear_session(session_id):
                cleared_count += 1
        
        logger.info(f"Cleared {cleared_count} sessions")
        
        return {
            "success": True,
            "message": f"Cleared {cleared_count} sessions",
            "cleared_count": cleared_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing all sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# SYSTEM ENDPOINTS
# ========================================

@ocr_app.get("/api/v1/health-enhanced", response_model=EnhancedHealthCheck, tags=["API - System"])
async def api_enhanced_health_check():
    """
    Enhanced health check including all services
    No authentication required
    """
    uptime = (datetime.now() - service_start_time).total_seconds()
    
    return EnhancedHealthCheck(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="2.0.0",
        services={
            "ocr": True,
            "supabase": supabase is not None,
            "web_scraper": web_scraper is not None,
            "ai_chatbot": ai_chatbot is not None
        },
        uptime_seconds=round(uptime, 2)
    )

@ocr_app.get("/api/v1/services/status", tags=["API - System"])
async def api_services_status(api_key: str = Depends(verify_api_key)):
    """
    Get detailed status of all services
    
    **Authentication:** Required (Bearer token)
    """
    return {
        "success": True,
        "services": {
            "ocr": {
                "status": "active",
                "description": "Business card OCR extraction"
            },
            "database": {
                "status": "active" if supabase else "inactive",
                "description": "Supabase database connection",
                "connected": supabase is not None
            },
            "web_scraper": {
                "status": "active" if web_scraper else "inactive",
                "description": "Tavily web scraping service",
                "available": web_scraper is not None
            },
            "ai_chatbot": {
                "status": "active" if ai_chatbot else "inactive",
                "description": "Gemini AI chatbot service",
                "available": ai_chatbot is not None,
                "active_sessions": len(ai_chatbot.get_all_sessions()) if ai_chatbot else 0
            }
        },
        "version": "2.0.0",
        "uptime_seconds": round((datetime.now() - service_start_time).total_seconds(), 2),
        "timestamp": datetime.now().isoformat()
    }

# ========================================
# WEB INTERFACE ROUTES
# ========================================

@ocr_app.get("/enhanced", response_class=HTMLResponse, tags=["Web Interface"])
async def enhanced_home(request: Request):
    """Enhanced web interface with chatbot and web scraping"""
    try:
        templates = Jinja2Templates(directory="templates")
        return templates.TemplateResponse("enhanced_form.html", {
            "request": request,
            "web_scraper_available": web_scraper is not None,
            "chatbot_available": ai_chatbot is not None
        })
    except Exception as e:
        logger.error(f"Error rendering enhanced form: {e}")
        return HTMLResponse(
            content=f"<h1>Error</h1><p>Failed to load enhanced interface: {str(e)}</p>",
            status_code=500
        )

# ========================================
# STARTUP AND SHUTDOWN EVENTS
# ========================================

@ocr_app.on_event("startup")
async def enhanced_startup_event():
    """Initialize enhanced services on application startup"""
    global service_start_time
    service_start_time = datetime.now()
    
    logger.info("=" * 80)
    logger.info("ENHANCED OCR APPLICATION STARTUP")
    logger.info("=" * 80)
    
    initialize_enhanced_services()
    
    logger.info("=" * 80)
    logger.info("Enhanced OCR application started successfully")
    logger.info(f"Version: 2.0.0")
    logger.info(f"Startup time: {service_start_time.isoformat()}")
    logger.info(f"Enhanced API Documentation: http://127.0.0.1:8000/api/docs")
    logger.info(f"Enhanced Web Interface: http://127.0.0.1:8000/enhanced")
    logger.info("=" * 80)

@ocr_app.on_event("shutdown")
async def enhanced_shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("=" * 80)
    logger.info("Shutting down Enhanced OCR Application")
    logger.info("=" * 80)
    
    # Clear all chat sessions
    if ai_chatbot:
        try:
            sessions = ai_chatbot.get_all_sessions()
            for session in sessions:
                session_id = session.get("session_id")
                if session_id:
                    ai_chatbot.clear_session(session_id)
            logger.info("All chat sessions cleared")
        except Exception as e:
            logger.error(f"Error clearing sessions on shutdown: {e}")
    
    logger.info("Enhanced OCR Application shut down successfully")
    logger.info("=" * 80)

# ========================================
# MAIN ENTRY POINT
# ========================================

if __name__ == "__main__":
    import uvicorn
    
    # Initialize services before starting server
    initialize_enhanced_services()
    
    # Run the application
    uvicorn.run(
        "enhanced_updated:ocr_app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to True for development
        log_level="info"
    )