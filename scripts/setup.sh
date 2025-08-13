#!/bin/bash

echo "🚀 Setting up OCR-to-LLM Pipeline Project"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+ first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Setup Backend
echo "📦 Setting up Backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create uploads directory
mkdir -p uploads

echo "✅ Backend setup complete"

# Setup Frontend
echo "📦 Setting up Frontend..."
cd ../frontend

# Install dependencies
echo "Installing Node.js dependencies..."
npm install

echo "✅ Frontend setup complete"

# Create environment files
echo "📝 Creating environment files..."

# Backend .env
cd ../backend
if [ ! -f ".env" ]; then
    cat > .env << EOF
DATABASE_URL=sqlite:///./app.db
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here
CORS_ORIGINS=http://localhost:3000
EOF
    echo "✅ Created backend/.env (please update with your OpenAI API key)"
else
    echo "ℹ️  backend/.env already exists"
fi

# Frontend .env.local
cd ../frontend
if [ ! -f ".env.local" ]; then
    cat > .env.local << EOF
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
EOF
    echo "✅ Created frontend/.env.local"
else
    echo "ℹ️  frontend/.env.local already exists"
fi

cd ..

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update backend/.env with your OpenAI API key"
echo "2. Start the backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "3. Start the frontend: cd frontend && npm run dev"
echo "4. Open http://localhost:3000 in your browser"
echo ""
echo "Or use Docker: docker-compose up --build" 