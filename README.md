# OCR-to-LLM Pipeline Project

A modern, industry-standard pipeline that extracts text from images using OCR and processes it through Large Language Models for intelligent analysis and insights.

## 🚀 Features

- **OCR Processing**: Extract text from images using advanced OCR technology
- **LLM Integration**: Process extracted text through state-of-the-art language models
- **RESTful API**: FastAPI backend with comprehensive endpoints
- **Modern Frontend**: React-based user interface with real-time processing
- **File Upload**: Support for multiple image formats
- **Real-time Processing**: Live status updates and progress tracking
- **Error Handling**: Robust error handling and validation

## 🏗️ Architecture

```
ulearncontent/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configurations
│   │   ├── models/         # Data models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── utils/          # Utility functions
│   │   └── styles/         # CSS/styling
│   ├── public/             # Static assets
│   └── package.json        # Node.js dependencies
├── docs/                   # Documentation
├── docker/                 # Docker configurations
└── scripts/                # Utility scripts
```

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation using Python type annotations
- **Uvicorn**: ASGI server for running FastAPI
- **Pillow**: Image processing
- **pytesseract**: OCR functionality
- **Mistral AI**: Advanced OCR and text extraction from images
- **Google Gemini AI**: Content generation and analysis
- **OpenAI**: LLM integration (fallback)
- **PyMuPDF**: PDF processing
- **openpyxl**: Excel file generation
- **pandas**: Data manipulation

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client
- **React Query**: Data fetching and caching
- **React Dropzone**: File upload component
- **React Hot Toast**: Toast notifications

### DevOps
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **GitHub Actions**: CI/CD pipeline
- **Black**: Code formatting
- **Flake8**: Linting
- **Pytest**: Testing framework

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker (optional)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:3000

### Docker Setup
```bash
docker-compose up --build
```

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📝 Environment Variables

Create `.env` files in both backend and frontend directories:

### Backend (.env)
```env
DATABASE_URL=sqlite:///./app.db
MISTRAL_API_KEY=your_mistral_api_key
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_secret_key
CORS_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, please open an issue in the GitHub repository or contact the development team. 