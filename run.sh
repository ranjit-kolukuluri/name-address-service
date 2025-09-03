#!/bin/bash
# run.sh - Simple script to run the Name & Address Validator

echo "🚀 Name & Address Validator Launcher"
echo "======================================"
echo ""
echo "Choose an option:"
echo "1) Run Streamlit UI (port 8501)"
echo "2) Run FastAPI Server (port 8000)"
echo "3) Run both (UI + API)"
echo "4) Install dependencies"
echo "5) Run debug app (troubleshooting)"
echo "6) Run minimal app (basic functionality)"
echo ""
read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        echo "🎨 Starting Streamlit UI..."
        streamlit run ui/app.py
        ;;
    2)
        echo "🔌 Starting FastAPI Server..."
        cd api && python main.py
        ;;
    3)
        echo "🚀 Starting both services..."
        echo "FastAPI will run on port 8000"
        echo "Streamlit will run on port 8501"
        echo ""
        # Start API in background
        cd api && python main.py &
        API_PID=$!
        echo "API started with PID: $API_PID"
        
        # Start Streamlit in foreground
        cd .. && streamlit run ui/app.py
        
        # Clean up API process when Streamlit exits
        kill $API_PID 2>/dev/null
        ;;
    4)
        echo "📦 Installing dependencies..."
        pip install -r requirements.txt
        echo "✅ Dependencies installed!"
        ;;
    5)
        echo "🔧 Starting debug app..."
        echo "This will help identify any issues with imports or initialization."
        streamlit run debug_app.py
        ;;
    6)
        echo "⚡ Starting minimal app..."
        echo "This is a basic version that should always work."
        streamlit run minimal_app.py
        ;;
    *)
        echo "❌ Invalid choice. Please run again and choose 1-6."
        exit 1
        ;;
esac