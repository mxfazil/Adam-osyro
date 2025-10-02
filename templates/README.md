# Business Card OCR Scanner

A FastAPI-based application that extracts information from business cards using Llama Vision AI, allows user confirmation, and stores the results in Supabase.

## Features

- 📤 **Upload business card images** from your device
- 📷 **Capture photos directly** using your webcam
- 🤖 **AI-powered OCR** using Llama 3.2 Vision model
- ✏️ **Review and edit** extracted information before saving
- 💾 **Store data** in Supabase database
- ✨ **Simple, clean UI** for easy testing

## Architecture

### Components

1. **Backend (FastAPI)**
   - Handles image uploads and camera captures
   - Processes images with Llama Vision API
   - Manages Supabase database operations
   - Provides templated HTML responses

2. **Frontend**
   - `upload.html` - Upload/capture interface
   - `form.html` - Confirmation form for extracted data

3. **External Services**
   - **Llama API** - Vision model for OCR
   - **Supabase** - PostgreSQL database for storage

## Prerequisites

- Python 3.8+
- Supabase account and project
- Llama API access (or compatible vision API endpoint)

## Installation

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
   - `SUPABASE_URL` - Your Supabase project URL
   - `SUPABASE_KEY` - Your Supabase service role key
   - `LLAMA_API_URL` - Your Llama API endpoint
   - `LLAMA_API_KEY` - Your Llama API key

5. **Create Supabase table**
   
   Run this SQL in your Supabase SQL editor:
   ```sql
   CREATE TABLE business_cards (
       id BIGSERIAL PRIMARY KEY,
       name TEXT NOT NULL,
       email TEXT,
       phone TEXT,
       company TEXT,
       created_at TIMESTAMPTZ DEFAULT NOW()
   );
   ```

6. **Create templates directory**
   ```bash
   mkdir templates
   ```
   
   Place `upload.html` and `form.html` in the `templates/` directory.

## Usage

1. **Start the server**
   ```bash
   python adamocr.py
   ```
   
   Or with uvicorn:
   ```bash
   uvicorn adamocr:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Access the application**
   
   Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

3. **Scan a business card**
   - **Option A**: Click "Choose File" and upload an image
   - **Option B**: Click "Start Camera" and capture a photo

4. **Review and save**
   - Review the extracted information
   - Edit any incorrect fields
   - Click "Save to Database"

## API Endpoints

- `GET /` - Home page (upload/capture interface)
- `POST /extract` - Process image and extract data
- `POST /save` - Save confirmed data to Supabase
- `GET /health` - Health check endpoint

## Project Structure

```
business-card-ocr/
├── adamocr.py           # Main FastAPI application
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── .env                # Your environment variables (not in git)
├── README.md           # This file
└── templates/
    ├── upload.html     # Upload/capture page
    └── form.html       # Confirmation form
```

## Enhancements Made

### Backend (`adamocr.py`)
- ✅ Environment variable support for configuration
- ✅ Comprehensive error handling and logging
- ✅ Image optimization (resize, format conversion)
- ✅ Better JSON parsing from LLM responses
- ✅ Request timeout handling
- ✅ Input validation
- ✅ Health check endpoint
- ✅ Detailed logging for debugging

### Frontend (`upload.html`)
- ✅ Modern, clean UI design
- ✅ Camera start/stop functionality
- ✅ Loading indicators
- ✅ Success/error messages
- ✅ Mobile-responsive design
- ✅ Better camera controls
- ✅ File input validation

### Frontend (`form.html`)
- ✅ Field validation (client-side)
- ✅ Empty field highlighting
- ✅ Real-time validation feedback
- ✅ Auto-focus on first empty field
- ✅ Email format validation
- ✅ Loading overlay during save
- ✅ Cancel button to go back

## Troubleshooting

### Camera not working
- Check browser permissions for camera access
- Use HTTPS in production (required for camera access)
- Try a different browser

### OCR extraction issues
- Ensure image is clear and well-lit
- Check Llama API credentials
- Review logs for API errors

### Database connection errors
- Verify Supabase credentials in `.env`
- Check table exists with correct schema
- Review Supabase logs

## Security Notes

⚠️ **Important**: Never commit your `.env` file to version control!

- Use service role key only on server-side
- Consider using anon key + RLS policies for production
- Implement authentication before deploying
- Add rate limiting for production use

## Future Enhancements

- [ ] User authentication
- [ ] Search and filter saved cards
- [ ] Export to CSV/vCard
- [ ] Bulk upload processing
- [ ] Image quality validation
- [ ] Multiple language support
- [ ] Card categorization/tags

## License

MIT License - Feel free to use and modify as needed.

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify all environment variables are set correctly
3. Ensure Supabase table schema matches requirements
4. Test with the `/health` endpoint