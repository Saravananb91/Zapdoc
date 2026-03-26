import { useState } from 'react'
import toast from 'react-hot-toast'
import { ocrApi } from '../services/api'

/**
 * CreateRequest Component
 * Creates a new Zapdoc request and displays the generated Request ID.
 * Updated: Fixed syntax error.
 */
function CreateRequest({ onRequestCreated }) {
    const [requestId, setRequestId] = useState(null)
    const [loading, setLoading] = useState(false)
    const [email, setEmail] = useState('')

    const handleCreateRequest = async () => {
        if (!email) {
            toast.error('Please enter your email address')
            return
        }

        setLoading(true)
        try {
            const data = await ocrApi.createRequest(email, [])
            setRequestId(data.requestId)
            toast.success('Request created successfully!')

            // Notify parent component
            if (onRequestCreated) {
                onRequestCreated(data.requestId)
            }
        } catch (error) {
            console.error('Create request error:', error)
            toast.error('Failed to create request')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="card">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <svg className="w-5 h-5 mr-2 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Create New Zapdoc Request
            </h2>

            {!requestId ? (
                <div>
                    <p className="text-gray-600 mb-4">
                        Start by creating a new request to process your invoice
                    </p>

                    <div className="mb-4">
                        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                            Email Address <span className="text-red-500">*</span>
                        </label>
                        <input
                            type="email"
                            id="email"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-primary-500"
                            placeholder="your@email.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                        />
                    </div>

                    <button
                        onClick={handleCreateRequest}
                        disabled={loading}
                        className="btn-primary"
                    >
                        {loading ? (
                            <>
                                <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Creating...
                            </>
                        ) : (
                            <>
                                <svg className="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                                </svg>
                                Create New Request
                            </>
                        )}
                    </button>
                </div>
            ) : (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-start">
                        <svg className="w-6 h-6 text-green-500 mr-3 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div className="flex-1">
                            <h3 className="text-sm font-semibold text-green-900 mb-1">Request Created Successfully!</h3>
                            <p className="text-sm text-green-700 mb-2">Your Request ID:</p>
                            <div className="flex items-center gap-3">
                                <div className="bg-white border border-green-300 rounded px-4 py-2 font-mono text-lg text-gray-900">
                                    {requestId}
                                </div>
                                <button
                                    onClick={() => {
                                        navigator.clipboard.writeText(requestId)
                                        toast.success('Request ID copied!')
                                    }}
                                    className="p-2 text-green-600 hover:text-green-800 hover:bg-green-100 rounded-lg transition-colors"
                                    title="Copy Request ID"
                                >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                    </svg>
                                </button>
                            </div>
                            <p className="text-xs text-green-600 mt-2">
                                Please save this ID for future reference
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default CreateRequest
