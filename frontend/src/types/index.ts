// API Response Types
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

// Frontend State Types
export interface ProcessingResult {
  id: string
  originalText: string
  processedText: string
  taskType: string
  timestamp: Date
}

export interface UploadedFile {
  file: File
  id: string
  preview?: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  error?: string
}

export interface ProcessingStatus {
  isProcessing: boolean
  currentStep: string
  progress: number
  totalSteps: number
}

// Component Props Types
export interface FileUploadProps {
  onFilesSelected: (files: File[]) => void
  acceptedFileTypes?: string[]
  maxFiles?: number
  maxFileSize?: number
}

export interface ProcessingOptions {
  taskType: string
  language?: string
  maxLength?: number
  targetLanguage?: string
  analysisType?: string
}

export interface ResultCardProps {
  result: ProcessingResult
  onDelete?: (id: string) => void
  onDownload?: (id: string) => void
}

// API Error Types
export interface APIError {
  detail: string
  status_code: number
  message?: string
}

// Configuration Types
export interface AppConfig {
  apiBaseUrl: string
  maxFileSize: number
  allowedFileTypes: string[]
  supportedLanguages: string[]
  defaultTaskType: string
}

// Utility Types
export type TaskType = 'summarize' | 'analyze' | 'translate' | 'extract_entities'
export type AnalysisType = 'sentiment' | 'entities' | 'topics' | 'summary'
export type FileStatus = 'pending' | 'processing' | 'completed' | 'error' 