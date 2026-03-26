import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { ocrApi } from '../services/api'
import InvoiceSummary from '../components/InvoiceSummary'
import ItemsTable from '../components/ItemsTable'
import DownloadActions from '../components/DownloadActions'

/**
 * ResultPage Component
 * Displays the extracted invoice data and download options
 */
function ResultPage() {
    const { requestId } = useParams()
    const [loading, setLoading] = useState(true)
    const [status, setStatus] = useState(null)
    const [pages, setPages] = useState([])
    const [globalInvoiceData, setGlobalInvoiceData] = useState(null)
    const [error, setError] = useState(null)

    useEffect(() => {
        const fetchResults = async () => {
            if (!requestId) {
                setError('No Request ID provided')
                setLoading(false)
                return
            }

            try {
                // Fetch status first
                const statusData = await ocrApi.getRequestStatus(requestId)
                setStatus(statusData.status)

                // Check if processing is complete
                if (statusData.status !== 'SUCCESS' && statusData.status !== 'COMPLETED' && statusData.status !== 'PARTIAL_SUCCESS') {
                    setError('Processing not complete. Please wait and refresh.')
                    setLoading(false)
                    return
                }

                // Fetch extracted data
                const extractedData = await ocrApi.getExtractedData(requestId)

                // Parse global invoice data
                setGlobalInvoiceData(extractedData.invoice_data || {})

                // Parse pages
                if (extractedData.pages && extractedData.pages.length > 0) {
                    setPages(extractedData.pages)
                } else {
                    // Fallback if no pages array (single page or old format)
                    setPages([{
                        page_number: 1,
                        status: 'SUCCESS',
                        ocr: { structured_data: extractedData.invoice_data }
                    }])
                }

            } catch (err) {
                console.error('Fetch error:', err)
                if (err.response?.status === 404) {
                    setError('Request not found')
                    toast.error('Request ID not found')
                } else {
                    setError('Failed to load results')
                    toast.error('Failed to load results')
                }
            } finally {
                setLoading(false)
            }
        }

        fetchResults()
    }, [requestId])

    // Loading state
    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-center">
                    <svg className="animate-spin h-12 w-12 text-primary-500 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <p className="text-gray-600">Loading results...</p>
                </div>
            </div>
        )
    }

    // Error state
    if (error) {
        return (
            <div className="card text-center py-12">
                <svg className="mx-auto h-16 w-16 text-red-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Results</h2>
                <p className="text-gray-600 mb-6">{error}</p>
                <button
                    onClick={() => window.location.href = '/'}
                    className="btn-primary"
                >
                    Back to Dashboard
                </button>
            </div>
        )
    }

    // Get status badge color
    const getStatusBadge = () => {
        const statusColors = {
            'SUCCESS': 'bg-green-100 text-green-800 border-green-300',
            'COMPLETED': 'bg-green-100 text-green-800 border-green-300',
            'PARTIAL_SUCCESS': 'bg-yellow-100 text-yellow-800 border-yellow-300',
            'FAILED': 'bg-red-100 text-red-800 border-red-300',
        }
        const colorClass = statusColors[status] || 'bg-gray-100 text-gray-800 border-gray-300'

        return (
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border ${colorClass}`}>
                {status}
            </span>
        )
    }

    return (
        <div className="space-y-8">
            {/* Header with Request ID and Status */}
            <div className="card">
                <div className="flex items-center justify-between flex-wrap gap-4">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900 mb-2">
                            Extraction Results
                        </h1>
                        <p className="text-sm text-gray-600 flex items-center gap-2">
                            Request ID: <span className="font-mono font-semibold text-gray-900">{requestId}</span>
                            <button
                                onClick={() => {
                                    navigator.clipboard.writeText(requestId)
                                    toast.success('Copied!')
                                }}
                                className="text-primary-600 hover:text-primary-800"
                                title="Copy ID"
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                </svg>
                            </button>
                        </p>
                    </div>
                    <div>
                        {getStatusBadge()}
                    </div>
                </div>
            </div>

            {/* Page Iteration */}
            {pages.map((page, index) => {
                const pageData = page.ocr?.structured_data || {};
                const pageItems = pageData.items || [];

                return (
                    <div key={index} className="space-y-4 border-t-4 border-primary-100 pt-6">
                        <div className="flex items-center gap-2 mb-4">
                            <span className="bg-primary-100 text-primary-800 text-xs font-bold px-2.5 py-0.5 rounded border border-primary-200 uppercase">
                                Page {page.page_number}
                            </span>
                            {page.status !== 'SUCCESS' && (
                                <span className="text-red-600 text-sm font-semibold">({page.status})</span>
                            )}
                        </div>

                        {/* Page Summary */}
                        <InvoiceSummary data={pageData} />

                        {/* Custom Fields Section Removed as per request */}
                        {/* {pageData.custom_fields && ... } */}

                        {/* Page Items */}
                        <ItemsTable items={pageItems.map(i => ({ ...i, _page_num: page.page_number }))} />
                    </div>
                );
            })}

            {/* Download Actions */}
            <DownloadActions requestId={requestId} />
        </div>
    )
}

export default ResultPage
