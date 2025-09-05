#!/bin/bash
# Enhanced run.sh with USPS credential management

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to load environment variables from .env file
load_env() {
    if [ -f .env ]; then
        echo -e "${GREEN}📄 Loading environment variables from .env file...${NC}"
        export $(grep -v '^#' .env | xargs)
    fi
}

# Function to setup USPS credentials
setup_usps_credentials() {
    echo -e "${BLUE}🔐 USPS API Credential Setup${NC}"
    echo "================================"
    echo ""
    
    # Check if credentials already exist
    if [ -f .env ] && grep -q "USPS_CLIENT_ID" .env; then
        echo -e "${GREEN}✅ USPS credentials found in .env file${NC}"
        return 0
    fi
    
    if [ ! -z "$USPS_CLIENT_ID" ] && [ ! -z "$USPS_CLIENT_SECRET" ]; then
        echo -e "${GREEN}✅ USPS credentials found in environment variables${NC}"
        return 0
    fi
    
    if [ -f .streamlit/secrets.toml ] && grep -q "USPS_CLIENT_ID" .streamlit/secrets.toml; then
        echo -e "${GREEN}✅ USPS credentials found in .streamlit/secrets.toml${NC}"
        # Extract credentials from secrets.toml and set as env vars
        export USPS_CLIENT_ID=$(grep "USPS_CLIENT_ID" .streamlit/secrets.toml | cut -d'"' -f2)
        export USPS_CLIENT_SECRET=$(grep "USPS_CLIENT_SECRET" .streamlit/secrets.toml | cut -d'"' -f2)
        return 0
    fi
    
    echo -e "${YELLOW}⚠️ USPS credentials not found${NC}"
    echo "Address validation requires USPS API credentials."
    echo ""
    echo "You can:"
    echo "1) Add credentials to .env file (recommended for API server)"
    echo "2) Set environment variables"
    echo "3) Skip for now (name validation will still work)"
    echo ""
    read -p "Would you like to set up USPS credentials now? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        read -p "Enter USPS Client ID: " usps_id
        read -p "Enter USPS Client Secret: " usps_secret
        
        if [ ! -z "$usps_id" ] && [ ! -z "$usps_secret" ]; then
            # Create .env file
            echo "USPS_CLIENT_ID=$usps_id" > .env
            echo "USPS_CLIENT_SECRET=$usps_secret" >> .env
            echo -e "${GREEN}✅ USPS credentials saved to .env file${NC}"
            
            # Export for current session
            export USPS_CLIENT_ID="$usps_id"
            export USPS_CLIENT_SECRET="$usps_secret"
        else
            echo -e "${YELLOW}⚠️ Credentials not provided, continuing without USPS API${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ Continuing without USPS API - address validation will be unavailable${NC}"
    fi
}

# Function to check USPS credentials
check_usps_status() {
    if [ ! -z "$USPS_CLIENT_ID" ] && [ ! -z "$USPS_CLIENT_SECRET" ]; then
        echo -e "${GREEN}✅ USPS API: Configured${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️ USPS API: Not configured (address validation unavailable)${NC}"
        return 1
    fi
}

# Function to start API server with credentials
start_api_with_credentials() {
    local port=${1:-8000}
    
    echo -e "${BLUE}🔌 Starting FastAPI Server with USPS integration...${NC}"
    
    # Load environment variables
    load_env
    
    # Check credentials
    echo -e "${YELLOW}📋 Checking API configuration:${NC}"
    check_usps_status
    
    # Check port availability
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Port $port is already in use${NC}"
        read -p "Kill process on port $port? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            lsof -ti:$port | xargs kill -9 2>/dev/null
            sleep 2
        else
            port=$((port + 1))
            echo -e "${YELLOW}📍 Using alternative port: $port${NC}"
        fi
    fi
    
    echo -e "${GREEN}🚀 Starting API server on port $port...${NC}"
    echo -e "${BLUE}📚 Documentation: http://localhost:$port/docs${NC}"
    echo -e "${BLUE}🔍 Health check: http://localhost:$port/health${NC}"
    
    cd api && python -c "
import uvicorn
from main import app
uvicorn.run(app, host='0.0.0.0', port=$port)
"
}

# Function to start UI with credentials
start_ui_with_credentials() {
    local port=${1:-8501}
    
    echo -e "${BLUE}🎨 Starting Streamlit UI...${NC}"
    
    # Load environment variables for consistency
    load_env
    
    echo -e "${YELLOW}📋 Checking UI configuration:${NC}"
    check_usps_status
    
    # Check port availability
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Port $port is already in use${NC}"
        read -p "Kill process on port $port? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            lsof -ti:$port | xargs kill -9 2>/dev/null
            sleep 2
        else
            port=$((port + 1))
            echo -e "${YELLOW}📍 Using alternative port: $port${NC}"
        fi
    fi
    
    echo -e "${GREEN}🚀 Starting UI on port $port...${NC}"
    echo -e "${BLUE}🌐 UI available at: http://localhost:$port${NC}"
    
    streamlit run ui/app.py --server.port $port
}

# Main menu
echo -e "${BLUE}🚀 Enhanced Name & Address Validator${NC}"
echo "====================================="
echo ""

# Check and setup credentials if needed
setup_usps_credentials

echo ""
echo "Choose an option:"
echo "1) Run Streamlit UI (port 8501)"
echo "2) Run FastAPI Server (port 8000)"
echo "3) Run both (UI + API)"
echo "4) Install dependencies"
echo "5) Setup/check USPS credentials"
echo "6) Check system status"
echo "7) Cleanup all processes"
echo ""
read -p "Enter your choice (1-7): " choice

case $choice in
    1)
        start_ui_with_credentials
        ;;
    2)
        start_api_with_credentials
        ;;
    3)
        echo -e "${GREEN}🚀 Starting both services with USPS integration...${NC}"
        
        # Load environment variables
        load_env
        
        # Start API in background
        echo -e "${BLUE}Starting API server...${NC}"
        start_api_with_credentials 8000 &
        API_PID=$!
        
        # Wait for API to start
        sleep 5
        
        # Start UI in foreground
        echo -e "${BLUE}Starting UI...${NC}"
        start_ui_with_credentials 8501
        
        # Cleanup
        kill $API_PID 2>/dev/null
        ;;
    4)
        echo -e "${BLUE}📦 Installing dependencies...${NC}"
        pip install -r requirements.txt
        echo -e "${GREEN}✅ Dependencies installed!${NC}"
        ;;
    5)
        setup_usps_credentials
        load_env
        echo -e "${YELLOW}📋 Current credential status:${NC}"
        check_usps_status
        ;;
    6)
        echo -e "${BLUE}📊 System Status${NC}"
        echo "================"
        load_env
        check_usps_status
        echo ""
        echo -e "${YELLOW}Port Status:${NC}"
        for port in 8000 8501; do
            if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
                echo -e "  🔴 Port $port: IN USE"
            else
                echo -e "  🟢 Port $port: AVAILABLE"
            fi
        done
        ;;
    7)
        echo -e "${YELLOW}🧹 Cleaning up processes...${NC}"
        pkill -f "streamlit.*ui/app.py" 2>/dev/null
        pkill -f "uvicorn.*main:app" 2>/dev/null
        lsof -ti:8000 | xargs kill -9 2>/dev/null
        lsof -ti:8501 | xargs kill -9 2>/dev/null
        echo -e "${GREEN}✅ Cleanup complete${NC}"
        ;;
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac