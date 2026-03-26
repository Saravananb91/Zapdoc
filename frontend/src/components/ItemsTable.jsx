/**
 * ItemsTable Component
 * Displays invoice line items in a responsive table
 */
function ItemsTable({ items }) {
    if (!items || items.length === 0) {
        return (
            <div className="card">
                <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                    <svg className="w-5 h-5 mr-2 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Line Items
                </h2>
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                    <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                    </svg>
                    <p className="text-gray-500">No line items found</p>
                </div>
            </div>
        )
    }

    // Define all potential columns with their accessors and labels
    const allColumns = [
        { key: 'page_num', label: 'Page', render: (item) => item._page_num || item.page_num || '' },
        { key: 'item_no', label: 'Item', render: (item) => item.item_no || '' },
        { key: 'description', label: 'Description', render: (item) => item.description || '' },
        { key: 'hsn_code', label: 'HSN Code', render: (item) => item.hsn_code || '' },
        { key: 'qty', label: 'Qty', align: 'right', render: (item) => item.qty || '' },
        { key: 'unit', label: 'Unit', render: (item) => item.unit || '' },
        { key: 'rate', label: 'Rate', align: 'right', render: (item) => item.rate || item.unit_price || '' },
        { key: 'net_amount', label: 'Net Amt', align: 'right', render: (item) => item.net_amount || '' },
        { key: 'discount', label: 'Discount', align: 'right', render: (item) => item.discount || '' },
        { key: 'tax', label: 'Tax/VAT', align: 'right', render: (item) => [item.tax_amount, item.vat_rate].filter(Boolean).join(' / ') || '' },
        { key: 'total', label: 'Total', align: 'right', render: (item) => item.total || item.gross_amount || '' },
    ]

    // Determine which columns have data (exclude Page/Item/Desc from being hidden)
    const visibleColumns = allColumns.filter(col => {
        if (['page_num', 'item_no', 'description', 'total', 'qty'].includes(col.key)) return true;

        // Specific logic: Check if ANY item has a value for this column
        return items.some(item => {
            const val = col.render(item);
            return val !== '' && val !== null && val !== undefined;
        });
    });

    return (
        <div className="card">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <svg className="w-5 h-5 mr-2 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Line Items ({items.length})
            </h2>

            <div className="overflow-x-auto rounded-lg border border-gray-200">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            {visibleColumns.map(col => (
                                <th
                                    key={col.key}
                                    className={`px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider ${col.align === 'right' ? 'text-right' : 'text-left'}`}
                                >
                                    {col.label}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {items.map((item, index) => (
                            <tr key={index} className="hover:bg-gray-50 transition-colors">
                                {visibleColumns.map(col => (
                                    <td
                                        key={col.key}
                                        className={`px-4 py-3 text-sm text-gray-900 whitespace-nowrap ${col.align === 'right' ? 'text-right' : 'text-left'}`}
                                    >
                                        {col.render(item)}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

export default ItemsTable
