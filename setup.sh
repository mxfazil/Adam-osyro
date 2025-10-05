#!/bin/bash

# Business Card OCR API - Setup Script
# This script helps you set up the API quickly

set -e

echo "================================================"
echo "  Business Card OCR API - Setup Script"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Install dependencies
echo "Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}✗ requirements.txt not found${NC}"
    exit 1
fi
echo ""

# Install testing dependencies
echo "Installing testing dependencies..."
pip install -q pytest pytest-cov
echo -e "${GREEN}✓ Testing dependencies installed${NC}"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Setting up environment file..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created from .env.example${NC}"
        echo -e "${YELLOW}⚠ Please edit .env with your credentials${NC}"
    else
        echo -e "${RED}✗ .env.example not found${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ .env file already exists${NC}"
fi
echo ""

# Generate API key if not set
echo "Checking API key..."
if grep -q "your-secret-api-key-change-this-in-production" .env; then
    echo "Generating secure API key..."
    NEW_API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Backup .env
    cp .env .env.backup
    
    # Replace API key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/API_KEY=your-secret-api-key-change-this-in-production/API_KEY=$NEW_API_KEY/" .env
    else
        # Linux
        sed -i "s/API_KEY=your-secret-api-key-change-this-in-production/API_KEY=$NEW_API_KEY/" .env
    fi
    
    echo -e "${GREEN}✓ New API key generated and saved to .env${NC}"
    echo -e "${YELLOW}Your API Key: $NEW_API_KEY${NC}"
    echo -e "${YELLOW}(Also saved in .env file)${NC}"
else
    echo -e "${GREEN}✓ API key already configured${NC}"
fi
echo ""

# Create templates directory if it doesn't exist
if [ ! -d "templates" ]; then
    echo "Creating templates directory..."
    mkdir templates
    echo -e "${GREEN}✓ templates/ directory created${NC}"
else
    echo -e "${GREEN}✓ templates/ directory exists${NC}"
fi
echo ""

# Check if form.html exists
if [ ! -f "templates/form.html" ]; then
    echo -e "${YELLOW}⚠ templates/form.html not found${NC}"
    echo "Please make sure form.html is in the templates/ directory"
else
    echo -e "${GREEN}✓ templates/form.html found${NC}"
fi
echo ""

# Run health check if server is already running
echo "Checking if API is running..."
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is running${NC}"
    echo ""
    echo "Testing API connection..."
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/health)
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    echo -e "${YELLOW}⚠ API is not running${NC}"
fi
echo ""

# Summary
echo "================================================"
echo "  Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your credentials in .env:"
echo "   - SUPABASE_URL"
echo "   - SUPABASE_KEY"
echo "   - LLAMA_API_URL"
echo "   - LLAMA_API_KEY"
echo ""
echo "2. Start the server:"
echo "   ${GREEN}python ocr.py${NC}"
echo ""
echo "3. Access the application:"
echo "   Web Interface: ${GREEN}http://localhost:8000${NC}"
echo "   API Docs:      ${GREEN}http://localhost:8000/api/docs${NC}"
echo ""
echo "4. Test the API:"
echo "   ${GREEN}pytest test_api.py -v${NC}"
echo ""
echo "5. Read the documentation:"
echo "   - README.md              (Main documentation)"
echo "   - API_DOCUMENTATION.md   (API reference)"
echo "   - QUICKSTART.md          (Integration guide)"
echo ""
echo "================================================"
echo ""

# Offer to start the server
read -p "Would you like to start the server now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting server..."
    python ocr.py
fi