"""
Business Card OCR Application with REST API
Combines web interface and REST API endpoints with auto-capture feature
"""

import requests
import json
import base64
import io
import os
from datetime import datetime
from typing import Optional, List
from dotenv import load_dotenv
from fastapi import FastAPI, Form, File, UploadFile, Request, HTTPException, Depends, status, Query, Header
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator
from supabase import create_client, Client
from PIL import Image
import logging

# Load environment variables
load_dotenv()

# -----------------------------
# Logging setup
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------
# Configuration
# -----------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
LLAMA_API_URL = os.getenv("LLAMA_API_URL")
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
LLAMA_DEPLOYMENT_NAME = os.getenv("LLAMA_DEPLOYMENT_NAME", "Llama-3.2-11B-Vision-Instruct")

# API Key for authentication (set this in .env for production)
API_KEY = os.getenv("API_KEY", "your-secret-api-key-change-this-in-production")

# Initialize Supabase
if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase credentials not found in environment variables")
    supabase = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        supabase = None

# Llama API headers
if LLAMA_API_URL and LLAMA_API_KEY:
    headers = {
        "Authorization": f"Bearer {LLAMA_API_KEY}",
        "Content-Type": "application/json"
    }
else:
    logger.error("Llama API credentials not found")
    headers = None

# -----------------------------
# FastAPI setup
# -----------------------------
app = FastAPI(
    title="Business Card OCR API",
    description="Extract and manage business card information using AI-powered OCR with auto-capture",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware for API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
security = HTTPBearer()

# -----------------------------
# Pydantic Models for API
# -----------------------------
class BusinessCardBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Full name of the person")
    email: Optional[str] = Field(None, max_length=200, description="Email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    company: Optional[str] = Field(None, max_length=200, description="Company/organization name")
    
    @validator('email')
    def validate_email(cls, v):
        if v and v.strip():
            # Basic email validation
            if '@' not in v or '.' not in v.split('@')[-1]:
                raise ValueError('Invalid email format')
        return v

class BusinessCardCreate(BusinessCardBase):
    """Model for creating a business card"""
    pass

class BusinessCardResponse(BusinessCardBase):
    """Model for business card response"""
    id: int
    created_at: str

class OCRResponse(BaseModel):
    """Model for OCR extraction response"""
    success: bool
    fields: Optional[dict] = None
    message: Optional[str] = None
    error: Optional[str] = None

class APIResponse(BaseModel):
    """Generic API response"""
    success: bool
    message: str
    data: Optional[dict] = None

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    supabase_connected: bool
    llama_api_configured: bool
    version: str

class PaginatedResponse(BaseModel):
    """Paginated list response"""
    success: bool
    data: List[BusinessCardResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# -----------------------------
# Authentication
# -----------------------------
def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify API key from Bearer token"""
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

def verify_api_key_header(x_api_key: str = Header(None)) -> str:
    """Alternative: Verify API key from X-API-Key header"""
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key in X-API-Key header"
        )
    return x_api_key

# -----------------------------
# Helper Functions
# -----------------------------
def encode_image(image: Image.Image, max_size: tuple = (1024, 1024)) -> str:
    """Encode image to base64 with optional resizing"""
    try:
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            logger.info(f"Image resized to {image.size}")
        
        buffer = io.BytesIO()
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        image.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        logger.error(f"Error encoding image: {e}")
        raise HTTPException(status_code=400, detail="Failed to process image")

def extract_fields_with_llama(image: Image.Image) -> dict:
    """Extract business card fields using Llama Vision API"""
    try:
        if not headers:
            raise HTTPException(status_code=503, detail="OCR service not configured")
        
        b64_img = encode_image(image)
        
        messages = [
            {
                "role": "system",
                "content": "You are an OCR assistant that extracts structured business card details. Always respond with valid JSON only."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Extract the following fields from this business card image:
- name (full name of the person)
- email (email address)
- phone (phone number)
- company (company/organization name)

Respond ONLY with a JSON object in this exact format:
{"name": "...", "email": "...", "phone": "...", "company": "..."}

If a field is not found, use an empty string."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64_img}"
                        }
                    }
                ]
            }
        ]
        
        payload = {
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 500
        }
        
        if "azure.com" in LLAMA_API_URL:
            payload["model"] = LLAMA_DEPLOYMENT_NAME
        else:
            payload["model"] = "Llama-3.2-11B-Vision-Instruct"
        
        logger.info("Sending request to Llama API...")
        
        response = requests.post(
            LLAMA_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        logger.info(f"Raw API response: {content}")
        
        # Parse JSON from response
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        parsed_data = json.loads(content)
        
        fields = {
            "name": parsed_data.get("name", ""),
            "email": parsed_data.get("email", ""),
            "phone": parsed_data.get("phone", ""),
            "company": parsed_data.get("company", "")
        }
        
        logger.info(f"Extracted fields: {fields}")
        return fields
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=503, detail="Failed to connect to OCR service")
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return {"name": "", "email": "", "phone": "", "company": ""}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="OCR processing failed")

# -----------------------------
# Web Interface Routes
# -----------------------------
@app.get("/", response_class=HTMLResponse, tags=["Web Interface"])
async def home(request: Request):
    """Display web interface for business card scanning"""
    return templates.TemplateResponse("form.html", {"request": request})

@app.post("/extract", response_class=JSONResponse, tags=["Web Interface"])
async def extract_card(
    file: Optional[UploadFile] = File(None),
    camera_image: Optional[str] = Form(None)
):
    """
    Extract business card information from uploaded file or camera capture
    Used by the web interface (including auto-capture)
    """
    try:
        image = None
        
        if file:
            logger.info(f"Processing uploaded file: {file.filename}")
            if not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="File must be an image")
            image = Image.open(file.file)
            
        elif camera_image:
            logger.info("Processing camera capture (auto or manual)")
            if "," in camera_image:
                image_data = base64.b64decode(camera_image.split(",")[1])
            else:
                image_data = base64.b64decode(camera_image)
            image = Image.open(io.BytesIO(image_data))
        else:
            raise HTTPException(status_code=400, detail="No image provided")
        
        fields = extract_fields_with_llama(image)
        return JSONResponse({"success": True, "fields": fields})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in extract_card: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@app.post("/save", tags=["Web Interface"])
async def save_card(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    company: str = Form(...)
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
        logger.info(f"Successfully saved card")
        
        return JSONResponse({"success": True, "message": "Business card saved successfully"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving to Supabase: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save: {str(e)}")

# -----------------------------
# REST API Routes
# -----------------------------

@app.get("/api/health", response_model=HealthCheck, tags=["API - System"])
async def api_health_check():
    """
    Check API health status and configuration
    No authentication required
    """
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        supabase_connected=supabase is not None,
        llama_api_configured=headers is not None,
        version="1.0.0"
    )

@app.post("/api/v1/ocr/extract", response_model=OCRResponse, tags=["API - OCR"])
async def api_extract_business_card(
    file: UploadFile = File(..., description="Business card image file"),
    api_key: str = Depends(verify_api_key)
):
    """
    Extract information from a business card image using OCR
    
    **Authentication:** Required (Bearer token)
    
    **Parameters:**
    - file: Image file (JPG, PNG, JPEG)
    
    **Returns:**
    - Extracted fields: name, email, phone, company
    """
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Please upload an image file."
            )
        
        logger.info(f"API: Processing file {file.filename}")
        image = Image.open(file.file)
        fields = extract_fields_with_llama(image)
        
        return OCRResponse(
            success=True,
            fields=fields,
            message="Information extracted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API extraction error: {e}")
        return OCRResponse(
            success=False,
            error=str(e),
            message="Failed to extract information"
        )

@app.post("/api/v1/cards", response_model=APIResponse, status_code=status.HTTP_201_CREATED, tags=["API - Cards"])
async def api_create_card(
    card: BusinessCardCreate,
    api_key: str = Depends(verify_api_key)
):
    """
    Create a new business card entry
    
    **Authentication:** Required (Bearer token)
    
    **Parameters:**
    - name: Full name (required)
    - email: Email address (optional)
    - phone: Phone number (optional)
    - company: Company name (optional)
    """
    try:
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not available")
        
        data = {
            "name": card.name.strip(),
            "email": card.email.strip() if card.email else "",
            "phone": card.phone.strip() if card.phone else "",
            "company": card.company.strip() if card.company else ""
        }
        
        result = supabase.table("business_cards").insert(data).execute()
        
        return APIResponse(
            success=True,
            message="Business card created successfully",
            data={"id": result.data[0]["id"]}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating card: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/cards", response_model=PaginatedResponse, tags=["API - Cards"])
async def api_list_cards(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, email, or company"),
    api_key: str = Depends(verify_api_key)
):
    """
    List all business cards with pagination and search
    
    **Authentication:** Required (Bearer token)
    
    **Parameters:**
    - page: Page number (default: 1)
    - page_size: Items per page (default: 10, max: 100)
    - search: Search term for name, email, or company
    """
    try:
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Build query
        query = supabase.table("business_cards").select("*", count="exact")
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.or_(f"name.ilike.{search_term},email.ilike.{search_term},company.ilike.{search_term}")
        
        # Order and paginate
        query = query.order("created_at", desc=True).range(offset, offset + page_size - 1)
        
        result = query.execute()
        total = result.count if hasattr(result, 'count') else len(result.data)
        
        cards = [
            BusinessCardResponse(
                id=card["id"],
                name=card["name"],
                email=card.get("email"),
                phone=card.get("phone"),
                company=card.get("company"),
                created_at=card["created_at"]
            )
            for card in result.data
        ]
        
        total_pages = (total + page_size - 1) // page_size
        
        return PaginatedResponse(
            success=True,
            data=cards,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing cards: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/cards/{card_id}", response_model=BusinessCardResponse, tags=["API - Cards"])
async def api_get_card(
    card_id: int,
    api_key: str = Depends(verify_api_key)
):
    """
    Get a specific business card by ID
    
    **Authentication:** Required (Bearer token)
    """
    try:
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not available")
        
        result = supabase.table("business_cards").select("*").eq("id", card_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Business card not found")
        
        card = result.data[0]
        return BusinessCardResponse(
            id=card["id"],
            name=card["name"],
            email=card.get("email"),
            phone=card.get("phone"),
            company=card.get("company"),
            created_at=card["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting card: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/cards/{card_id}", response_model=APIResponse, tags=["API - Cards"])
async def api_update_card(
    card_id: int,
    card: BusinessCardCreate,
    api_key: str = Depends(verify_api_key)
):
    """
    Update an existing business card
    
    **Authentication:** Required (Bearer token)
    """
    try:
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not available")
        
        data = {
            "name": card.name.strip(),
            "email": card.email.strip() if card.email else "",
            "phone": card.phone.strip() if card.phone else "",
            "company": card.company.strip() if card.company else ""
        }
        
        result = supabase.table("business_cards").update(data).eq("id", card_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Business card not found")
        
        return APIResponse(
            success=True,
            message="Business card updated successfully",
            data={"id": card_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating card: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/cards/{card_id}", response_model=APIResponse, tags=["API - Cards"])
async def api_delete_card(
    card_id: int,
    api_key: str = Depends(verify_api_key)
):
    """
    Delete a business card
    
    **Authentication:** Required (Bearer token)
    """
    try:
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not available")
        
        result = supabase.table("business_cards").delete().eq("id", card_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Business card not found")
        
        return APIResponse(
            success=True,
            message="Business card deleted successfully",
            data={"id": card_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting card: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ocr/extract-and-save", response_model=APIResponse, status_code=status.HTTP_201_CREATED, tags=["API - OCR"])
async def api_extract_and_save(
    file: UploadFile = File(..., description="Business card image"),
    api_key: str = Depends(verify_api_key)
):
    """
    Extract information from business card and save it in one operation
    
    **Authentication:** Required (Bearer token)
    
    **Parameters:**
    - file: Image file (JPG, PNG, JPEG)
    
    **Returns:**
    - Extracted fields and saved card ID
    """
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Extract
        image = Image.open(file.file)
        fields = extract_fields_with_llama(image)
        
        # Validate minimum requirements
        if not fields.get("name") or not fields.get("name").strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract name from business card"
            )
        
        # Save
        data = {
            "name": fields["name"].strip(),
            "email": fields.get("email", "").strip(),
            "phone": fields.get("phone", "").strip(),
            "company": fields.get("company", "").strip()
        }
        
        result = supabase.table("business_cards").insert(data).execute()
        
        return APIResponse(
            success=True,
            message="Business card extracted and saved successfully",
            data={
                "id": result.data[0]["id"],
                "extracted_fields": fields
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in extract and save: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Legacy health check endpoint
@app.get("/health", tags=["Web Interface"])
async def health_check():
    """Legacy health check endpoint for web interface"""
    return JSONResponse({
        "status": "healthy",
        "supabase_connected": supabase is not None,
        "supabase_url": SUPABASE_URL if SUPABASE_URL else "Not configured",
        "llama_api_configured": headers is not None,
        "llama_api_url": LLAMA_API_URL if LLAMA_API_URL else "Not configured"
    })

# -----------------------------
# Startup Event
# -----------------------------
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 50)
    logger.info("Starting Business Card OCR Application with Auto-Capture API")
    logger.info("=" * 50)
    logger.info(f"Web Interface: http://127.0.0.1:8000/")
    logger.info(f"API Documentation: http://127.0.0.1:8000/api/docs")
    logger.info(f"Supabase: {'Connected' if supabase else 'Not configured'}")
    logger.info(f"Llama API: {'Configured' if headers else 'Not configured'}")
    logger.info(f"API Key: {'Configured' if API_KEY != 'your-secret-api-key-change-this-in-production' else 'USING DEFAULT - CHANGE IN PRODUCTION!'}")
    logger.info("=" * 50)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)