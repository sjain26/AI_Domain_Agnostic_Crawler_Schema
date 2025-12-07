#!/bin/bash

echo "🚀 Setting up AI_Domain_Agnostic_Crawler Environment"
echo "=================================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
echo ""
echo "📥 Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt

echo ""
echo "✅ Dependencies installed!"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp env_template.txt .env
    echo "⚠️  Please edit .env file with your API keys and configuration"
else
    echo "✅ .env file exists"
fi

echo ""
echo "🧪 Running setup tests..."
echo ""
python3 test_setup.py

echo ""
echo "=================================================="
echo "✅ Setup complete!"
echo ""
echo "To activate the environment:"
echo "  source venv/bin/activate"
echo ""
echo "To run the application:"
echo "  python3 main.py"
echo ""
echo "To test Qdrant connection:"
echo "  python3 test_qdrant.py"
echo ""

