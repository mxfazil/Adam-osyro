@echo off
REM Business Card OCR API - Windows Setup Script

echo ================================================
echo   Business Card OCR API - Setup Script
echo ================================================
echo.

REM Check Python
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found
echo.

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [WARNING] Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated
echo.

REM Install dependencies
echo Installing dependencies...
if exist "requirements.txt" (
    python -m pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
    echo [OK] Dependencies installed
) else (
    echo [ERROR] requirements.txt not found
    pause
    exit /b 1
)
echo.

REM Install testing dependencies
echo Installing testing dependencies...
pip install --quiet pytest pytest-cov
echo [OK] Testing dependencies installed
echo.

REM Setup .env file
if not exist ".env" (
    echo Setting up environment file...
    if exist ".env.example" (
        copy .env.example .env >nul
        echo [OK] .env file created from .env.example
        echo [WARNING] Please edit .env with your credentials
    ) else (
        echo [ERROR] .env.example not found
        pause
        exit /b 1
    )
) else (
    echo [WARNING] .env file already exists
)
echo.

REM Generate API key
echo Checking API key...
findstr /C:"your-secret-api-key-change-this-in-production" .env >nul
if %errorlevel%==0 (
    echo Generating secure API key...
    
    REM Generate API key using Python
    for /f "delims=" %%i in ('python -c "import secrets; print(secrets.token_urlsafe(32))"') do set NEW_API_KEY=%%i
    
    REM Backup .env
    copy .env .env.backup >nul
    
    REM Replace API key
    powershell -Command "(Get-Content .env) -replace 'API_KEY=your-secret-api-key-change-this-in-production', 'API_KEY=%NEW_API_KEY%' | Set-Content .env"
    
    echo [OK] New API key generated and saved to .env
    echo Your API Key: %NEW_API_KEY%
    echo (Also saved in .env file)
) else (
    echo [OK] API key already configured
)
echo.

REM Create templates directory
if not exist "templates" (
    echo Creating templates directory...
    mkdir templates
    echo [OK] templates directory created
) else (
    echo [OK] templates directory exists
)
echo.

REM Check for form.html
if not exist "templates\form.html" (
    echo [WARNING] templates\form.html not found
    echo Please make sure form.html is in the templates directory
) else (
    echo [OK] templates\form.html found
)
echo.

REM Check if API is running
echo Checking if API is running...
curl -s http://localhost:8000/api/health >nul 2>&1
if %errorlevel%==0 (
    echo [OK] API is running
    echo.
    echo Testing API connection...
    curl -s http://localhost:8000/api/health
) else (
    echo [WARNING] API is not running
)
echo.

REM Summary
echo ================================================
echo   Setup Complete!
echo ================================================
echo.
echo Next steps:
echo.
echo 1. Configure your credentials in .env:
echo    - SUPABASE_URL
echo    - SUPABASE_KEY
echo    - LLAMA_API_URL
echo    - LLAMA_API_KEY
echo.
echo 2. Start the server:
echo    python ocr.py
echo.
echo 3. Access the application:
echo    Web Interface: http://localhost:8000
echo    API Docs:      http://localhost:8000/api/docs
echo.
echo 4. Test the API:
echo    pytest test_api.py -v
echo.
echo 5. Read the documentation:
echo    - README.md              (Main documentation)
echo    - API_DOCUMENTATION.md   (API reference)
echo    - QUICKSTART.md          (Integration guide)
echo.
echo ================================================
echo.

REM Offer to start server
set /p START_SERVER="Would you like to start the server now? (y/n): "
if /i "%START_SERVER%"=="y" (
    echo.
    echo Starting server...
    python ocr.py
)

pause