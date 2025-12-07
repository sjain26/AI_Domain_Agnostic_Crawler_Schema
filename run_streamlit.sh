#!/bin/bash

echo "🚀 Starting Streamlit Demo App"
echo "================================"
echo ""

# Check if API is running
echo "🔍 Checking API server..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API server is running"
else
    echo "⚠️  API server is not running!"
    echo "📝 Please start the API server first:"
    echo "   cd AI_Domain_Agnostic_Crawler"
    echo "   source venv/bin/activate"
    echo "   uvicorn main:app --host 0.0.0.0 --port 8000"
    echo ""
    read -p "Do you want to start the API server now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Starting API server in background..."
        cd AI_Domain_Agnostic_Crawler
        source venv/bin/activate
        nohup uvicorn main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
        sleep 3
        echo "✅ API server started"
    else
        exit 1
    fi
fi

echo ""
echo "🌐 Starting Streamlit app..."
echo "📍 App will be available at: http://localhost:8501"
echo ""

cd AI_Domain_Agnostic_Crawler
source venv/bin/activate
streamlit run streamlit_app.py

