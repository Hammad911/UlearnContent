import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export interface OCRResponse {
  success: boolean
  text: string
  file_id: string
  original_filename: string
  processed_at: string
  error?: string
}

export interface ContentGenerationRequest {
  text: string
  topic?: string
}

export interface ContentGenerationResponse {
  success: boolean
  original_text: string
  content_items: Array<{
    topic: string
    subtopic: string
    content: string
  }>
  topic?: string
  processed_at: string
  processing_time: number
  total_items: number
  error?: string
}

export interface ImageGenerationRequest {
  content: string
  topic?: string
  subtopic?: string
}

export interface ImageGenerationResponse {
  success: boolean
  image_data?: string
  prompt_used?: string
  topic?: string
  subtopic?: string
  generated_at?: string
  error?: string
}

export interface ContentWithImageItem {
  topic: string
  subtopic: string
  content: string
  image_data?: string
  image_prompt?: string
}

export interface ContentWithImagesGenerationRequest {
  text: string
  topic?: string
  generate_images: boolean
}

export interface ContentWithImagesGenerationResponse {
  success: boolean
  original_text: string
  content_items: ContentWithImageItem[]
  topic?: string
  processed_at: string
  processing_time: number
  total_items: number
  images_generated: number
  error?: string
}

export interface ContentExcelGenerationRequest {
  text: string
  topic?: string
}

export interface ContentExcelGenerationResponse {
  success: boolean
  filename: string
  file_url: string
  topic?: string
  total_items: number
  generated_at: string
  error?: string
}

export interface QnAExcelGenerationRequest {
  text: string
  topic?: string
}

export interface QnAExcelGenerationResponse {
  success: boolean
  filename: string
  file_url: string
  topic?: string
  total_questions: number
  generated_at: string
  error?: string
}

// Quiz interfaces
export interface QuizQuestion {
  chapter: string
  topic: string
  question: string
  option_1: string
  option_2: string
  option_3: string
  option_4: string
  explanation: string
  correct_option: number
}

export interface QuizGenerationRequest {
  content: string
  topic: string
  chapter: string
  num_questions: number
  language: string
}

export interface QuizGenerationResponse {
  success: boolean
  topic: string
  chapter: string
  questions: QuizQuestion[]
  total_questions: number
  generated_at: string
  processing_time: number
  error?: string
}

export interface ExcelQuizRequest {
  content: string
  topic: string
  chapter: string
  num_questions: number
  filename?: string
  language: string
}

export interface ExcelQuizResponse {
  success: boolean
  filename: string
  file_url: string
  topic: string
  chapter: string
  total_questions: number
  generated_at: string
  error?: string
}

// OCR API functions
export const processImage = async (formData: FormData): Promise<OCRResponse> => {
  const response = await api.post('/api/v1/ocr/extract', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

// PDF API functions
export const processPDF = async (formData: FormData): Promise<any> => {
  const response = await api.post('/api/v1/pdf/extract', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const generateExcelFromPDF = async (formData: FormData): Promise<Blob> => {
  const response = await api.post('/api/v1/pdf/generate-excel', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    responseType: 'blob',
  })
  return response.data
}

export const getExcelContent = async (formData: FormData): Promise<any> => {
  const response = await api.post('/api/v1/pdf/get-excel-content', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

// LLM API functions
export const generateContent = async (text: string, topic?: string): Promise<ContentGenerationResponse> => {
  const response = await api.post('/api/v1/llm/generate-content', {
    text,
    topic,
  }, {
    timeout: 300000, // 5 minute timeout
  })
  return response.data
}

export const generateContentExcel = async (text: string, topic?: string): Promise<ContentExcelGenerationResponse> => {
  const response = await api.post('/api/v1/llm/generate-content-excel', {
    text,
    topic,
  }, {
    timeout: 300000, // 5 minute timeout
  })
  return response.data
}

export const generateQnAExcel = async (text: string, topic?: string): Promise<QnAExcelGenerationResponse> => {
  const response = await api.post('/api/v1/llm/generate-qna-excel', {
    text,
    topic,
  }, {
    timeout: 300000, // 5 minute timeout
  })
  return response.data
}

// Image generation API functions
export const generateImage = async (content: string, topic?: string, subtopic?: string): Promise<ImageGenerationResponse> => {
  const response = await api.post('/api/v1/llm/generate-image', {
    content,
    topic,
    subtopic,
  }, {
    timeout: 120000, // 2 minute timeout for image generation
  })
  return response.data
}

export const generateContentWithImages = async (
  text: string, 
  topic?: string, 
  generateImages: boolean = true
): Promise<ContentWithImagesGenerationResponse> => {
  const response = await api.post('/api/v1/llm/generate-content-with-images', {
    text,
    topic,
    generate_images: generateImages,
  }, {
    timeout: 600000, // 10 minute timeout for content + images
  })
  return response.data
}

// Quiz API functions
export const generateQuiz = async (
  content: string,
  topic: string,
  chapter: string,
  numQuestions: number = 10,
  language: string = "urdu"
): Promise<QuizGenerationResponse> => {
  const response = await api.post('/api/v1/quiz/generate-quiz', {
    content,
    topic,
    chapter,
    num_questions: numQuestions,
    language,
  }, {
    timeout: 300000, // 5 minute timeout
  })
  return response.data
}

export const generateExcelQuiz = async (
  content: string,
  topic: string,
  chapter: string,
  numQuestions: number = 10,
  filename?: string,
  language: string = "urdu"
): Promise<ExcelQuizResponse> => {
  const response = await api.post('/api/v1/quiz/generate-excel', {
    content,
    topic,
    chapter,
    num_questions: numQuestions,
    filename,
    language,
  }, {
    timeout: 300000, // 5 minute timeout
  })
  return response.data
}

export const downloadQuizFile = async (filename: string): Promise<Blob> => {
  const response = await api.get(`/api/v1/quiz/download/${filename}`, {
    responseType: 'blob',
  })
  return response.data
}

// Health check
export const healthCheck = async (): Promise<{ status: string; service: string }> => {
  const response = await api.get('/health')
  return response.data
}

export default api 