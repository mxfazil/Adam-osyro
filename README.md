# Business Card OCR Scanner with REST API

A FastAPI-based application that extracts information from business cards using Llama Vision AI, with both a web interface and a comprehensive REST API for integration into your applications.

## 🌟 Features

### Web Interface
- ✏️ **Manual entry** - Fill in business card details manually
- 📤 **Upload images** - Upload business card images from your device
- 📷 **Camera capture** - Capture photos directly using your webcam
- 🤖 **AI-powered OCR** - Using Llama 3.2 Vision model
- ✨ **Auto-fill form** - OCR automatically fills the form fields
- ✏️ **Review and edit** - Edit extracted information before saving
- 💾 **Database storage** - Store data in Supabase
- 🎨 **Modern UI** - Intuitive interface with drag & drop support

### REST API
- 🔐 **Authentication** - Secure API key authentication
- 📊 **Full CRUD** - Create, Read, Update, Delete operations
- 🔍 **Search & Filter** - Search cards by name, email, or company
- 📄 **Pagination** - Efficient data retrieval with pagination
- 🤖 **OCR Endpoint** - Extract information programmatically
- ⚡ **Combined Operations** - Extract and save in one API call
- 📚 **Interactive Docs** - Swagger UI for API exploration
- 🔄 **RESTful** - Standard REST API design

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Web Interface](#web-interface)
  - [REST API](#rest-api)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

```bash
# Clone repository
git clone <your-repo>
cd business-card-ocr

# Install dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run application
python ocr.py

# Access
# Web Interface: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

## 📦 Installation

### Prerequisites
- Python 3.8+
- Supabase account and project
- Llama API access (or compatible vision API)
- Tavily API key for web scraping

### Step-by-Step

1. **Clone the repository**
   ```bash
   git clone <your-repo>
   cd business-card-ocr
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your credentials:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-service-role-key
   LLAMA_API_URL=https://your-llama-api-endpoint
   LLAMA_API_KEY=your-llama-api-key
   API_KEY=your-secure-api-key-here
   TAVILY_API_KEY=your-tavily-api-key-for-web-scraping
   GEMINI_API_KEY=your-gemini-api-key-for-chatbot
   ```

5. **Create Supabase tables**
   
   The `business_cards` table should already exist. Run this SQL in your Supabase SQL editor to create the web-scraped data table:
   ```sql
   CREATE TABLE web_scraped_data (
       id BIGSERIAL PRIMARY KEY,
       name TEXT NOT NULL,
       company TEXT,
       web_info JSONB,
       created_at TIMESTAMPTZ DEFAULT NOW()
   );
   
   -- Create indexes for faster searches
   CREATE INDEX idx_web_scraped_name ON web_scraped_data (name);
   CREATE INDEX idx_web_scraped_company ON web_scraped_data (company);
   ```

6. **Create templates directory**
   ```bash
   mkdir templates
   ```
   Place `form.html` in the `templates/` directory.

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Your Supabase project URL | Yes |
| `SUPABASE_KEY` | Supabase service role key | Yes |
| `LLAMA_API_URL` | Llama API endpoint | Yes |
| `LLAMA_API_KEY` | Llama API key | Yes |
| `API_KEY` | API authentication key | Yes |
| `TAVILY_API_KEY` | Tavily API key for web scraping | Yes |
| `GEMINI_API_KEY` | Google Gemini API key for chatbot | Yes |
| `LLAMA_DEPLOYMENT_NAME` | Model deployment name | No |

### Generate Secure API Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 📖 Usage

### Web Interface

1. **Start the server**
   ```bash
   python streamlined_app.py
   ```

2. **Access the interface**
   
   Open your browser: `http://localhost:8000`

3. **Three ways to add cards:**
   
   **Option A: Manual Entry**
   - Fill in the form fields manually
   - Click "Save Card" to save just the business card
   - Click "Save Web Info" to save just the web-scraped information
   - Click "Save All" to save both the business card and web information
   - Click "Continue to AI Chat" to proceed to the chat interface
   
   **Option B: Upload Image**
   - Click "Upload Image" tab
   - Upload or drag & drop an image
   - Review and edit extracted data
   - Click "Save Card" to save just the business card
   - Click "Save Web Info" to save just the web-scraped information
   - Click "Save All" to save both the business card and web information
   - Click "Continue to AI Chat" to proceed to the chat interface
   
   **Option C: Camera Capture**
   - Click "Use Camera" tab
   - Click "Start Camera"
   - Position card and click "Capture"
   - Review and edit extracted data
   - Click "Save Card" to save just the business card
   - Click "Save Web Info" to save just the web-scraped information
   - Click "Save All" to save both the business card and web information
   - Click "Continue to AI Chat" to proceed to the chat interface

### REST API

#### Quick Start

```python
import requests

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Extract OCR
with open("business-card.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post(
        f"{BASE_URL}/api/v1/ocr/extract",
        files=files,
        headers=headers
    )
    print(response.json())

# Create card
data = {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "company": "Acme Corp"
}
response = requests.post(
    f"{BASE_URL}/api/v1/cards",
    json=data,
    headers=headers
)
print(response.json())

# List cards
response = requests.get(
    f"{BASE_URL}/api/v1/cards?page=1&page_size=10",
    headers=headers
)
print(response.json())
```

#### Using the Python Client

```python
from client import BusinessCardClient

# Initialize client
client = BusinessCardClient(
    base_url="http://localhost:8000",
    api_key="your-api-key-here"
)

# Extract and save in one operation
result = client.extract_and_save("business-card.jpg")
print(f"Saved with ID: {result['id']}")

# List cards
cards = client.list_cards(page=1, page_size=20)
print(f"Total: {cards['total']} cards")

# Search
results = client.list_cards(search="Acme")
for card in results['data']:
    print(f"{card['name']} - {card['company']}")
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
All endpoints (except `/api/health`) require authentication:

```bash
Authorization: Bearer your-api-key-here
```

### Main Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check (no auth) |
| `POST` | `/api/v1/ocr/extract` | Extract OCR from image |
| `POST` | `/api/v1/cards` | Create new card |
| `GET` | `/api/v1/cards` | List cards (paginated) |
| `GET` | `/api/v1/cards/{id}` | Get specific card |
| `PUT` | `/api/v1/cards/{id}` | Update card |
| `DELETE` | `/api/v1/cards/{id}` | Delete card |
| `POST` | `/api/v1/ocr/extract-and-save` | Extract & save |

### Interactive Documentation

Visit these URLs when the server is running:

- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`

### Examples

**Extract OCR**
```bash
curl -X POST http://localhost:8000/api/v1/ocr/extract \
  -H "Authorization: Bearer your-api-key" \
  -F "file=@card.jpg"
```

**Create Card**
```bash
curl -X POST http://localhost:8000/api/v1/cards \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com"}'
```

**List Cards**
```bash
curl "http://localhost:8000/api/v1/cards?page=1&page_size=10" \
  -H "Authorization: Bearer your-api-key"
```

For complete API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## 🧪 Testing

### Run Tests

```bash
# Install pytest
pip install pytest pytest-cov

# Run all tests
pytest test_api.py -v

# Run with coverage
pytest test_api.py --cov=ocr --cov-report=html

# Run specific test class
pytest test_api.py::TestCardCRUD -v

# Run specific test
pytest test_api.py::TestCardCRUD::test_create_card -v
```

### Manual Testing

Use the interactive API documentation:
1. Start server: `python ocr.py`
2. Visit: `http://localhost:8000/api/docs`
3. Click "Authorize" and enter your API key
4. Test endpoints directly in the browser

## 🚀 Deployment

### Production Checklist

- [ ] Change `API_KEY` to a secure random string
- [ ] Enable HTTPS (use reverse proxy like Nginx)
- [ ] Configure CORS for specific origins only
- [ ] Implement rate limiting
- [ ] Set up logging and monitoring
- [ ] Enable database backups
- [ ] Configure firewall rules
- [ ] Set up health check monitoring
- [ ] Use environment-specific configs

### Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "ocr:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build
docker build -t business-card-ocr .

# Run
docker run -p 8000:8000 --env-file .env business-card-ocr
```

## 🔧 Troubleshooting

### Common Issues

**1. API Key Authentication Failed**
```
Solution: Check that API_KEY in .env matches the key you're using
```

**2. Supabase Connection Error**
```
Solution: Verify SUPABASE_URL and SUPABASE_KEY are correct
Check Supabase dashboard for project status
```

**3. OCR Extraction Failed**
```
Solution: Verify LLAMA_API_URL and LLAMA_API_KEY
Check image quality and format
Review logs for specific error messages
```

**4. Camera Not Working**
```
Solution: Check browser permissions
Use HTTPS in production (required for camera)
Try different browser
```

**5. Import Errors**
```
Solution: Ensure all dependencies are installed:
pip install -r requirements.txt
```

### Debug Mode

Enable detailed logging:
```python
# In ocr.py, change logging level
logging.basicConfig(level=logging.DEBUG)
```

### Health Check

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "supabase_connected": true,
  "llama_api_configured": true,
  "version": "1.0.0"
}
```

## 📁 Project Structure

```
business-card-ocr/
├── ocr.py                  # Main application (Web + API)
├── client.py               # Python client library
├── test_api.py             # API tests
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── .env                   # Your environment (not in git)
├── .gitignore            # Git ignore rules
├── README.md             # This file
├── API_DOCUMENTATION.md  # Detailed API docs
└── templates/
    └── form.html         # Web interface
```

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

MIT License - Feel free to use and modify as needed.

## 🆘 Support

- **Documentation**: Check `/api/docs` when server is running
- **Issues**: Create an issue on GitHub
- **API Help**: See `API_DOCUMENTATION.md`
- **Tests**: Run `pytest test_api.py -v`

## 🎯 Roadmap

- [x] Web interface
- [x] OCR extraction
- [x] REST API
- [x] Authentication
- [x] Pagination
- [x] Search functionality
- [ ] Rate limiting
- [ ] Batch upload
- [ ] Export to CSV/vCard
- [ ] Duplicate detection
- [ ] Multi-language support
- [ ] Analytics dashboard
- [ ] Webhooks
- [ ] GraphQL API

## 📊 Version History

### v1.0.0 (2025-10-05)
- Initial release
- Web interface with manual entry, upload, and camera
- Full REST API with CRUD operations
- OCR extraction with Llama Vision
- Supabase integration
- API authentication
- Interactive documentation
- Python client library
- Comprehensive tests

---

**Made with ❤️ using FastAPI, Llama Vision, and Supabase**