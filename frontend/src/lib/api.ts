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
  confidence?: number
  language?: string
  error?: string
  word_count?: number
  character_count?: number
}

export interface LLMRequest {
  text: string
  task_type: string
  additional_context?: Record<string, any>
}

export interface LLMResponse {
  success: boolean
  original_text: string
  processed_result: string
  task_type: string
  processed_at: string
  model_used?: string
  processing_time?: number
  error?: string
}

export interface AnalysisRequest {
  text: string
  analysis_type: string
  language?: string
}

export interface AnalysisResponse {
  success: boolean
  original_text: string
  analysis_result: Record<string, any>
  analysis_type: string
  language: string
  processed_at: string
  confidence_scores?: Record<string, number>
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

export const processBatchImages = async (formData: FormData): Promise<OCRResponse[]> => {
  const response = await api.post('/api/v1/ocr/batch-extract', formData, {
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

export const analyzePDFContent = async (formData: FormData): Promise<any> => {
  const response = await api.post('/api/v1/pdf/analyze-content', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

// LLM API functions
export const processText = async (request: LLMRequest): Promise<LLMResponse> => {
  const response = await api.post('/api/v1/llm/process', request)
  return response.data
}

export const analyzeText = async (request: AnalysisRequest): Promise<AnalysisResponse> => {
  const response = await api.post('/api/v1/llm/analyze', request)
  return response.data
}

export const summarizeText = async (request: LLMRequest): Promise<{ summary: string }> => {
  const response = await api.post('/api/v1/llm/summarize', request)
  return response.data
}

export const translateText = async (request: LLMRequest): Promise<{ translated_text: string }> => {
  const response = await api.post('/api/v1/llm/translate', request)
  return response.data
}

export const extractEntities = async (request: LLMRequest): Promise<{ entities: any[] }> => {
  const response = await api.post('/api/v1/llm/extract-entities', request)
  return response.data
}

export const generateContent = async (text: string, contentType: string = 'educational', topic?: string, difficultyLevel: string = 'intermediate', targetAudience: string = 'students'): Promise<any> => {
  const response = await api.post('/api/v1/llm/generate-content', {
    text,
    content_type: contentType,
    topic,
    difficulty_level: difficultyLevel,
    target_audience: targetAudience,
  })
  return response.data
}

// File management API functions
export const listFiles = async (): Promise<{ files: any[]; total: number }> => {
  const response = await api.get('/api/v1/files/list')
  return response.data
}

export const deleteFile = async (filename: string): Promise<{ success: boolean; message: string }> => {
  const response = await api.delete(`/api/v1/files/${filename}`)
  return response.data
}

export const getFileInfo = async (filename: string): Promise<any> => {
  const response = await api.get(`/api/v1/files/info/${filename}`)
  return response.data
}

export const cleanupFiles = async (): Promise<{ deleted: number; message: string }> => {
  const response = await api.post('/api/v1/files/cleanup')
  return response.data
}

// Health check
export const healthCheck = async (): Promise<{ status: string; service: string }> => {
  const response = await api.get('/health')
  return response.data
}

export default api 