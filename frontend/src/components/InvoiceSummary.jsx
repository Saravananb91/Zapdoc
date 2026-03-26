/**
 * InvoiceSummary Component
 * Displays key invoice information in a clean grid layout
 */
function InvoiceSummary({ data }) {
    const fields = [
        { key: 'invoice_no', label: 'Invoice Number' },
        { key: 'date_of_issue', label: 'Date of Issue' },
        { key: 'seller_name', label: 'Seller Name' },
        { key: 'seller_address', label: 'Seller Address' },
        { key: 'seller_mobile', label: 'Seller Mobile' },
        { key: 'seller_email', label: 'Seller Email' },
        { key: 'seller_tax_id', label: 'Seller Tax ID' },
        { key: 'client_name', label: 'Client Name' },
        { key: 'client_address', label: 'Client Address' },
        { key: 'client_mobile', label: 'Client Mobile' },
        { key: 'client_email', label: 'Client Email' },
        { key: 'client_tax_id', label: 'Client Tax ID' },
        { key: 'sub_total', label: 'Sub Total' },
        { key: 'cgst', label: 'CGST' },
        { key: 'sgst', label: 'SGST' },
        { key: 'net_total', label: 'Net Total' },
        { key: 'vat_total', label: 'VAT Total' },
        { key: 'gross_total', label: 'Gross Total' },
    ]

    return (
        <div className="card">
            <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                <svg className="w-5 h-5 mr-2 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Invoice Summary
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {fields.filter(field => data?.[field.key] && data[field.key].toString().trim() !== '').map((field) => (
                    <div
                        key={field.key}
                        className="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:border-primary-300 transition-colors"
                    >
                        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                            {field.label}
                        </p>
                        <p className="text-sm font-semibold text-gray-900 break-words">
                            {data[field.key]}
                        </p>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default InvoiceSummary
