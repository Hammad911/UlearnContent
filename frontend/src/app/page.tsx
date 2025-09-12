'use client'

import { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Brain, Download, Trash2, BookOpen, HelpCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { 
  processImage, 
  processPDF, 
  generateExcelFromPDF, 
  generateContent, 
  generateContentExcel,
  generateQnAExcel,
  getExcelContent,
  generateExcelQuiz,
  QuizQuestion
} from '@/lib/api'
import { cn } from '@/lib/utils'

interface ContentItem {
  topic: string
  subtopic: string
  content: string
}

interface ProcessingResult {
  id: string
  originalText: string
  contentItems: ContentItem[]
  processingTime: number
  timestamp: Date
}

interface QuizResult {
  id: string
  originalText: string
  questions: QuizQuestion[]
  processingTime: number
  timestamp: Date
  topic: string
  chapter: string
  filename?: string
}

export default function Home() {
  const [isOCRProcessing, setIsOCRProcessing] = useState(false)
  const [isPDFProcessing, setIsPDFProcessing] = useState(false)
  const [isExcelGenerating, setIsExcelGenerating] = useState(false)
  const [isContentGenerating, setIsContentGenerating] = useState(false)
  const [isMCQGenerating, setIsMCQGenerating] = useState(false)
  const [isQnAGenerating, setIsQnAGenerating] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [extractedText, setExtractedText] = useState('')
  const [processingResults, setProcessingResults] = useState<ProcessingResult[]>([])
  const [quizResults, setQuizResults] = useState<QuizResult[]>([])
  const [pdfData, setPdfData] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<'ocr' | 'pdf'>('ocr')
  const [contentBreakdown, setContentBreakdown] = useState<any>(null)
  const [excelContent, setExcelContent] = useState<any[]>([])
  const [topic, setTopic] = useState('')
  const [numQuestions, setNumQuestions] = useState(10)
  const [language, setLanguage] = useState('urdu')
  const [generationProgress, setGenerationProgress] = useState<string>('')
  const [generationTime, setGenerationTime] = useState<number>(0)

  const onDrop = (acceptedFiles: File[]) => {
    setUploadedFiles(acceptedFiles)
    toast.success(`${acceptedFiles.length} file(s) uploaded`)
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: activeTab === 'ocr' 
      ? { 'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.bmp', '.tiff'] }
      : { 'application/pdf': ['.pdf'] },
    multiple: true
  })

  const handleOCRProcessing = async () => {
    if (uploadedFiles.length === 0) {
      toast.error('Please upload at least one image')
      return
    }

    setIsOCRProcessing(true)
    setGenerationProgress('Starting OCR processing...')
    setGenerationTime(0)
    
    // Start timer
    const startTime = Date.now()
    const timerInterval = setInterval(() => {
      setGenerationTime(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)
    
    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setGenerationProgress(prev => {
          if (prev.includes('Starting OCR processing')) {
            return 'Analyzing image content...'
          } else if (prev.includes('Analyzing image content')) {
            return 'Extracting text...'
          } else if (prev.includes('Extracting text')) {
            return 'Finalizing text extraction...'
          } else {
            return 'Starting OCR processing...'
          }
        })
      }, 1500) // Update every 1.5 seconds
      
      const formData = new FormData()
      uploadedFiles.forEach(file => {
        formData.append('file', file)
      })

      const result = await processImage(formData)
      
      // Clear intervals
      clearInterval(progressInterval)
      clearInterval(timerInterval)
      setGenerationProgress('')
      setGenerationTime(0)
      
      setExtractedText(result.text)
      toast.success('Text extracted successfully!')
    } catch (error) {
      // Clear intervals
      clearInterval(timerInterval)
      setGenerationProgress('')
      setGenerationTime(0)
      
      toast.error('Failed to extract text from image')
      console.error('OCR Error:', error)
    } finally {
      setIsOCRProcessing(false)
    }
  }

  const handlePDFProcessing = async () => {
    if (uploadedFiles.length === 0) {
      toast.error('Please upload at least one PDF file')
      return
    }

    setIsPDFProcessing(true)
    setGenerationProgress('Starting PDF processing...')
    setGenerationTime(0)
    
    // Start timer
    const startTime = Date.now()
    const timerInterval = setInterval(() => {
      setGenerationTime(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)
    
    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setGenerationProgress(prev => {
          if (prev.includes('Starting PDF processing')) {
            return 'Analyzing PDF structure...'
          } else if (prev.includes('Analyzing PDF structure')) {
            return 'Extracting text and content...'
          } else if (prev.includes('Extracting text and content')) {
            return 'Processing tables and images...'
          } else if (prev.includes('Processing tables and images')) {
            return 'Finalizing PDF analysis...'
          } else {
            return 'Starting PDF processing...'
          }
        })
      }, 2000) // Update every 2 seconds
      
      const formData = new FormData()
      formData.append('file', uploadedFiles[0]) // Process first PDF

      const result = await processPDF(formData)
      
      // Clear intervals
      clearInterval(progressInterval)
      clearInterval(timerInterval)
      setGenerationProgress('')
      setGenerationTime(0)
      
      setPdfData(result)
      setExtractedText(result.text)
      setContentBreakdown(result.content_breakdown || null)
      toast.success('PDF processed successfully!')
    } catch (error) {
      // Clear intervals
      clearInterval(timerInterval)
      setGenerationProgress('')
      setGenerationTime(0)
      
      toast.error('Failed to process PDF')
      console.error('PDF Error:', error)
    } finally {
      setIsPDFProcessing(false)
    }
  }

  const handleExcelGeneration = async () => {
    if (!pdfData) {
      toast.error('Please process a PDF first')
      return
    }

    setIsExcelGenerating(true)
    setGenerationProgress('Starting Excel generation...')
    setGenerationTime(0)
    
    // Start timer
    const startTime = Date.now()
    const timerInterval = setInterval(() => {
      setGenerationTime(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)
    
    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setGenerationProgress(prev => {
          if (prev.includes('Starting Excel generation')) {
            return 'Analyzing PDF content...'
          } else if (prev.includes('Analyzing PDF content')) {
            return 'Extracting tables and data...'
          } else if (prev.includes('Extracting tables and data')) {
            return 'Creating Excel structure...'
          } else if (prev.includes('Creating Excel structure')) {
            return 'Finalizing Excel file...'
          } else {
            return 'Starting Excel generation...'
          }
        })
      }, 2000) // Update every 2 seconds
      
      const formData = new FormData()
      formData.append('file', uploadedFiles[0])
      formData.append('include_metadata', 'true')

      const result = await generateExcelFromPDF(formData)
      
      // Create download link
      const blob = new Blob([result], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${uploadedFiles[0].name.replace('.pdf', '')}_content.xlsx`
      a.click()
      URL.revokeObjectURL(url)
      
      // Clear intervals
      clearInterval(progressInterval)
      clearInterval(timerInterval)
      setGenerationProgress('')
      setGenerationTime(0)
      
      // Also fetch the content to display
      try {
        const contentFormData = new FormData()
        contentFormData.append('file', uploadedFiles[0])
        const contentResult = await getExcelContent(contentFormData)
        
        if (contentResult.success && contentResult.data) {
          setExcelContent(contentResult.data)
          toast.success(`Excel file generated and downloaded! Found ${contentResult.total_items} content items.`)
        } else {
          toast.success('Excel file generated and downloaded!')
        }
      } catch (contentError) {
        console.log('Could not fetch content for display:', contentError)
        toast.success('Excel file generated and downloaded!')
      }
    } catch (error) {
      // Clear intervals
      clearInterval(timerInterval)
      setGenerationProgress('')
      setGenerationTime(0)
      
      toast.error('Failed to generate Excel file')
      console.error('Excel Error:', error)
    } finally {
      setIsExcelGenerating(false)
    }
  }

  const handleContentGeneration = async () => {
    if (!extractedText.trim()) {
      toast.error('Please extract text from an image or PDF first')
      return
    }

    setIsContentGenerating(true)
    setGenerationProgress('Starting content generation...')
    setGenerationTime(0)
    
    // Start timer
    const startTime = Date.now()
    const timerInterval = setInterval(() => {
      setGenerationTime(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)
    
    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setGenerationProgress(prev => {
          if (prev.includes('Analyzing text structure')) {
            return 'Generating subtopics...'
          } else if (prev.includes('Generating subtopics')) {
            return 'Creating educational content...'
          } else if (prev.includes('Creating educational content')) {
            return 'Generating Excel file...'
          } else if (prev.includes('Generating Excel file')) {
            return 'Finalizing content...'
          } else {
            return 'Analyzing text structure...'
          }
        })
      }, 3000) // Update every 3 seconds
      
      // Generate content and Excel file
      const result = await generateContentExcel(extractedText, topic || undefined)
      
      // Clear intervals
      clearInterval(progressInterval)
      clearInterval(timerInterval)
      setGenerationProgress('')
      setGenerationTime(0)
      
      if (result.success) {
        // Download the Excel file
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}${result.file_url}`)
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = result.filename
        a.click()
        URL.revokeObjectURL(url)
        
        // Also generate content for display
        try {
          const contentResult = await generateContent(extractedText, topic || undefined)
          const newResult: ProcessingResult = {
            id: Date.now().toString(),
            originalText: extractedText,
            contentItems: contentResult.content_items,
            processingTime: contentResult.processing_time,
            timestamp: new Date()
          }
          setProcessingResults(prev => [newResult, ...prev])
        } catch (contentError) {
          console.log('Could not generate content for display:', contentError)
        }
        
        toast.success(`Generated ${result.total_items} content items and Excel file successfully!`)
      } else {
        throw new Error(result.error || 'Content generation failed')
      }
    } catch (error) {
      // Clear intervals
      clearInterval(timerInterval)
      setGenerationProgress('')
      setGenerationTime(0)
      
      if (error && typeof error === 'object' && 'toString' in error && error.toString().includes('timeout')) {
        toast.error('Content generation timed out. Please try with a smaller document or try again.')
      } else if (error && typeof error === 'object' && 'toString' in error && (error.toString().includes('429') || error.toString().includes('quota'))) {
        toast.error('API rate limit reached. Please wait a minute and try again, or use a smaller document.')
      } else {
        toast.error('Failed to generate educational content')
      }
      console.error('Content Generation Error:', error)
    } finally {
      setIsContentGenerating(false)
    }
  }

  const handleMCQGeneration = async () => {
    if (!extractedText.trim()) {
      toast.error('Please extract text from an image or PDF first')
      return
    }

    if (!topic.trim()) {
      toast.error('Please enter a chapter name')
      return
    }

    setIsMCQGenerating(true)
    setGenerationProgress('Starting MCQ generation...')
    setGenerationTime(0)
    
    // Start timer
    const startTime = Date.now()
    const timerInterval = setInterval(() => {
      setGenerationTime(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)
    
    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setGenerationProgress(prev => {
          if (prev.includes('Starting MCQ generation')) {
            return 'Analyzing text content...'
          } else if (prev.includes('Analyzing text content')) {
            return 'Detecting subtopic...'
          } else if (prev.includes('Detecting subtopic')) {
            return 'Generating questions...'
          } else if (prev.includes('Generating questions')) {
            return 'Creating Excel file...'
          } else if (prev.includes('Creating Excel file')) {
            return 'Finalizing MCQ file...'
          } else {
            return 'Starting MCQ generation...'
          }
        })
      }, 2000) // Update every 2 seconds
      
      const result = await generateExcelQuiz(
        extractedText,
        topic, // This is the chapter name (topic in Excel)
        topic, // Chapter name (same as topic for MCQ)
        numQuestions,
        undefined, // filename
        language
      )
      
      // Clear intervals
      clearInterval(progressInterval)
      clearInterval(timerInterval)
      setGenerationProgress('')
      setGenerationTime(0)
      
      if (result.success) {
        // Download the Excel file
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}${result.file_url}`)
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = result.filename
        a.click()
        URL.revokeObjectURL(url)
        
        // Add to quiz results
        const newQuizResult: QuizResult = {
          id: Date.now().toString(),
          originalText: extractedText,
          questions: [], // We don't have individual questions in the response
          processingTime: 0, // Not provided in response
          timestamp: new Date(),
          topic: result.topic,
          chapter: result.chapter,
          filename: result.filename
        }
        setQuizResults(prev => [newQuizResult, ...prev])
        
        toast.success(`MCQ Excel file generated successfully! ${result.total_questions} questions created.`)
      } else {
        throw new Error(result.error || 'MCQ generation failed')
      }
      
    } catch (error) {
      // Clear intervals
      clearInterval(timerInterval)
      setGenerationProgress('')
      setGenerationTime(0)
      
      if (error && typeof error === 'object' && 'toString' in error && error.toString().includes('timeout')) {
        toast.error('MCQ generation timed out. Please try with a smaller document or try again.')
      } else if (error && typeof error === 'object' && 'toString' in error && (error.toString().includes('429') || error.toString().includes('quota'))) {
        toast.error('API rate limit reached. Please wait a minute and try again.')
      } else {
        toast.error('Failed to generate MCQ file')
      }
      console.error('MCQ Generation Error:', error)
    } finally {
      setIsMCQGenerating(false)
    }
  }

  const handleQnAGeneration = async () => {
    if (!extractedText.trim()) {
      toast.error('Please extract text from an image or PDF first')
      return
    }

    setIsQnAGenerating(true)
    setGenerationProgress('Starting Q&A generation...')
    setGenerationTime(0)
    
    // Start timer
    const startTime = Date.now()
    const timerInterval = setInterval(() => {
      setGenerationTime(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)
    
    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setGenerationProgress(prev => {
          if (prev.includes('Starting Q&A generation')) {
            return 'Analyzing content structure...'
          } else if (prev.includes('Analyzing content structure')) {
            return 'Generating questions...'
          } else if (prev.includes('Generating questions')) {
            return 'Creating answers...'
          } else if (prev.includes('Creating answers')) {
            return 'Generating Excel file...'
          } else if (prev.includes('Generating Excel file')) {
            return 'Finalizing Q&A file...'
          } else {
            return 'Starting Q&A generation...'
          }
        })
      }, 2000) // Update every 2 seconds
      
      // Generate Q&A pairs and Excel file
      const result = await generateQnAExcel(extractedText, topic || undefined)
      
      // Clear intervals
      clearInterval(progressInterval)
      clearInterval(timerInterval)
      setGenerationProgress('')
      setGenerationTime(0)
      
      if (result.success) {
        // Download the Excel file
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}${result.file_url}`)
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = result.filename
        a.click()
        URL.revokeObjectURL(url)
        
        toast.success(`Generated ${result.total_questions} Q&A pairs and Excel file successfully!`)
      } else {
        throw new Error(result.error || 'Q&A generation failed')
      }
    } catch (error) {
      // Clear intervals
      clearInterval(timerInterval)
      setGenerationProgress('')
      setGenerationTime(0)
      
      if (error && typeof error === 'object' && 'toString' in error && error.toString().includes('timeout')) {
        toast.error('Q&A generation timed out. Please try with a smaller document or try again.')
      } else if (error && typeof error === 'object' && 'toString' in error && (error.toString().includes('429') || error.toString().includes('quota'))) {
        toast.error('API rate limit reached. Please wait a minute and try again.')
      } else {
        toast.error('Failed to generate Q&A Excel file')
      }
      console.error('Q&A Generation Error:', error)
    } finally {
      setIsQnAGenerating(false)
    }
  }

  const clearResults = () => {
    setUploadedFiles([])
    setExtractedText('')
    setProcessingResults([])
    setQuizResults([])
    setTopic('')
    toast.success('All results cleared')
  }

  const downloadResults = () => {
    const data = {
      extractedText,
      processingResults,
      timestamp: new Date().toISOString()
    }
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'educational-content-results.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gradient mb-4">
            Educational Content Generator
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Extract text from images or PDFs and generate structured educational content with MathPix formula support.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex justify-center mb-8">
          <div className="flex bg-white rounded-lg shadow-sm border">
            <button
              onClick={() => setActiveTab('ocr')}
              className={cn(
                "px-6 py-3 rounded-l-lg font-medium transition-colors",
                activeTab === 'ocr'
                  ? "bg-primary-600 text-white"
                  : "bg-white text-gray-600 hover:bg-gray-50"
              )}
            >
              <FileText className="w-4 h-4 inline mr-2" />
              OCR Processing
            </button>
            <button
              onClick={() => setActiveTab('pdf')}
              className={cn(
                "px-6 py-3 rounded-r-lg font-medium transition-colors",
                activeTab === 'pdf'
                  ? "bg-primary-600 text-white"
                  : "bg-white text-gray-600 hover:bg-gray-50"
              )}
            >
              <BookOpen className="w-4 h-4 inline mr-2" />
              PDF to Excel
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - File Upload & Processing */}
          <div className="space-y-6">
            {/* File Upload */}
            <div className="card">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Upload className="w-5 h-5" />
                Upload {activeTab === 'ocr' ? 'Images' : 'PDF Files'}
              </h2>
              
              <div
                {...getRootProps()}
                className={cn(
                  "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
                  isDragActive 
                    ? "border-primary-400 bg-primary-50" 
                    : "border-gray-300 hover:border-primary-400 hover:bg-gray-50"
                )}
              >
                <input {...getInputProps()} />
                <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                {isDragActive ? (
                  <p className="text-primary-600">Drop the files here...</p>
                ) : (
                  <div>
                    <p className="text-gray-600 mb-2">
                      Drag & drop {activeTab === 'ocr' ? 'images' : 'PDF files'} here, or click to select
                    </p>
                    <p className="text-sm text-gray-500">
                      {activeTab === 'ocr' 
                        ? 'Supports: JPG, PNG, GIF, BMP, TIFF'
                        : 'Supports: PDF files with text and images'
                      }
                    </p>
                  </div>
                )}
              </div>

              {uploadedFiles.length > 0 && (
                <div className="mt-4">
                  <h3 className="font-medium mb-2">Uploaded Files:</h3>
                  <div className="space-y-2">
                    {uploadedFiles.map((file, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <span className="text-sm truncate">{file.name}</span>
                        <span className="text-xs text-gray-500">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Progress Indicator for File Processing */}
              {generationProgress && ((activeTab === 'ocr' && isOCRProcessing) || (activeTab === 'pdf' && isPDFProcessing)) && (
                <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="loading-spinner w-5 h-5"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-blue-800">
                        {generationProgress}
                      </p>
                      <p className="text-xs text-blue-600 mt-1">
                        {activeTab === 'ocr' 
                          ? 'This may take 30-60 seconds for image processing...'
                          : 'This may take 1-2 minutes for PDF processing...'
                        }
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-blue-800">
                        {Math.floor(generationTime / 60)}:{(generationTime % 60).toString().padStart(2, '0')}
                      </p>
                      <p className="text-xs text-blue-600">elapsed</p>
                    </div>
                  </div>
                  
                  {/* Progress Bar */}
                  <div className="w-full bg-blue-200 rounded-full h-2">
                    <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                  </div>
                </div>
              )}

              {activeTab === 'ocr' ? (
                <button
                  onClick={handleOCRProcessing}
                  disabled={isOCRProcessing || uploadedFiles.length === 0}
                  className="btn-primary w-full mt-4 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isOCRProcessing ? (
                    <div className="flex items-center justify-center gap-2">
                      <div className="loading-spinner" />
                      Processing...
                    </div>
                  ) : (
                    <div className="flex items-center justify-center gap-2">
                      <FileText className="w-4 h-4" />
                      Extract Text (OCR)
                    </div>
                  )}
                </button>
              ) : (
                <div className="space-y-2 mt-4">
                  <button
                    onClick={handlePDFProcessing}
                    disabled={isPDFProcessing || uploadedFiles.length === 0}
                    className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isPDFProcessing ? (
                      <div className="flex items-center justify-center gap-2">
                        <div className="loading-spinner" />
                        Processing...
                      </div>
                    ) : (
                      <div className="flex items-center justify-center gap-2">
                        <BookOpen className="w-4 h-4" />
                        Process PDF
                      </div>
                    )}
                  </button>
                  
                  {/* Progress Indicator for Excel Generation */}
                  {generationProgress && isExcelGenerating && (
                    <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="loading-spinner w-5 h-5"></div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-blue-800">
                            {generationProgress}
                          </p>
                          <p className="text-xs text-blue-600 mt-1">
                            This may take 30-60 seconds for Excel generation...
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium text-blue-800">
                            {Math.floor(generationTime / 60)}:{(generationTime % 60).toString().padStart(2, '0')}
                          </p>
                          <p className="text-xs text-blue-600">elapsed</p>
                        </div>
                      </div>
                      
                      {/* Progress Bar */}
                      <div className="w-full bg-blue-200 rounded-full h-2">
                        <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                      </div>
                    </div>
                  )}
                  
                  {pdfData && (
                    <button
                      onClick={handleExcelGeneration}
                      disabled={isExcelGenerating}
                      className="btn-secondary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isExcelGenerating ? (
                        <div className="flex items-center justify-center gap-2">
                          <div className="loading-spinner" />
                          Generating...
                        </div>
                      ) : (
                        <div className="flex items-center justify-center gap-2">
                          <Download className="w-4 h-4" />
                          Generate Excel
                        </div>
                      )}
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Content Breakdown */}
            {contentBreakdown && (
              <div className="card">
                <h2 className="text-xl font-semibold mb-4">Content Analysis</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-blue-50 rounded-lg p-3">
                    <div className="text-2xl font-bold text-blue-600">{contentBreakdown.tables || 0}</div>
                    <div className="text-sm text-blue-700">Tables</div>
                  </div>
                  <div className="bg-green-50 rounded-lg p-3">
                    <div className="text-2xl font-bold text-green-600">{contentBreakdown.formulas || 0}</div>
                    <div className="text-sm text-green-700">Formulas</div>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-3">
                    <div className="text-2xl font-bold text-purple-600">{contentBreakdown.diagrams || 0}</div>
                    <div className="text-sm text-purple-700">Diagrams</div>
                  </div>
                  <div className="bg-orange-50 rounded-lg p-3">
                    <div className="text-2xl font-bold text-orange-600">{contentBreakdown.general_images || 0}</div>
                    <div className="text-sm text-orange-700">Images</div>
                  </div>
                </div>
              </div>
            )}

            {/* Extracted Text */}
            {extractedText && (
              <div className="card">
                <h2 className="text-xl font-semibold mb-4">Extracted Text</h2>
                <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                    {extractedText}
                  </p>
                </div>
              </div>
            )}

            {/* Excel Content Preview */}
            {excelContent.length > 0 && (
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold">Generated Excel Content</h2>
                  <span className="text-sm text-gray-500">{excelContent.length} items</span>
                </div>
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {excelContent.map((item, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-gray-50">
                      <div className="grid grid-cols-1 gap-2">
                        <div>
                          <span className="text-sm font-medium text-blue-600">Topic:</span>
                          <p className="text-sm text-gray-700 mt-1">{item.topic}</p>
                        </div>
                        {item.subtopic && (
                          <div>
                            <span className="text-sm font-medium text-green-600">Subtopic:</span>
                            <p className="text-sm text-gray-700 mt-1">{item.subtopic}</p>
                          </div>
                        )}
                        <div>
                          <span className="text-sm font-medium text-purple-600">Content:</span>
                          <div className="bg-white rounded p-3 mt-1 max-h-32 overflow-y-auto">
                            <p className="text-sm text-gray-700 whitespace-pre-wrap">
                              {item.content}
                            </p>
                          </div>
                        </div>
                        {item.video_link && (
                          <div>
                            <span className="text-sm font-medium text-orange-600">Video Link:</span>
                            <p className="text-sm text-gray-700 mt-1">{item.video_link}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Content Generation */}
          <div className="space-y-6">
            {/* Content Generation */}
            <div className="card">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Brain className="w-5 h-5" />
                Generate Educational Content
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Topic (Optional)
                  </label>
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="e.g., Mathematics, Physics, Chemistry"
                    className="input-field"
                  />
                </div>

                {/* Progress Indicator */}
                {generationProgress && isContentGenerating && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="loading-spinner w-5 h-5"></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-blue-800">
                          {generationProgress}
                        </p>
                        <p className="text-xs text-blue-600 mt-1">
                          This may take 1-3 minutes for large documents and Excel generation...
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-blue-800">
                          {Math.floor(generationTime / 60)}:{(generationTime % 60).toString().padStart(2, '0')}
                        </p>
                        <p className="text-xs text-blue-600">elapsed</p>
                      </div>
                    </div>
                    
                    {/* Progress Bar */}
                    <div className="w-full bg-blue-200 rounded-full h-2">
                      <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                    </div>
                  </div>
                )}

                <button
                  onClick={handleContentGeneration}
                  disabled={isContentGenerating || !extractedText.trim()}
                  className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isContentGenerating ? (
                    <div className="flex items-center justify-center gap-2">
                      <div className="loading-spinner" />
                      Generating Content...
                    </div>
                  ) : (
                    <div className="flex items-center justify-center gap-2">
                      <Brain className="w-4 h-4" />
                      Generate Educational Content & Excel
                    </div>
                  )}
                </button>
              </div>
            </div>

            {/* MCQ Generation */}
            <div className="card">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <HelpCircle className="w-5 h-5" />
                Generate MCQ File
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Chapter Name *
                  </label>
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="e.g., ٹیسٹ یونٹ PTB2:6"
                    className="input-field"
                  />
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-sm text-blue-800">
                    <strong>Note:</strong> Subtopic name will be automatically detected from the content.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Number of Questions
                    </label>
                    <select
                      value={numQuestions}
                      onChange={(e) => setNumQuestions(Number(e.target.value))}
                      className="input-field"
                    >
                      <option value={5}>5 Questions</option>
                      <option value={6}>6 Questions</option>
                      <option value={7}>7 Questions</option>
                      <option value={8}>8 Questions</option>
                      <option value={9}>9 Questions</option>
                      <option value={10}>10 Questions</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Language
                    </label>
                    <select
                      value={language}
                      onChange={(e) => setLanguage(e.target.value)}
                      className="input-field"
                    >
                      <option value="urdu">Urdu</option>
                      <option value="english">English</option>
                    </select>
                  </div>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <p className="text-sm text-yellow-800">
                    <strong>Note:</strong> MCQ file will be generated with correct answers marked with "Y*" prefix.
                  </p>
                </div>

                {/* Progress Indicator for MCQ Generation */}
                {generationProgress && isMCQGenerating && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="loading-spinner w-5 h-5"></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-blue-800">
                          {generationProgress}
                        </p>
                        <p className="text-xs text-blue-600 mt-1">
                          This may take 1-2 minutes for MCQ generation...
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-blue-800">
                          {Math.floor(generationTime / 60)}:{(generationTime % 60).toString().padStart(2, '0')}
                        </p>
                        <p className="text-xs text-blue-600">elapsed</p>
                      </div>
                    </div>
                    
                    {/* Progress Bar */}
                    <div className="w-full bg-blue-200 rounded-full h-2">
                      <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                    </div>
                  </div>
                )}

                <button
                  onClick={handleMCQGeneration}
                  disabled={isMCQGenerating || !extractedText.trim() || !topic.trim()}
                  className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isMCQGenerating ? (
                    <div className="flex items-center justify-center gap-2">
                      <div className="loading-spinner" />
                      Generating MCQ File...
                    </div>
                  ) : (
                    <div className="flex items-center justify-center gap-2">
                      <HelpCircle className="w-4 h-4" />
                      Generate MCQ Excel File
                    </div>
                  )}
                </button>
              </div>
            </div>

            {/* Q&A Generation */}
            <div className="card">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <HelpCircle className="w-5 h-5" />
                Generate Q&A Excel File
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Topic (Optional)
                  </label>
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="e.g., Mathematics, Physics, Chemistry"
                    className="input-field"
                  />
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-sm text-blue-800">
                    <strong>Note:</strong> This will generate an Excel file with columns: Topic, Sub-Topic, Question, and Answer.
                  </p>
                </div>

                {/* Progress Indicator for Q&A Generation */}
                {generationProgress && isQnAGenerating && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="loading-spinner w-5 h-5"></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-blue-800">
                          {generationProgress}
                        </p>
                        <p className="text-xs text-blue-600 mt-1">
                          This may take 2-4 minutes for Q&A generation...
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-blue-800">
                          {Math.floor(generationTime / 60)}:{(generationTime % 60).toString().padStart(2, '0')}
                        </p>
                        <p className="text-xs text-blue-600">elapsed</p>
                      </div>
                    </div>
                    
                    {/* Progress Bar */}
                    <div className="w-full bg-blue-200 rounded-full h-2">
                      <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                    </div>
                  </div>
                )}

                <button
                  onClick={handleQnAGeneration}
                  disabled={isQnAGenerating || !extractedText.trim()}
                  className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isQnAGenerating ? (
                    <div className="flex items-center justify-center gap-2">
                      <div className="loading-spinner" />
                      Generating Q&A File...
                    </div>
                  ) : (
                    <div className="flex items-center justify-center gap-2">
                      <HelpCircle className="w-4 h-4" />
                      Generate Q&A Excel File
                    </div>
                  )}
                </button>
              </div>
            </div>

            {/* Results */}
            {processingResults.length > 0 && (
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold">Generated Content</h2>
                  <div className="flex gap-2">
                    <button
                      onClick={downloadResults}
                      className="btn-secondary flex items-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Download
                    </button>
                    <button
                      onClick={clearResults}
                      className="btn-secondary flex items-center gap-2"
                    >
                      <Trash2 className="w-4 h-4" />
                      Clear
                    </button>
                  </div>
                </div>

                <div className="space-y-4">
                  {processingResults.map((result) => (
                    <div key={result.id} className="border rounded-lg p-4 bg-gray-50">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-primary-600">
                          Generated Content ({result.contentItems.length} subtopics)
                        </span>
                        <div className="text-xs text-gray-500">
                          <div>{result.timestamp.toLocaleTimeString()}</div>
                          <div>{result.processingTime.toFixed(2)}s</div>
                        </div>
                      </div>
                      
                      <div className="mb-3 p-2 bg-blue-50 rounded text-sm text-blue-700">
                        <strong>Note:</strong> Each subtopic below will appear on a separate row in Excel output.
                      </div>
                      
                      <div className="space-y-3">
                        {result.contentItems.map((item, index) => (
                          <div key={index} className="bg-white rounded p-3 border-l-4 border-blue-500">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-sm font-medium text-blue-600">{item.topic}</span>
                              {item.subtopic && (
                                <>
                                  <span className="text-gray-400">→</span>
                                  <span className="text-sm font-medium text-green-600">{item.subtopic}</span>
                                </>
                              )}
                              <span className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-600">
                                Row {index + 1}
                              </span>
                            </div>
                            <div className="text-sm text-gray-700 max-h-32 overflow-y-auto">
                              <p className="whitespace-pre-wrap">{item.content}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* MCQ Results */}
            {quizResults.length > 0 && (
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold">Generated MCQ Files</h2>
                  <div className="flex gap-2">
                    <button
                      onClick={clearResults}
                      className="btn-secondary flex items-center gap-2"
                    >
                      <Trash2 className="w-4 h-4" />
                      Clear
                    </button>
                  </div>
                </div>

                <div className="space-y-4">
                  {quizResults.map((result) => (
                    <div key={result.id} className="border rounded-lg p-4 bg-gray-50">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-primary-600">
                          MCQ File Generated
                        </span>
                        <div className="text-xs text-gray-500">
                          <div>{result.timestamp.toLocaleTimeString()}</div>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 mb-3">
                        <div>
                          <span className="text-sm font-medium text-blue-600">Chapter:</span>
                          <p className="text-sm text-gray-700">{result.topic}</p>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-green-600">Subtopic:</span>
                          <p className="text-sm text-gray-700">{result.chapter}</p>
                        </div>
                      </div>
                      
                      {result.filename && (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                          <p className="text-sm text-green-800">
                            <strong>✅ Success!</strong> MCQ Excel file "{result.filename}" has been generated and downloaded.
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
} 