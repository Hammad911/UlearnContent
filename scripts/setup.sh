#!/bin/bash

echo "🚀 Setting up Educational Content Generator..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed. Please install Node.js 16+ first."
    exit 1
fi

# Check if Tesseract is installed
if ! command -v tesseract &> /dev/null; then
    echo "⚠️  Tesseract OCR is not installed. Please install it:"
    echo "   macOS: brew install tesseract"
    echo "   Ubuntu: sudo apt-get install tesseract-ocr"
    echo "   Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
fi

echo "📦 Setting up backend..."

# Backend setup
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# API Keys (get from respective services)
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
MATHPIX_API_KEY=your_mathpix_api_key
MATHPIX_APP_ID=your_mathpix_app_id

# Optional: Mistral AI for OCR
MISTRAL_API_KEY=your_mistral_api_key

# Server settings
CORS_ORIGINS=http://localhost:3000
EOF
    echo "⚠️  Please update the .env file with your API keys"
fi

# Create uploads directory
mkdir -p uploads

cd ..

echo "🎨 Setting up frontend..."

# Frontend setup
cd frontend

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Create .env.local file if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "Creating .env.local file..."
    cat > .env.local << EOF
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
EOF
fi

cd ..

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Update backend/.env with your API keys"
echo "2. Start the backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "3. Start the frontend: cd frontend && npm run dev"
echo "4. Open http://localhost:3000 in your browser"
echo ""
echo "🔑 Required API keys:"
echo "- OpenAI API Key (for fallback LLM)"
echo "- Google Gemini API Key (for content generation)"
echo "- MathPix API Key & App ID (for formula conversion)"
echo "- Mistral AI API Key (optional, for enhanced OCR)" 