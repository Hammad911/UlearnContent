# Educational Content Generator

A streamlined application that extracts text from images or PDFs and generates structured educational content with MathPix formula support.

## Features

- **Fast OCR Processing**: Simplified OCR with optimized image preprocessing
- **PDF to Excel**: Convert PDF content to structured Excel format
- **Educational Content Generation**: Generate topic-based educational content from extracted text
- **MathPix Integration**: Automatic conversion of mathematical formulas to MathJax format
- **Modern UI**: Clean, responsive interface built with Next.js and Tailwind CSS

## Performance Optimizations

- **Simplified OCR**: Single, most effective preprocessing approach
- **Streamlined LLM Service**: Focused on educational content generation only
- **Short Prompts**: Optimized prompts for faster generation
- **MathPix API**: Professional formula conversion for mathematical content

## Setup

### Prerequisites

- Python 3.8+
- Node.js 16+
- Tesseract OCR

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the backend directory:
```env
# API Keys (get from respective services)
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
MATHPIX_API_KEY=your_mathpix_api_key
MATHPIX_APP_ID=your_mathpix_app_id

# Optional: Mistral AI for OCR
MISTRAL_API_KEY=your_mistral_api_key

# Server settings
CORS_ORIGINS=http://localhost:3000
```

5. Run the backend server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env.local` file:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

4. Run the development server:
```bash
npm run dev
```

## Usage

1. **Upload Files**: Drag and drop images or PDF files
2. **Extract Text**: Use OCR for images or PDF processing
3. **Generate Content**: Create structured educational content with topics and subtopics
4. **Download Results**: Export content as JSON or Excel files

## API Endpoints

### OCR
- `POST /api/v1/ocr/extract` - Extract text from images

### PDF Processing
- `POST /api/v1/pdf/extract` - Extract text and content from PDFs
- `POST /api/v1/pdf/generate-excel` - Generate Excel file from PDF content

### Content Generation
- `POST /api/v1/llm/generate-content` - Generate educational content from text

## MathPix Integration

The application automatically detects mathematical formulas in the extracted text and converts them to proper MathJax format using the MathPix API. This ensures that mathematical expressions are properly formatted for educational content.

## Performance Improvements

- **Reduced Processing Time**: Simplified OCR and LLM workflows
- **Optimized Prompts**: Shorter, more focused prompts for faster generation
- **Streamlined API**: Removed unnecessary endpoints and complexity
- **Better Error Handling**: Graceful fallbacks and clear error messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License 