Business Card OCR Scanner
A FastAPI-based application that extracts information from business cards using Llama Vision AI, allows user confirmation, and stores the results in Supabase.

Features
✏️ Manual entry - Fill in business card details manually
📤 Upload business card images from your device
📷 Capture photos directly using your webcam
🤖 AI-powered OCR using Llama 3.2 Vision model
✨ Auto-fill form - OCR automatically fills the form fields
✏️ Review and edit extracted information before saving
💾 Store data in Supabase database
🎨 Modern, intuitive UI with drag & drop support
Architecture
Components
Backend (FastAPI)
Handles image uploads and camera captures
Processes images with Llama Vision API
Manages Supabase database operations
Returns JSON responses for AJAX requests
Frontend
form.html - Unified interface with form, upload, and camera capture
Tab-based interface for easy switching between input methods
Real-time validation and auto-fill indicators
External Services
Llama API - Vision model for OCR
Supabase - PostgreSQL database for storage
Prerequisites
Python 3.8+
Supabase account and project
Llama API access (or compatible vision API endpoint)
Installation
Clone the repository
bash
   git clone <your-repo>
   cd business-card-ocr
Create virtual environment
bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies
bash
   pip install -r requirements.txt
Set up environment variables
bash
   cp .env.example .env
Edit .env and add your credentials:

SUPABASE_URL - Your Supabase project URL
SUPABASE_KEY - Your Supabase service role key
LLAMA_API_URL - Your Llama API endpoint
LLAMA_API_KEY - Your Llama API key
Create Supabase table Run this SQL in your Supabase SQL editor:
sql
   CREATE TABLE business_cards (
       id BIGSERIAL PRIMARY KEY,
       name TEXT NOT NULL,
       email TEXT,
       phone TEXT,
       company TEXT,
       created_at TIMESTAMPTZ DEFAULT NOW()
   );
Create templates directory
bash
   mkdir templates
Place form.html in the templates/ directory.

Usage
Start the server
bash
   python ocr.py
Or with uvicorn:

bash
   uvicorn ocr:app --reload --host 0.0.0.0 --port 8000
Access the application Open your browser and navigate to:
   http://localhost:8000
Enter business card information You have three options: Option A: Manual Entry
Simply fill in the form fields manually
Option B: Upload Image
Click the "Upload Image" tab
Click the upload area or drag & drop an image
Wait for OCR to extract and auto-fill the form
Review and edit any fields if needed
Option C: Camera Capture
Click the "Use Camera" tab
Click "Start Camera" and allow camera access
Position the business card in the frame
Click "Capture" to take a photo
Wait for OCR to extract and auto-fill the form
Review and edit any fields if needed
Save to database
After reviewing the information, click "Save to Database"
You'll see a success message when saved
API Endpoints
GET / - Home page (unified form interface)
POST /extract - Process image and return extracted data as JSON
POST /save - Save confirmed data to Supabase
GET /health - Health check endpoint
Project Structure
business-card-ocr/
├── ocr.py              # Main FastAPI application
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variables template
├── .env               # Your environment variables (not in git)
├── .gitignore         # Git ignore rules
├── README.md          # This file
└── templates/
    └── form.html      # Unified interface (form + upload + camera)
Key Features
Backend (ocr.py)
✅ Environment variable support for configuration
✅ Comprehensive error handling and logging
✅ Image optimization (resize, format conversion)
✅ Robust JSON parsing from LLM responses
✅ Request timeout handling
✅ Input validation
✅ Health check endpoint
✅ JSON responses for AJAX requests
Frontend (form.html)
✅ Unified interface - form, upload, and camera in one page
✅ Tab-based navigation between input methods
✅ Drag & drop file upload support
✅ Camera start/stop functionality
✅ Loading indicators for async operations
✅ Success/error message alerts
✅ Auto-fill indicators showing which fields were extracted
✅ Real-time form validation
✅ Email format validation
✅ Mobile-responsive design
✅ Modern gradient design with smooth animations
User Experience Improvements
Flexible Input Methods
Users can choose the method that works best for them
Easy switching between manual entry, upload, and camera
Visual Feedback
Auto-filled fields are highlighted in green
Clear indicators show which fields were extracted from OCR
Loading overlays prevent confusion during processing
Error Handling
Clear error messages for validation issues
Graceful handling of OCR failures
Camera permission errors are user-friendly
Form Validation
Real-time validation as user types
Clear error messages under fields
Email format validation
Required field indicators
Troubleshooting
Camera not working
Check browser permissions for camera access
Use HTTPS in production (required for camera access)
Try a different browser
Ensure camera is not being used by another application
OCR extraction issues
Ensure image is clear and well-lit
Check Llama API credentials in .env
Review logs for API errors
Try uploading instead of camera if quality is low
Database connection errors
Verify Supabase credentials in .env
Check table exists with correct schema
Review Supabase logs in dashboard
Test connection with /health endpoint
Form not auto-filling
Check browser console for JavaScript errors
Verify API is returning success response
Ensure JSON response format is correct
Check network tab in browser dev tools
Security Notes
⚠️ Important: Never commit your .env file to version control!

Use service role key only on server-side
Consider using anon key + RLS policies for production
Implement authentication before deploying
Add rate limiting for production use
Validate file types and sizes on server-side
Sanitize user inputs before database insertion
Future Enhancements
 User authentication and login
 Search and filter saved cards
 Export to CSV/vCard
 Bulk upload processing
 Image quality validation and feedback
 Multiple language support
 Card categorization/tags
 Edit/delete saved cards
 Duplicate detection
 Analytics dashboard
License
MIT License - Feel free to use and modify as needed.

Support
For issues or questions:

Check the logs for error messages
Verify all environment variables are set correctly
Ensure Supabase table schema matches requirements
Test with the /health endpoint
Check browser console for frontend errors
