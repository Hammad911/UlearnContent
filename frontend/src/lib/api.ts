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

// Health check
export const healthCheck = async (): Promise<{ status: string; service: string }> => {
  const response = await api.get('/health')
  return response.data
}

export default api 