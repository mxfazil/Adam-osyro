# Business Card OCR API Documentation

## Overview
The Business Card OCR API allows you to extract information from business card images using AI-powered OCR and manage business card data programmatically.

**Base URL:** `http://localhost:8000/api/v1`

**Interactive Documentation:** `http://localhost:8000/api/docs`

---

## Authentication

All API endpoints (except `/api/health`) require authentication using an API key.

### Methods

#### 1. Bearer Token (Recommended)
```bash
Authorization: Bearer your-api-key-here
```

#### 2. Custom Header
```bash
X-API-Key: your-api-key-here
```

### Getting Your API Key
1. Set `API_KEY` in your `.env` file
2. Generate a secure key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
3. Default key (development only): `your-secret-api-key-change-this-in-production`

---

## Endpoints

### 1. Health Check
Check API status and configuration.

**Endpoint:** `GET /api/health`  
**Authentication:** Not required

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-05T10:30:00",
  "supabase_connected": true,
  "llama_api_configured": true,
  "version": "1.0.0"
}
```

**Example:**
```bash
curl http://localhost:8000/api/health
```

---

### 2. Extract OCR from Business Card
Extract information from a business card image.

**Endpoint:** `POST /api/v1/ocr/extract`  
**Authentication:** Required  
**Content-Type:** `multipart/form-data`

**Parameters:**
- `file` (required): Image file (JPG, PNG, JPEG)

**Response:**
```json
{
  "success": true,
  "message": "Business card created successfully",
  "data": {
    "id": 123
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/cards \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1 234 567 8900",
    "company": "Acme Corporation"
  }'
```

**Python Example:**
```python
import requests

url = "http://localhost:8000/api/v1/cards"
headers = {
    "Authorization": "Bearer your-api-key-here",
    "Content-Type": "application/json"
}
data = {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1 234 567 8900",
    "company": "Acme Corporation"
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

---

### 4. List Business Cards
Get a paginated list of all business cards with optional search.

**Endpoint:** `GET /api/v1/cards`  
**Authentication:** Required

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 10, max: 100)
- `search` (optional): Search term for name, email, or company

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john.doe@example.com",
      "phone": "+1 234 567 8900",
      "company": "Acme Corporation",
      "created_at": "2025-10-05T10:30:00"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 10,
  "total_pages": 5
}
```

**Examples:**
```bash
# Get first page
curl http://localhost:8000/api/v1/cards \
  -H "Authorization: Bearer your-api-key-here"

# Get page 2 with 20 items
curl "http://localhost:8000/api/v1/cards?page=2&page_size=20" \
  -H "Authorization: Bearer your-api-key-here"

# Search for cards
curl "http://localhost:8000/api/v1/cards?search=Acme" \
  -H "Authorization: Bearer your-api-key-here"
```

---

### 5. Get Single Business Card
Retrieve a specific business card by ID.

**Endpoint:** `GET /api/v1/cards/{card_id}`  
**Authentication:** Required

**Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+1 234 567 8900",
  "company": "Acme Corporation",
  "created_at": "2025-10-05T10:30:00"
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/cards/1 \
  -H "Authorization: Bearer your-api-key-here"
```

---

### 6. Update Business Card
Update an existing business card.

**Endpoint:** `PUT /api/v1/cards/{card_id}`  
**Authentication:** Required  
**Content-Type:** `application/json`

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john.doe@newcompany.com",
  "phone": "+1 234 567 8900",
  "company": "New Company Inc"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Business card updated successfully",
  "data": {
    "id": 1
  }
}
```

**Example:**
```bash
curl -X PUT http://localhost:8000/api/v1/cards/1 \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@newcompany.com",
    "phone": "+1 234 567 8900",
    "company": "New Company Inc"
  }'
```

---

### 7. Delete Business Card
Delete a business card.

**Endpoint:** `DELETE /api/v1/cards/{card_id}`  
**Authentication:** Required

**Response:**
```json
{
  "success": true,
  "message": "Business card deleted successfully",
  "data": {
    "id": 1
  }
}
```

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/v1/cards/1 \
  -H "Authorization: Bearer your-api-key-here"
```

---

### 8. Extract and Save (Combined Operation)
Extract information from a business card image and save it in one operation.

**Endpoint:** `POST /api/v1/ocr/extract-and-save`  
**Authentication:** Required  
**Content-Type:** `multipart/form-data`

**Parameters:**
- `file` (required): Image file (JPG, PNG, JPEG)

**Response:**
```json
{
  "success": true,
  "message": "Business card extracted and saved successfully",
  "data": {
    "id": 123,
    "extracted_fields": {
      "name": "John Doe",
      "email": "john.doe@example.com",
      "phone": "+1 234 567 8900",
      "company": "Acme Corporation"
    }
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/ocr/extract-and-save \
  -H "Authorization: Bearer your-api-key-here" \
  -F "file=@/path/to/business-card.jpg"
```

**Python Example:**
```python
import requests

url = "http://localhost:8000/api/v1/ocr/extract-and-save"
headers = {"Authorization": "Bearer your-api-key-here"}
files = {"file": open("business-card.jpg", "rb")}

response = requests.post(url, headers=headers, files=files)
result = response.json()

print(f"Saved with ID: {result['data']['id']}")
print(f"Extracted: {result['data']['extracted_fields']}")
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid file type. Please upload an image file."
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid API key"
}
```

### 404 Not Found
```json
{
  "detail": "Business card not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "OCR processing failed"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Database not available"
}
```

---

## Rate Limiting

Currently, there are no rate limits on the API. For production deployment, consider implementing rate limiting using:
- FastAPI Rate Limiter
- Nginx rate limiting
- API Gateway (AWS, Azure, etc.)

---

## Integration Examples

### JavaScript/Node.js
```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

// Extract OCR
async function extractBusinessCard(imagePath) {
  const formData = new FormData();
  formData.append('file', fs.createReadStream(imagePath));
  
  const response = await axios.post(
    'http://localhost:8000/api/v1/ocr/extract',
    formData,
    {
      headers: {
        'Authorization': 'Bearer your-api-key-here',
        ...formData.getHeaders()
      }
    }
  );
  
  return response.data;
}

// Create card
async function createCard(data) {
  const response = await axios.post(
    'http://localhost:8000/api/v1/cards',
    data,
    {
      headers: {
        'Authorization': 'Bearer your-api-key-here',
        'Content-Type': 'application/json'
      }
    }
  );
  
  return response.data;
}

// List cards
async function listCards(page = 1, pageSize = 10) {
  const response = await axios.get(
    `http://localhost:8000/api/v1/cards?page=${page}&page_size=${pageSize}`,
    {
      headers: {
        'Authorization': 'Bearer your-api-key-here'
      }
    }
  );
  
  return response.data;
}
```

### Python
```python
import requests

class BusinessCardAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def extract_ocr(self, image_path):
        """Extract information from business card"""
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.base_url}/api/v1/ocr/extract",
                headers=self.headers,
                files=files
            )
        return response.json()
    
    def create_card(self, name, email=None, phone=None, company=None):
        """Create a new business card"""
        data = {
            "name": name,
            "email": email,
            "phone": phone,
            "company": company
        }
        response = requests.post(
            f"{self.base_url}/api/v1/cards",
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def list_cards(self, page=1, page_size=10, search=None):
        """List business cards"""
        params = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        
        response = requests.get(
            f"{self.base_url}/api/v1/cards",
            headers=self.headers,
            params=params
        )
        return response.json()
    
    def get_card(self, card_id):
        """Get a specific card"""
        response = requests.get(
            f"{self.base_url}/api/v1/cards/{card_id}",
            headers=self.headers
        )
        return response.json()
    
    def update_card(self, card_id, name, email=None, phone=None, company=None):
        """Update a card"""
        data = {
            "name": name,
            "email": email,
            "phone": phone,
            "company": company
        }
        response = requests.put(
            f"{self.base_url}/api/v1/cards/{card_id}",
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def delete_card(self, card_id):
        """Delete a card"""
        response = requests.delete(
            f"{self.base_url}/api/v1/cards/{card_id}",
            headers=self.headers
        )
        return response.json()
    
    def extract_and_save(self, image_path):
        """Extract and save in one operation"""
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.base_url}/api/v1/ocr/extract-and-save",
                headers=self.headers,
                files=files
            )
        return response.json()

# Usage
api = BusinessCardAPI("http://localhost:8000", "your-api-key-here")

# Extract and save
result = api.extract_and_save("business-card.jpg")
print(f"Card saved with ID: {result['data']['id']}")

# List all cards
cards = api.list_cards(page=1, page_size=20)
print(f"Total cards: {cards['total']}")

# Search cards
results = api.list_cards(search="Acme")
print(f"Found {len(results['data'])} cards")
```

### cURL Examples
```bash
# Health check
curl http://localhost:8000/api/health

# Extract OCR
curl -X POST http://localhost:8000/api/v1/ocr/extract \
  -H "Authorization: Bearer your-api-key-here" \
  -F "file=@business-card.jpg"

# Create card
curl -X POST http://localhost:8000/api/v1/cards \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'

# List cards
curl http://localhost:8000/api/v1/cards?page=1&page_size=10 \
  -H "Authorization: Bearer your-api-key-here"

# Get card
curl http://localhost:8000/api/v1/cards/1 \
  -H "Authorization: Bearer your-api-key-here"

# Update card
curl -X PUT http://localhost:8000/api/v1/cards/1 \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Doe","email":"jane@example.com"}'

# Delete card
curl -X DELETE http://localhost:8000/api/v1/cards/1 \
  -H "Authorization: Bearer your-api-key-here"

# Extract and save
curl -X POST http://localhost:8000/api/v1/ocr/extract-and-save \
  -H "Authorization: Bearer your-api-key-here" \
  -F "file=@business-card.jpg"
```

---

## Best Practices

### 1. Security
- **Never hardcode API keys** in your application
- Store API keys in environment variables
- Use HTTPS in production
- Rotate API keys regularly
- Implement rate limiting

### 2. Error Handling
```python
try:
    response = api.extract_ocr("card.jpg")
    if response['success']:
        print(response['fields'])
    else:
        print(f"Error: {response.get('error')}")
except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")
```

### 3. Pagination
Always handle pagination for large datasets:
```python
def get_all_cards(api):
    all_cards = []
    page = 1
    while True:
        result = api.list_cards(page=page, page_size=100)
        all_cards.extend(result['data'])
        if page >= result['total_pages']:
            break
        page += 1
    return all_cards
```

### 4. Image Quality
- Use clear, well-lit images
- Minimum resolution: 800x600
- Supported formats: JPG, PNG, JPEG
- Maximum file size: 10MB (recommended)

---

## Testing

### Using Interactive Documentation
1. Start the server: `python ocr.py`
2. Visit: http://localhost:8000/api/docs
3. Click "Authorize" and enter your API key
4. Test endpoints directly in the browser

### Using Postman
1. Import the API endpoints
2. Set Authorization header: `Bearer your-api-key-here`
3. Test each endpoint

### Unit Tests
```python
import pytest
from fastapi.testclient import TestClient
from ocr import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_card():
    headers = {"Authorization": "Bearer your-api-key-here"}
    data = {
        "name": "Test User",
        "email": "test@example.com"
    }
    response = client.post("/api/v1/cards", json=data, headers=headers)
    assert response.status_code == 201
    assert response.json()["success"] == True
```

---

## Deployment

### Environment Variables
```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
LLAMA_API_URL=https://your-llama-endpoint
LLAMA_API_KEY=your-llama-key
API_KEY=your-secure-random-key

# Optional
LLAMA_DEPLOYMENT_NAME=Llama-3.2-11B-Vision-Instruct
```

### Production Checklist
- [ ] Change default API key to secure random string
- [ ] Enable HTTPS
- [ ] Configure CORS for specific origins
- [ ] Implement rate limiting
- [ ] Set up logging and monitoring
- [ ] Enable database backups
- [ ] Configure firewall rules
- [ ] Set up health check monitoring
- [ ] Document API versioning strategy

---

## Support

For issues or questions:
1. Check the interactive documentation: http://localhost:8000/api/docs
2. Review the logs for error messages
3. Test with the `/api/health` endpoint
4. Verify API key configuration

## Changelog

### Version 1.0.0 (2025-10-05)
- Initial API release
- OCR extraction endpoint
- CRUD operations for business cards
- Pagination and search
- Combined extract-and-save operation
- Bearer token authentication
- Interactive API documentation
  "fields": {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1 234 567 8900",
    "company": "Acme Corporation"
  },
  "message": "Information extracted successfully"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/ocr/extract \
  -H "Authorization: Bearer your-api-key-here" \
  -F "file=@/path/to/business-card.jpg"
```

**Python Example:**
```python
import requests

url = "http://localhost:8000/api/v1/ocr/extract"
headers = {"Authorization": "Bearer your-api-key-here"}
files = {"file": open("business-card.jpg", "rb")}

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

---

### 3. Create Business Card
Manually create a business card entry.

**Endpoint:** `POST /api/v1/cards`  
**Authentication:** Required  
**Content-Type:** `application/json`

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+1 234 567 8900",
  "company": "Acme Corporation"
}
```

**Response:**
```json
{
  "success": true,