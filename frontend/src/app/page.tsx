'use client'

import { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Brain, Download, Trash2, FileSpreadsheet, BookOpen } from 'lucide-react'
import toast from 'react-hot-toast'
import { processImage, processText, processPDF, generateExcelFromPDF, generateContent, getExcelContent } from '@/lib/api'
import { cn } from '@/lib/utils'

interface ProcessingResult {
  id: string
  originalText: string
  processedText: string
  taskType: string
  timestamp: Date
}

export default function Home() {
  const [isProcessing, setIsProcessing] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [extractedText, setExtractedText] = useState('')
  const [processingResults, setProcessingResults] = useState<ProcessingResult[]>([])
  const [selectedTask, setSelectedTask] = useState('summarize')
  const [pdfData, setPdfData] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<'ocr' | 'pdf'>('ocr')
  const [contentBreakdown, setContentBreakdown] = useState<any>(null)
  const [excelContent, setExcelContent] = useState<any[]>([])

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

    setIsProcessing(true)
    try {
      const formData = new FormData()
      uploadedFiles.forEach(file => {
        formData.append('file', file)
      })

      const result = await processImage(formData)
      setExtractedText(result.text)
      toast.success('Text extracted successfully!')
    } catch (error) {
      toast.error('Failed to extract text from image')
      console.error('OCR Error:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  const handlePDFProcessing = async () => {
    if (uploadedFiles.length === 0) {
      toast.error('Please upload at least one PDF file')
      return
    }

    setIsProcessing(true)
    try {
      const formData = new FormData()
      formData.append('file', uploadedFiles[0]) // Process first PDF

      const result = await processPDF(formData)
      setPdfData(result)
      setExtractedText(result.text)
      setContentBreakdown(result.content_breakdown || null)
      toast.success('PDF processed successfully!')
    } catch (error) {
      toast.error('Failed to process PDF')
      console.error('PDF Error:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleExcelGeneration = async () => {
    if (!pdfData) {
      toast.error('Please process a PDF first')
      return
    }

    setIsProcessing(true)
    try {
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
      toast.error('Failed to generate Excel file')
      console.error('Excel Error:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleLLMProcessing = async () => {
    if (!extractedText.trim()) {
      toast.error('Please extract text from an image first')
      return
    }

    setIsProcessing(true)
    try {
      let result;
      
      if (selectedTask === 'generate_content') {
        // Handle content generation separately
        result = await generateContent(extractedText, 'educational')
        const newResult: ProcessingResult = {
          id: Date.now().toString(),
          originalText: extractedText,
          processedText: result.generated_content,
          taskType: selectedTask,
          timestamp: new Date()
        }
        setProcessingResults(prev => [newResult, ...prev])
      } else {
        // Handle other LLM tasks
        result = await processText({
          text: extractedText,
          task_type: selectedTask,
          additional_context: {}
        })

        const newResult: ProcessingResult = {
          id: Date.now().toString(),
          originalText: extractedText,
          processedText: result.processed_result,
          taskType: selectedTask,
          timestamp: new Date()
        }
        setProcessingResults(prev => [newResult, ...prev])
      }

      toast.success(`${selectedTask.replace('_', ' ')} completed successfully!`)
    } catch (error) {
      toast.error(`Failed to process text with ${selectedTask}`)
      console.error('LLM Error:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  const clearResults = () => {
    setUploadedFiles([])
    setExtractedText('')
    setProcessingResults([])
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
    a.download = 'ocr-llm-results.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gradient mb-4">
            OCR-to-LLM Pipeline
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Extract text from images using OCR and process through Large Language Models 
            for intelligent analysis and insights.
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

              {activeTab === 'ocr' ? (
                <button
                  onClick={handleOCRProcessing}
                  disabled={isProcessing || uploadedFiles.length === 0}
                  className="btn-primary w-full mt-4 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isProcessing ? (
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
                    disabled={isProcessing || uploadedFiles.length === 0}
                    className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isProcessing ? (
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
                  
                  {pdfData && (
                    <button
                      onClick={handleExcelGeneration}
                      disabled={isProcessing}
                      className="btn-secondary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isProcessing ? (
                        <div className="flex items-center justify-center gap-2">
                          <div className="loading-spinner" />
                          Generating...
                        </div>
                      ) : (
                        <div className="flex items-center justify-center gap-2">
                          <FileSpreadsheet className="w-4 h-4" />
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

          {/* Right Column - LLM Processing */}
          <div className="space-y-6">
            {/* LLM Processing */}
            <div className="card">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Brain className="w-5 h-5" />
                LLM Processing
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Processing Task
                  </label>
                  <select
                    value={selectedTask}
                    onChange={(e) => setSelectedTask(e.target.value)}
                    className="input-field"
                  >
                    <option value="summarize">Summarize</option>
                    <option value="analyze">Analyze</option>
                    <option value="translate">Translate</option>
                    <option value="extract_entities">Extract Entities</option>
                    <option value="generate_content">Generate Educational Content</option>
                  </select>
                </div>

                <button
                  onClick={handleLLMProcessing}
                  disabled={isProcessing || !extractedText.trim()}
                  className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isProcessing ? (
                    <div className="flex items-center justify-center gap-2">
                      <div className="loading-spinner" />
                      Processing...
                    </div>
                  ) : (
                    <div className="flex items-center justify-center gap-2">
                      <Brain className="w-4 h-4" />
                      Process with LLM
                    </div>
                  )}
                </button>
              </div>
            </div>

            {/* Results */}
            {processingResults.length > 0 && (
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold">Processing Results</h2>
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
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-primary-600 capitalize">
                          {result.taskType.replace('_', ' ')}
                        </span>
                        <span className="text-xs text-gray-500">
                          {result.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="bg-white rounded p-3 max-h-32 overflow-y-auto">
                        <p className="text-sm text-gray-700">
                          {result.processedText}
                        </p>
                      </div>
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