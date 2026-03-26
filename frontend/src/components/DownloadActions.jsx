import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ocrApi } from '../services/api'
import toast from 'react-hot-toast'

/**
 * DownloadActions Component
 * Provides download buttons for different formats and navigation
 */
function DownloadActions({ requestId }) {
    const [downloading, setDownloading] = useState(null)
    const [emailing, setEmailing] = useState(false)
    const navigate = useNavigate()

    const handleDownload = async (format) => {
        setDownloading(format)
        try {
            const url = ocrApi.downloadResult(requestId, format)

            // Open download URL in new tab
            window.open(url, '_blank')

            toast.success(`Downloading ${format.toUpperCase()} file...`)
        } catch (error) {
            console.error('Download error:', error)
            toast.error(`Failed to download ${format.toUpperCase()}`)
        } finally {
            setTimeout(() => setDownloading(null), 1000)
        }
    }

    const handleProcessNew = () => {
        navigate('/')
        toast.success('Ready to process a new invoice')
    }

    return (
        <div className="card">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Download Options
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {/* 1. Send to Email (Primary Action) */}
                <button
                    onClick={async () => {
                        setEmailing(true)
                        try {
                            await ocrApi.sendEmail(requestId)
                            toast.success('Email sent successfully!')
                        } catch (error) {
                            console.error('Email error:', error)
                            toast.error('Failed to send email. Check logs.')
                        } finally {
                            setEmailing(false)
                        }
                    }}
                    disabled={emailing}
                    className="btn-primary flex items-center justify-center"
                    title="Send results to the email used for this request"
                >
                    {emailing ? (
                        <>
                            <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Sending...
                        </>
                    ) : (
                        <>
                            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                            </svg>
                            Send to Email
                        </>
                    )}
                </button>

                {/* 2. Download Excel */}
                <button
                    onClick={() => handleDownload('xlsx')}
                    disabled={downloading === 'xlsx'}
                    className="btn-secondary flex items-center justify-center text-green-700 hover:text-green-800 hover:bg-green-50 border-green-200"
                >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    {downloading === 'xlsx' ? 'Downloading...' : 'Download Excel'}
                </button>

                {/* 3. Download CSV */}
                <button
                    onClick={() => handleDownload('csv')}
                    disabled={downloading === 'csv'}
                    className="btn-secondary flex items-center justify-center"
                >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    {downloading === 'csv' ? 'Downloading...' : 'Download CSV'}
                </button>

                {/* 4. Process New Invoice */}
                <button
                    onClick={handleProcessNew}
                    className="btn-secondary flex items-center justify-center text-gray-700 hover:bg-gray-50 border-gray-300"
                >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Process New Invoice
                </button>
            </div>

            <p className="mt-4 text-sm text-gray-500 text-center">
                Choose a format to download the extracted data or process a new invoice
            </p>
        </div>
    )
}

export default DownloadActions
