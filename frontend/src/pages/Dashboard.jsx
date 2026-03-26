import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import RequestSearch from '../components/RequestSearch'
import CreateRequest from '../components/CreateRequest'
import FileUpload from '../components/FileUpload'
import ProcessingStatus from '../components/ProcessingStatus'
import { ocrApi } from '../services/api'
import toast from 'react-hot-toast'

/**
 * Dashboard Page
 * Main page for creating new OCR requests and searching existing ones
 */
function Dashboard() {
    const [currentStep, setCurrentStep] = useState('search') // 'search', 'create', 'upload', 'processing'
    const [requestId, setRequestId] = useState(null)
    const navigate = useNavigate()

    // Handle request creation
    const handleRequestCreated = (newRequestId) => {
        setRequestId(newRequestId)
        setCurrentStep('upload')
    }

    // Handle file upload
    const handleUploadComplete = async () => {
        toast.success('Starting processing...')

        try {
            // Trigger processing
            await ocrApi.processInvoice(requestId)
            setCurrentStep('processing')
        } catch (error) {
            console.error('Processing error:', error)
            toast.error('Failed to start processing')
        }
    }

    // Handle processing complete
    const handleProcessingComplete = () => {
        setTimeout(() => {
            navigate(`/result/${requestId}`)
        }, 1500)
    }

    // Reset to initial state
    const handleReset = () => {
        setCurrentStep('search')
        setRequestId(null)
    }

    return (
        <div className="space-y-6">
            {/* Page Title & Actions */}
            <div className="flex flex-col md:flex-row items-center justify-between gap-4 mb-8">
                <div className="text-center md:text-left">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">
                        Zapdoc Dashboard
                    </h1>
                    <p className="text-gray-600">
                        Upload and process invoices or search for existing results
                    </p>
                </div>


            </div>

            {/* Create Request Section - First */}
            {currentStep === 'search' && (
                <div className="text-center">
                    <CreateRequest onRequestCreated={handleRequestCreated} />
                </div>
            )}

            {/* Divider */}
            {currentStep === 'search' && (
                <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-gray-300"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                        <span className="px-4 bg-gradient-to-br from-gray-50 to-gray-100 text-gray-500 font-medium">
                            OR
                        </span>
                    </div>
                </div>
            )}

            {/* Search Section - Second */}
            {currentStep === 'search' && <RequestSearch />}

            {currentStep === 'upload' && (
                <div className="space-y-6">
                    {/* Show Request ID */}
                    <div className="card bg-blue-50 border-blue-200">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-blue-600 mb-1">Active Request ID</p>
                                <div className="flex items-center gap-2">
                                    <p className="text-xl font-mono font-bold text-blue-900">{requestId}</p>
                                    <button
                                        onClick={() => {
                                            navigator.clipboard.writeText(requestId)
                                            toast.success('Request ID copied!')
                                        }}
                                        className="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded transition-colors"
                                        title="Copy Request ID"
                                    >
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                        </svg>
                                    </button>
                                </div>
                            </div>
                            <button
                                onClick={handleReset}
                                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                            >
                                Start Over
                            </button>
                        </div>
                    </div>

                    {/* File Upload */}
                    <FileUpload requestId={requestId} onUploadComplete={handleUploadComplete} />
                </div>
            )}

            {currentStep === 'processing' && (
                <div className="space-y-6">
                    {/* Show Request ID */}
                    <div className="card bg-blue-50 border-blue-200">
                        <p className="text-sm text-blue-600 mb-1">Processing Request ID</p>
                        <div className="flex items-center gap-2">
                            <p className="text-xl font-mono font-bold text-blue-900">{requestId}</p>
                            <button
                                onClick={() => {
                                    navigator.clipboard.writeText(requestId)
                                    toast.success('Request ID copied!')
                                }}
                                className="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded transition-colors"
                                title="Copy Request ID"
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                </svg>
                            </button>
                        </div>
                    </div>

                    {/* Processing Status */}
                    <ProcessingStatus requestId={requestId} onComplete={handleProcessingComplete} />
                </div>
            )}

            {/* Help Section */}
            <div className="card bg-gradient-to-br from-primary-50 to-secondary-50 border-primary-200">
                <div className="flex items-start space-x-3">
                    <svg className="w-6 h-6 text-primary-600 flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                        <h3 className="text-sm font-semibold text-gray-900 mb-2">How It Works</h3>
                        <ol className="text-sm text-gray-700 space-y-1 list-decimal list-inside">
                            <li>Create a new request to get a unique Request ID</li>
                            <li>Upload your invoice (PDF, JPG, PNG, or JPEG)</li>
                            <li>Wait for processing to complete (usually takes 10-30 seconds)</li>
                            <li>View and download the extracted data</li>
                        </ol>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Dashboard
