import requests
import json
import base64
import io
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Form, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from supabase import create_client, Client
from PIL import Image
import logging
from typing import Optional

# Load environment variables
load_dotenv()

# -----------------------------
# Logging setup
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------
# Supabase setup
# -----------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

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

# -----------------------------
# Llama API setup
# -----------------------------
LLAMA_API_URL = os.getenv("LLAMA_API_URL")
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
LLAMA_DEPLOYMENT_NAME = os.getenv("LLAMA_DEPLOYMENT_NAME", "Llama-3.2-11B-Vision-Instruct")

if not LLAMA_API_URL or not LLAMA_API_KEY:
    logger.error("Llama API credentials not found in environment variables")
else:
    headers = {
        "Authorization": f"Bearer {LLAMA_API_KEY}",
        "Content-Type": "application/json"
    }

# -----------------------------
# FastAPI setup
# -----------------------------
app = FastAPI(title="Business Card OCR", version="1.0.0")
templates = Jinja2Templates(directory="templates")

# -----------------------------
# Helper Functions
# -----------------------------
def encode_image(image: Image.Image, max_size: tuple = (1024, 1024)) -> str:
    """
    Encode image to base64 with optional resizing for API efficiency
    """
    try:
        # Resize if image is too large
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            logger.info(f"Image resized to {image.size}")
        
        buffer = io.BytesIO()
        # Convert RGBA to RGB if necessary
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        image.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        logger.error(f"Error encoding image: {e}")
        raise HTTPException(status_code=400, detail="Failed to process image")

def extract_fields_with_llama(image: Image.Image) -> dict:
    """
    Extract business card fields using Llama Vision API
    """
    try:
        b64_img = encode_image(image)
        
        # Prepare messages
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
        
        # Base payload
        payload = {
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 500
        }
        
        # Adjust for Azure OpenAI format if needed
        if "azure.com" in LLAMA_API_URL:
            # Azure OpenAI might require the model/deployment name in the payload
            payload["model"] = LLAMA_DEPLOYMENT_NAME
        else:
            # Standard OpenAI format
            payload["model"] = "Llama-3.2-11B-Vision-Instruct"
        
        logger.info("Sending request to Llama API...")
        logger.info(f"API URL: {LLAMA_API_URL}")
        logger.info(f"Using model/deployment: {payload['model']}")
        
        response = requests.post(
            LLAMA_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Log the full request for debugging
        logger.info(f"Request headers: {headers}")
        logger.info(f"Request payload: {payload}")
        
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        logger.info(f"Raw API response: {content}")
        
        # Try to parse JSON from the response
        # Sometimes the model wraps JSON in code blocks
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        parsed_data = json.loads(content)
        
        # Ensure all expected fields exist
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
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response headers: {e.response.headers}")
            logger.error(f"Response content: {e.response.text}")
        raise HTTPException(status_code=503, detail="Failed to connect to OCR service")
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}, Content: {content}")
        # Return empty fields if parsing fails
        return {"name": "", "email": "", "phone": "", "company": ""}
    except Exception as e:
        logger.error(f"Unexpected error in extract_fields_with_llama: {e}")
        raise HTTPException(status_code=500, detail="OCR processing failed")

# -----------------------------
# Routes
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Display upload/capture page"""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/extract", response_class=HTMLResponse)
async def extract_card(
    request: Request,
    file: Optional[UploadFile] = File(None),
    camera_image: Optional[str] = Form(None)
):
    """
    Extract business card information from uploaded file or camera capture
    """
    try:
        image = None
        
        if file:
            logger.info(f"Processing uploaded file: {file.filename}")
            # Validate file type
            if not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="File must be an image")
            
            image = Image.open(file.file)
            
        elif camera_image:
            logger.info("Processing camera capture")
            # Remove data URL prefix if present
            if "," in camera_image:
                image_data = base64.b64decode(camera_image.split(",")[1])
            else:
                image_data = base64.b64decode(camera_image)
            image = Image.open(io.BytesIO(image_data))
        else:
            raise HTTPException(status_code=400, detail="No image provided")
        
        # Extract fields using Llama
        fields = extract_fields_with_llama(image)
        
        return templates.TemplateResponse(
            "form.html",
            {"request": request, "fields": fields}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in extract_card: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/save")
async def save_card(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    company: str = Form(...)
):
    """
    Save confirmed business card data to Supabase
    """
    try:
        if not supabase:
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        # Basic validation
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
        logger.info(f"Successfully saved card: {result}")
        
        return RedirectResponse("/?success=true", status_code=303)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving to Supabase: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "supabase_connected": supabase is not None,
        "supabase_url": SUPABASE_URL if SUPABASE_URL else "Not configured",
        "llama_api_configured": LLAMA_API_URL is not None and LLAMA_API_KEY is not None,
        "llama_api_url": LLAMA_API_URL if LLAMA_API_URL else "Not configured"
    })

# -----------------------------
# Startup Event
# -----------------------------
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Business Card OCR application...")
    logger.info(f"Supabase URL configured: {SUPABASE_URL is not None}")
    logger.info(f"Llama API URL configured: {LLAMA_API_URL is not None}")
    if SUPABASE_URL:
        logger.info(f"Supabase URL: {SUPABASE_URL}")
    if LLAMA_API_URL:
        logger.info(f"Llama API URL: {LLAMA_API_URL}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
