import { useState, useEffect } from 'react'
import { ocrApi } from '../services/api'
import toast from 'react-hot-toast'

/**
 * ProcessingStatus Component
 * Displays processing progress and polls for status updates
 */
function ProcessingStatus({ requestId, onComplete }) {
    const [status, setStatus] = useState('PROCESSING')
    const [progress, setProgress] = useState(60)

    useEffect(() => {
        if (!requestId) return

        const pollStatus = async () => {
            try {
                const data = await ocrApi.getRequestStatus(requestId)

                // Update status
                setStatus(data.status)

                // Update progress based on status
                if (data.status === 'PROCESSING') {
                    setProgress(75)
                } else if (data.status === 'SUCCESS' || data.status === 'COMPLETED') {
                    setProgress(100)
                    toast.success('Processing completed successfully!')
                    if (onComplete) {
                        onComplete()
                    }
                    return // Stop polling
                } else if (data.status === 'FAILED' || data.status === 'PARTIAL_SUCCESS') {
                    setProgress(100)
                    if (data.status === 'FAILED') {
                        toast.error('Processing failed')
                    } else {
                        toast('Processing completed with some warnings', { icon: '⚠️' })
                    }
                    if (onComplete) {
                        onComplete()
                    }
                    return // Stop polling
                }
            } catch (error) {
                console.error('Status polling error:', error)
            }
        }

        // Poll immediately
        pollStatus()

        // Then poll every 2 seconds
        const interval = setInterval(pollStatus, 2000)

        return () => clearInterval(interval)
    }, [requestId, onComplete])

    const getStatusColor = () => {
        switch (status) {
            case 'SUCCESS':
            case 'COMPLETED':
                return 'text-green-600'
            case 'FAILED':
                return 'text-red-600'
            case 'PARTIAL_SUCCESS':
                return 'text-yellow-600'
            default:
                return 'text-blue-600'
        }
    }

    return (
        <div className="card">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <svg className="w-5 h-5 mr-2 text-primary-500 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Processing Invoice
            </h2>

            {/* Progress Bar */}
            <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">Progress</span>
                    <span className="text-sm font-semibold text-gray-900">{progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${progress}%` }}
                    >
                        <div className="h-full w-full bg-white opacity-25 animate-pulse"></div>
                    </div>
                </div>
            </div>

            {/* Status */}
            <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm text-gray-600 mb-1">Current Status</p>
                        <p className={`text-lg font-semibold ${getStatusColor()}`}>
                            {status.replace('_', ' ')}
                        </p>
                    </div>
                    {(status === 'PROCESSING' || status === 'DOCUMENT_UPLOADED') && (
                        <div className="flex space-x-1">
                            <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                            <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                            <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                        </div>
                    )}
                </div>
            </div>

            <p className="mt-4 text-sm text-gray-500 text-center">
                This may take a few moments. Please wait...
            </p>
        </div>
    )
}

export default ProcessingStatus
