#!/bin/bash

# Quick start script for AI_Domain_Agnostic_Crawler

echo "AI_Domain_Agnostic_Crawler"
echo "======================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating .env from template..."
    cp env_template.txt .env
    echo "✅ Please edit .env with your configuration before running"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Check MySQL connection (optional)
echo "🔍 Checking configuration..."

# Start the server
echo "🚀 Starting FastAPI server..."
echo "📍 API will be available at http://localhost:8000"
echo "📚 API docs at http://localhost:8000/docs"
echo ""
python3 main.py

