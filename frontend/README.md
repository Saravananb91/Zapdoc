# OCR Invoice Processing - React Frontend

A modern, responsive React frontend for the OCR Invoice Processing Agent. Built with React 18, Vite, Tailwind CSS, and Axios.

## Features

✨ **Modern UI/UX**
- Clean, professional invoice-style interface
- Responsive design (mobile to desktop)
- Dark-to-light gradient theme
- Smooth animations and transitions

🔍 **Search & Process**
- Search existing requests by Request ID
- Create new OCR requests
- Drag & drop file upload
- Real-time processing status

📊 **Results Display**
- Invoice summary with key fields
- Line items table with page numbers
- Download options (JSON, CSV, ZIP)
- Support for multi-page PDFs

🎯 **Developer Experience**
- Component-based architecture
- API service layer
- Toast notifications
- Error handling throughout

## Tech Stack

- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Routing**: React Router v6
- **Notifications**: React Hot Toast

## Prerequisites

- Node.js 16+ and npm
- Backend API running on `http://localhost:8000`

## Installation

1. **Install dependencies**:
   ```bash
   cd "c:\Users\HP Victus 16\ocr pipeline\frontend_react"
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Open in browser**:
   ```
   http://localhost:3000
   ```

## Project Structure

```
frontend_react/
├── src/
│   ├── components/          # Reusable components
│   │   ├── RequestSearch.jsx      # Search by Request ID
│   │   ├── CreateRequest.jsx      # Create new request
│   │   ├── FileUpload.jsx         # File upload with drag & drop
│   │   ├── ProcessingStatus.jsx   # Status polling & progress
│   │   ├── InvoiceSummary.jsx     # Invoice fields display
│   │   ├── ItemsTable.jsx         # Line items table
│   │   └── DownloadActions.jsx    # Download buttons
│   ├── pages/               # Main pages
│   │   ├── Dashboard.jsx          # Main workflow page
│   │   └── ResultPage.jsx         # Results display
│   ├── services/            # API layer
│   │   └── api.js                 # Axios instance & methods
│   ├── App.jsx              # Main app with routing
│   ├── main.jsx             # React entry point
│   └── index.css            # Tailwind & global styles
├── index.html
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## Usage

### 1. Process New Invoice

1. Click **"Create New Request"** on the dashboard
2. A Request ID will be generated
3. Upload your invoice (PDF, JPG, PNG, JPEG)
4. Click **"Upload File"**
5. Processing will start automatically
6. Wait for completion (10-30 seconds)
7. View results automatically

### 2. Search Existing Request

1. Enter a **Request ID** in the search box
2. Click **"Search"**
3. View the results if the request exists

### 3. Download Results

On the result page, choose from:
- **Download JSON** - Full extraction data
- **Download CSV** - Tabular format
- **Download ZIP** - Package with all formats

## API Configuration

The frontend expects the backend API at:
```
http://localhost:8000/api/v1
```

To change this, edit `src/services/api.js`:
```javascript
const api = axios.create({
  baseURL: '/api/v1',  // Proxied through Vite
  // or use direct URL:
  // baseURL: 'http://your-backend-url/api/v1',
})
```

## Build for Production

```bash
npm run build
```

Output will be in the `dist/` folder.

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

### Component Documentation

All components include JSDoc comments. Key components:

- **RequestSearch**: Search functionality with error handling
- **CreateRequest**: Request ID generation and display
- **FileUpload**: Drag & drop with validation (PDF/JPG/PNG, max 50MB)
- **ProcessingStatus**: Real-time status polling (2s interval)
- **InvoiceSummary**: Responsive grid of invoice fields
- **ItemsTable**: Scrollable table with page numbers
- **DownloadActions**: Download triggers for all formats

### API Methods

See `src/services/api.js` for all available methods:
- `createRequest()` - Create new OCR request
- `uploadFile(requestId, file)` - Upload document
- `processInvoice(requestId)` - Trigger extraction
- `getRequestStatus(requestId)` - Poll status
- `getExtractedData(requestId)` - Fetch results
- `downloadResult(requestId, format)` - Get download URL

## Styling

Uses Tailwind CSS with custom design tokens:

```css
/* Custom button classes */
.btn-primary  - Primary gradient button
.btn-secondary - Secondary outlined button

/* Custom components */
.card - White card with shadow
.input-field - Styled input with focus ring
```

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Troubleshooting

**Issue**: "Cannot GET /api/v1/requests"
- **Solution**: Ensure backend is running on port 8000

**Issue**: CORS errors
- **Solution**: Backend should allow origin `http://localhost:3000`

**Issue**: File upload fails
- **Solution**: Check file type (PDF/JPG/PNG) and size (<50MB)

## License

MIT

## Support

For issues or questions, please contact the development team.
