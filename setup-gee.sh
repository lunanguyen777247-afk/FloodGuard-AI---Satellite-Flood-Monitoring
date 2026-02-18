#!/bin/bash
# Setup GEE Credentials Script
# This script helps set up GEE credentials safely

set -e

echo "=================================="
echo "🔐 GEE Credentials Setup"
echo "=================================="

# Colors
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if gee-key.json exists
if [ -f "fastapi/config/gee-key.json" ]; then
    echo -e "${GREEN}✓${NC} GEE credentials found"
else
    echo -e "${YELLOW}⚠${NC} GEE credentials not found"
    echo ""
    echo "To setup GEE, follow these steps:"
    echo ""
    echo "1. Visit Google Cloud Console:"
    echo "   https://console.cloud.google.com/iam-admin/serviceaccounts?project=driven-torus-431807-u3"
    echo ""
    echo "2. Select: floodguard-gee-service@driven-torus-431807-u3.iam.gserviceaccount.com"
    echo ""
    echo "3. Go to Keys tab → Add Key → Create new key → JSON"
    echo ""
    echo "4. Save the downloaded file as:"
    echo "   fastapi/config/gee-key.json"
    echo ""
    read -p "Press Enter when done..."
fi

# Check if .env exists
if [ -f "fastapi/.env" ]; then
    echo -e "${GREEN}✓${NC} .env file found"
else
    echo -e "${YELLOW}⚠${NC} .env file not found, creating from template..."
    cp fastapi/.env.example fastapi/.env
    echo -e "${GREEN}✓${NC} Created fastapi/.env"
    echo ""
    echo "Please fill in required values in fastapi/.env:"
    echo "  - GEMINI_API_KEY"
    echo "  - DATABASE_URL (or use SQLite)"
    echo "  - Other optional API keys"
fi

echo ""
echo "Testing GEE connection..."
if python3 fastapi/app/gee/test_simple.py; then
    echo ""
    echo -e "${GREEN}✅ GEE setup successful!${NC}"
    echo ""
    echo "You can now:"
    echo "  1. Start server: uvicorn app.main:app --reload"
    echo "  2. Test API: curl http://localhost:8000/api/regions"
else
    echo ""
    echo -e "${RED}❌ GEE setup failed${NC}"
    echo "Please check:"
    echo "  1. gee-key.json exists and is valid"
    echo "  2. .env is properly configured"
    echo "  3. Required Python packages are installed"
    exit 1
fi
