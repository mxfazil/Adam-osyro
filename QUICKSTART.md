# Quick Start Guide - Business Card OCR API

## 🎯 Goal
Integrate the Business Card OCR API into your main application in 5 minutes.

## ⚡ 5-Minute Setup

### 1. Start the API Server (2 min)

```bash
# In your business-card-ocr directory
python ocr.py
```

Server runs at: `http://localhost:8000`

### 2. Get Your API Key (1 min)

Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add to your `.env` file:
```env
API_KEY=your-generated-key-here
```

Restart the server.

### 3. Test the API (1 min)

```bash
# Health check
curl http://localhost:8000/api/health

# Extract OCR (replace with your key and image)
curl -X POST http://localhost:8000/api/v1/ocr/extract \
  -H "Authorization: Bearer your-api-key" \
  -F "file=@business-card.jpg"
```

### 4. Integrate into Your App (1 min)

**Python:**
```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "your-api-key"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Extract and save
with open("card.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post(
        f"{API_URL}/api/v1/ocr/extract-and-save",
        files=files,
        headers=headers
    )
    result = response.json()
    print(f"Saved! ID: {result['data']['id']}")
```

**JavaScript/Node.js:**
```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const API_URL = 'http://localhost:8000';
const API_KEY = 'your-api-key';

async function extractAndSave(imagePath) {
    const formData = new FormData();
    formData.append('file', fs.createReadStream(imagePath));
    
    const response = await axios.post(
        `${API_URL}/api/v1/ocr/extract-and-save`,
        formData,
        {
            headers: {
                'Authorization': `Bearer ${API_KEY}`,
                ...formData.getHeaders()
            }
        }
    );
    
    console.log('Saved! ID:', response.data.data.id);
}

extractAndSave('card.jpg');
```

---

## 🔧 Common Integration Patterns

### Pattern 1: Extract Only (Review Before Save)

```python
# 1. Extract information
response = requests.post(
    f"{API_URL}/api/v1/ocr/extract",
    files={"file": open("card.jpg", "rb")},
    headers=headers
)
fields = response.json()['fields']

# 2. Show to user for confirmation
print(f"Name: {fields['name']}")
print(f"Email: {fields['email']}")
user_confirmed = input("Save? (y/n): ")

# 3. Save if confirmed
if user_confirmed == 'y':
    requests.post(
        f"{API_URL}/api/v1/cards",
        json=fields,
        headers=headers
    )
```

### Pattern 2: Extract and Save Immediately

```python
# One-step operation
response = requests.post(
    f"{API_URL}/api/v1/ocr/extract-and-save",
    files={"file": open("card.jpg", "rb")},
    headers=headers
)
card_id = response.json()['data']['id']
```

### Pattern 3: Batch Processing

```python
import os

# Process multiple cards
card_dir = "cards/"
for filename in os.listdir(card_dir):
    if filename.endswith(('.jpg', '.png', '.jpeg')):
        filepath = os.path.join(card_dir, filename)
        
        with open(filepath, 'rb') as f:
            try:
                response = requests.post(
                    f"{API_URL}/api/v1/ocr/extract-and-save",
                    files={"file": f},
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 201:
                    print(f"✓ {filename}: Saved")
                else:
                    print(f"✗ {filename}: Failed")
            except Exception as e:
                print(f"✗ {filename}: Error - {e}")
```

### Pattern 4: Search and Retrieve

```python
# Search for cards
response = requests.get(
    f"{API_URL}/api/v1/cards",
    params={"search": "Acme", "page_size": 50},
    headers=headers
)

cards = response.json()['data']
for card in cards:
    print(f"{card['name']} at {card['company']}")
```

---

## 🎨 Using the Python Client Library

### Installation

Copy `client.py` to your project:
```bash
cp client.py /path/to/your/project/
```

### Usage

```python
from client import BusinessCardClient

# Initialize
client = BusinessCardClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# Extract and save
result = client.extract_and_save("card.jpg")
print(f"Card ID: {result['id']}")

# List all cards
cards = client.get_all_cards()
print(f"Total: {len(cards)} cards")

# Search
results = client.list_cards(search="Acme", page_size=10)

# Update
client.update_card(
    card_id=123,
    name="John Doe",
    email="john@newcompany.com"
)

# Delete
client.delete_card(123)
```

### Error Handling

```python
from client import BusinessCardClient, BusinessCardAPIError

client = BusinessCardClient("http://localhost:8000", "your-api-key")

try:
    result = client.extract_and_save("card.jpg")
    print(f"Success! ID: {result['id']}")
except FileNotFoundError:
    print("Image file not found")
except BusinessCardAPIError as e:
    print(f"API Error: {e}")
```

---

## 🌐 Integration Examples

### Flask Application

```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

OCR_API_URL = "http://localhost:8000"
OCR_API_KEY = "your-api-key"

@app.route('/upload-card', methods=['POST'])
def upload_card():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Forward to OCR API
    files = {'file': (file.filename, file.stream, file.content_type)}
    headers = {'Authorization': f'Bearer {OCR_API_KEY}'}
    
    response = requests.post(
        f'{OCR_API_URL}/api/v1/ocr/extract-and-save',
        files=files,
        headers=headers
    )
    
    return jsonify(response.json()), response.status_code

if __name__ == '__main__':
    app.run(port=5000)
```

### Django View

```python
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests

OCR_API_URL = "http://localhost:8000"
OCR_API_KEY = "your-api-key"

@csrf_exempt
def upload_business_card(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    file = request.FILES['file']
    
    # Send to OCR API
    files = {'file': (file.name, file.read(), file.content_type)}
    headers = {'Authorization': f'Bearer {OCR_API_KEY}'}
    
    response = requests.post(
        f'{OCR_API_URL}/api/v1/ocr/extract-and-save',
        files=files,
        headers=headers
    )
    
    return JsonResponse(response.json(), status=response.status_code)
```

### FastAPI Service

```python
from fastapi import FastAPI, UploadFile, File
import requests

app = FastAPI()

OCR_API_URL = "http://localhost:8000"
OCR_API_KEY = "your-api-key"

@app.post("/scan-card")
async def scan_card(file: UploadFile = File(...)):
    # Forward to OCR API
    files = {'file': (file.filename, await file.read(), file.content_type)}
    headers = {'Authorization': f'Bearer {OCR_API_KEY}'}
    
    response = requests.post(
        f'{OCR_API_URL}/api/v1/ocr/extract-and-save',
        files=files,
        headers=headers
    )
    
    return response.json()
```

### React Frontend

```javascript
import React, { useState } from 'react';
import axios from 'axios';

const OCR_API_URL = 'http://localhost:8000';
const OCR_API_KEY = 'your-api-key';

function BusinessCardUpload() {
    const [file, setFile] = useState(null);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file) return;

        setLoading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post(
                `${OCR_API_URL}/api/v1/ocr/extract-and-save`,
                formData,
                {
                    headers: {
                        'Authorization': `Bearer ${OCR_API_KEY}`,
                        'Content-Type': 'multipart/form-data'
                    }
                }
            );
            
            setResult(response.data);
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to process card');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <form onSubmit={handleSubmit}>
                <input type="file" onChange={handleFileChange} accept="image/*" />
                <button type="submit" disabled={!file || loading}>
                    {loading ? 'Processing...' : 'Upload'}
                </button>
            </form>
            
            {result && (
                <div>
                    <h3>Card Saved! ID: {result.data.id}</h3>
                    <p>Name: {result.data.extracted_fields.name}</p>
                    <p>Email: {result.data.extracted_fields.email}</p>
                </div>
            )}
        </div>
    );
}

export default BusinessCardUpload;
```

---

## 🔐 Security Best Practices

### 1. Environment Variables

Never hardcode API keys:

```python
import os

# Good ✓
API_KEY = os.getenv('OCR_API_KEY')

# Bad ✗
API_KEY = "your-api-key-here"
```

### 2. HTTPS in Production

Always use HTTPS:
```python
# Production
API_URL = "https://your-domain.com"

# Development only
API_URL = "http://localhost:8000"
```

### 3. Rate Limiting

Implement client-side rate limiting:
```python
import time
from functools import wraps

def rate_limit(calls_per_minute=60):
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

@rate_limit(calls_per_minute=30)
def process_card(image_path):
    # Your API call here
    pass
```

### 4. Error Handling

Always handle errors gracefully:
```python
import requests
from requests.exceptions import RequestException

def safe_api_call(url, **kwargs):
    try:
        response = requests.post(url, timeout=30, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print("Request timed out")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e.response.status_code}")
    except RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    return None
```

---

## 📊 Monitoring Integration

### Health Check Endpoint

Add to your monitoring system:
```python
import requests
import time

def monitor_ocr_api():
    try:
        response = requests.get(
            "http://localhost:8000/api/health",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API is healthy")
            print(f"  Supabase: {data['supabase_connected']}")
            print(f"  Llama API: {data['llama_api_configured']}")
            return True
        else:
            print(f"✗ API returned {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ API is down: {e}")
        return False

# Run every 5 minutes
while True:
    monitor_ocr_api()
    time.sleep(300)
```

### Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_card_with_logging(image_path):
    logger.info(f"Processing card: {image_path}")
    
    try:
        response = requests.post(...)
        logger.info(f"Success! Card ID: {response.json()['data']['id']}")
        return response.json()
    except Exception as e:
        logger.error(f"Failed to process {image_path}: {e}")
        return None
```

---

## 🚀 Performance Tips

### 1. Connection Pooling

```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import requests

session = requests.Session()

# Retry configuration
retry = Retry(
    total=3,
    backoff_factor=0.3,
    status_forcelist=[500, 502, 503, 504]
)

adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
session.mount('http://', adapter)
session.mount('https://', adapter)

# Use session for all requests
response = session.post(url, headers=headers, files=files)
```

### 2. Async Processing

```python
import asyncio
import aiohttp

async def process_card_async(session, image_path):
    with open(image_path, 'rb') as f:
        data = aiohttp.FormData()
        data.add_field('file', f, filename=image_path)
        
        async with session.post(
            f'{API_URL}/api/v1/ocr/extract-and-save',
            data=data,
            headers={'Authorization': f'Bearer {API_KEY}'}
        ) as response:
            return await response.json()

async def process_multiple_cards(image_paths):
    async with aiohttp.ClientSession() as session:
        tasks = [process_card_async(session, path) for path in image_paths]
        return await asyncio.gather(*tasks)

# Usage
image_paths = ['card1.jpg', 'card2.jpg', 'card3.jpg']
results = asyncio.run(process_multiple_cards(image_paths))
```

---

## ❓ FAQ

**Q: Can I run multiple instances?**
A: Yes! Just use different ports and configure load balancing.

**Q: How do I deploy to production?**
A: See the Deployment section in README.md. Use a reverse proxy (Nginx) with HTTPS.

**Q: What's the rate limit?**
A: No built-in limit currently. Implement your own or use an API gateway.

**Q: Can I use this with mobile apps?**
A: Yes! The API works with any HTTP client (iOS, Android, React Native, Flutter).

**Q: How accurate is the OCR?**
A: Depends on image quality. Best with clear, well-lit images.

**Q: Can I customize the extracted fields?**
A: Yes! Modify the Llama prompt in `ocr.py` to extract additional fields.

---

## 📚 Next Steps

1. **Explore API Docs**: Visit `http://localhost:8000/api/docs`
2. **Read Full Documentation**: See `API_DOCUMENTATION.md`
3. **Run Tests**: `pytest test_api.py -v`
4. **Customize**: Modify `ocr.py` for your needs
5. **Deploy**: Follow the production checklist

## 🆘 Need Help?

- Check `/api/docs` for interactive testing
- Review logs with `python ocr.py` (verbose mode)
- Test health: `curl http://localhost:8000/api/health`
- See `README.md` for troubleshooting

---

**Happy Integrating! 🎉**