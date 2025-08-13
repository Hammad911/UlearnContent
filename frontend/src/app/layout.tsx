import type { Metadata } from 'next'
import './globals.css'
import { Toaster } from 'react-hot-toast'
import Providers from '@/components/Providers'

export const metadata: Metadata = {
  title: 'OCR-to-LLM Pipeline',
  description: 'Extract text from images and process through LLMs for intelligent analysis',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans">
        <Providers>
          <div className="min-h-screen bg-gray-50">
            {children}
          </div>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
            }}
          />
        </Providers>
      </body>
    </html>
  )
} 