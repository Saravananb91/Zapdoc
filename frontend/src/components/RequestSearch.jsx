import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { ocrApi } from '../services/api'

/**
 * RequestSearch Component
 * Allows users to search for existing requests by Request ID
 */
function RequestSearch() {
    const [requestId, setRequestId] = useState('')
    const [loading, setLoading] = useState(false)
    const navigate = useNavigate()

    const handleSearch = async (e) => {
        e.preventDefault()

        if (!requestId.trim()) {
            toast.error('Please enter a Request ID')
            return
        }

        setLoading(true)
        try {
            // Check if request exists by fetching its status
            await ocrApi.getRequestStatus(requestId)

            // If successful, navigate to result page
            navigate(`/result/${requestId}`)
        } catch (error) {
            console.error('Search error:', error)
            if (error.response?.status === 404) {
                toast.error('Request ID not found')
            } else {
                toast.error('Failed to search request')
            }
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="card">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <svg className="w-5 h-5 mr-2 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Search by Request ID
            </h2>

            <form onSubmit={handleSearch} className="flex gap-3">
                <input
                    type="text"
                    value={requestId}
                    onChange={(e) => setRequestId(e.target.value)}
                    placeholder="Enter Request ID (e.g., 12345abc)"
                    className="input-field flex-1"
                    disabled={loading}
                />
                <button
                    type="submit"
                    disabled={loading}
                    className="btn-primary whitespace-nowrap"
                >
                    {loading ? (
                        <>
                            <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Searching...
                        </>
                    ) : (
                        'Search'
                    )}
                </button>
            </form>

            <p className="mt-3 text-sm text-gray-500">
                Enter a Request ID to view the extraction results
            </p>
        </div>
    )
}

export default RequestSearch
