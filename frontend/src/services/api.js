import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
    baseURL: '/api/v1',
    headers: {
        'Content-Type': 'application/json',
        'X-API-KEY': 'dev_secret_key_123'
    },
})

// API Service Methods
export const ocrApi = {
    /**
     * Create a new OCR request
     * @returns {Promise<{requestId: string}>}
     */
    createRequest: async (email, customFields) => {
        const response = await api.post('/requests', { email, custom_fields: customFields })
        return response.data
    },

    /**
     * Upload a file for OCR processing
     * @param {string} requestId - The request ID
     * @param {File} file - The file to upload
     * @returns {Promise<any>}
     */
    uploadFile: async (requestId, file) => {
        const formData = new FormData()
        formData.append('file', file)

        const response = await api.post(`/requests/${requestId}/documents`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        })
        return response.data
    },

    /**
     * Trigger invoice processing/extraction
     * @param {string} requestId - The request ID
     * @returns {Promise<any>}
     */
    processInvoice: async (requestId) => {
        const response = await api.post(`/requests/${requestId}/extract`)
        return response.data
    },

    /**
     * Get the status of a request
     * @param {string} requestId - The request ID
     * @returns {Promise<{status: string, extractedData: any}>}
     */
    getRequestStatus: async (requestId) => {
        const response = await api.get(`/requests/${requestId}/status`)
        return response.data
    },

    /**
     * Get the full extracted data (for results page)
     * @param {string} requestId - The request ID
     * @returns {Promise<any>}
     */
    getExtractedData: async (requestId) => {
        const response = await api.get(`/requests/${requestId}/extracted-data/download?format=json`)
        return response.data
    },

    /**
     * Download results in specified format
     * @param {string} requestId - The request ID
     * @param {string} format - Format: 'json', 'csv', or 'zip'
     * @returns {string} - Download URL
     */
    /**
     * Download results in specified format
     * @param {string} requestId - The request ID
     * @param {string} format - Format: 'json', 'csv', or 'zip'
     * @returns {string} - Download URL
     */
    downloadResult: (requestId, format) => {
        // Use new CLEAN export endpoint
        return `/api/v1/requests/${requestId}/download/clean?format=${format}`
    },

    /**
     * Download ALL extracted data in bulk
     * @param {string} format - Format: 'csv', 'json', 'zip'
     * @returns {string} - Download URL
     */
    exportAllData: (format = 'csv') => {
        return `/api/v1/export/all?format=${format}`
    },

    /**
     * Send extracted data to email
     * @param {string} requestId - The request ID
     * @param {string} email - Optional email address
     * @returns {Promise<any>}
     */
    sendEmail: async (requestId, email) => {
        const response = await api.post(`/requests/${requestId}/email`, { email })
        return response.data
    },
}

// Error interceptor
api.interceptors.response.use(
    (response) => response,
    (error) => {
        // Handle errors globally
        const message = error.response?.data?.message || error.message || 'An error occurred'
        console.error('API Error:', message)
        return Promise.reject(error)
    }
)

export default api
