# ⚡ Zapdoc — AI-Powered Invoice Extraction Platform

> Extract structured invoice data from PDFs, images, and ZIP files using Google Gemini 2.5 Flash — fully automated, production-ready, and Dockerised.

![Tech Stack](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React_18-61DAFB?style=flat&logo=react&logoColor=black)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=flat&logo=mongodb&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-4285F4?style=flat&logo=google&logoColor=white)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)

---

## Overview

Zapdoc automates the digitisation of invoices at scale. Businesses handle large volumes of invoices daily — manual data entry is slow, error-prone, and expensive. Traditional OCR tools produce unstructured text that still requires human cleanup.

**Zapdoc solves this** by combining Google Gemini 2.5 Flash (a multimodal AI vision model) with structured prompt engineering and a rule-based fallback parser. Upload any invoice — the system extracts, structures, and returns the data in machine-readable formats ready for your ERP or accounting pipeline.

---

## Features

### 🔍 Core Extraction
| # | Feature | Description |
|---|---------|-------------|
| 1 | **Multi-Format Upload** | Supports PDF, PNG, JPG, JPEG, and ZIP archives |
| 2 | **AI-Powered Extraction** | Gemini 2.5 Flash vision model extracts structured invoice fields |
| 3 | **Multi-Page Support** | Handles multi-page PDFs with parallel page processing |
| 4 | **Smart Invoice Grouping** | Auto-detects and merges multi-page invoices by invoice number |
| 5 | **Dual Parser** | Auto-detects JSON vs. plain text OCR output for reliable parsing |
| 6 | **Custom Field Extraction** | Specify additional fields to extract beyond the standard schema |
| 7 | **Searchable PDF Detection** | Skips image conversion for text-based PDFs automatically |
| 8 | **ZIP Archive Processing** | Recursively processes all documents inside a ZIP file |

### 📤 Export & Downloads
| # | Feature | Description |
|---|---------|-------------|
| 9 | **JSON Export** | Structured JSON output |
| 10 | **CSV Export** | Spreadsheet-ready CSV |
| 11 | **ZIP Export** | Bundled multi-file downloads |
| 12 | **Excel Report** | Formatted `.xlsx` with header info and line items |
| 13 | **Bulk Export** | Export all extraction results at once |

### 🔐 Auth & Payments
- Supabase JWT authentication
- API Key (`X-API-KEY`) header security
- Per-user credit balance with Stripe webhook integration

### ⚡ Reliability & Performance
- Fully async backend (asyncio + Motor)
- Background worker queue with in-memory `asyncio.Queue`
- Parallel page OCR via `asyncio.Semaphore` (up to 5 concurrent pages)
- Exponential backoff retry via Tenacity (3 attempts per page)
- Partial success reporting when only some pages fail

---

## Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────┐
│                   Client Layer                      │
│              React SPA (Browser)                    │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               Reverse Proxy (Nginx)                 │
│         Serves SPA · Proxies /api → backend         │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│         Application Layer (FastAPI + Worker)        │
│      REST API · Job Queue · OCR Orchestration       │
└──────────┬───────────────────────┬──────────────────┘
           │                       │
┌──────────▼──────────┐  ┌─────────▼────────────────┐
│  AI / OCR Layer     │  │     Data Layer            │
│  Gemini 2.5 Flash   │  │  MongoDB + File Storage   │
│  + Rule-Based Parser│  │                           │
└─────────────────────┘  └───────────────────────────┘
```

### Container Architecture (Docker Compose)

| Container | Image | Port | Role |
|-----------|-------|------|------|
| `ocr_frontend` | React + Nginx | `3000 → 80` | Serves SPA, proxies API calls |
| `ocr_backend` | FastAPI + Uvicorn | `8000` | REST API, OCR orchestration, workers |
| `ocr_mongo` | MongoDB (latest) | `27017` | Document database |

### Request Lifecycle

```
1. POST /api/v1/requests          → Create request (status: CREATED)
2. POST /requests/{id}/documents  → Upload file   (status: UPLOADED)
3. POST /requests/{id}/extract    → Enqueue job   (status: QUEUED)
4. Background Worker              → Process OCR   (status: PROCESSING)
5. GET  /requests/{id}/status     → Poll status   (status: SUCCESS / PARTIAL_SUCCESS / FAILED)
6. GET  /requests/{id}/download   → Fetch results (JSON / CSV / Excel / ZIP)
```

---

## Tech Stack

### Backend
| Component | Technology | Notes |
|-----------|-----------|-------|
| Web Framework | FastAPI | Async Python, auto-generated OpenAPI docs |
| ASGI Server | Uvicorn | High-performance async server |
| Database Driver | Motor | Async MongoDB driver |
| Authentication | Supabase | JWT-based with user management |
| Payments | Stripe | Webhook-based credit top-ups |
| Email | FastAPI-Mail | SMTP email service |
| AI Model | Google Gemini 2.5 Flash | Multimodal vision + text |
| PDF Processing | PyMuPDF | Text extraction and rendering |
| Retry Logic | Tenacity | Exponential backoff (3 attempts) |
| Validation | Pydantic Settings | Type-safe config & request models |
| Excel | openpyxl | XLSX report generation |

### Frontend
| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | React | 18.2 |
| Build Tool | Vite | 5.0 |
| Styling | Tailwind CSS | 3.3 |
| HTTP Client | Axios | 1.6 |
| Routing | React Router | 6.20 |
| Notifications | React Hot Toast | 2.4 |

### Infrastructure
| Component | Technology |
|-----------|-----------|
| Containerisation | Docker |
| Orchestration | Docker Compose v3.9 |
| Reverse Proxy | Nginx |
| Database | MongoDB (latest) |

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- A [Google AI Studio](https://aistudio.google.com/) API key (Gemini 2.5 Flash)
- A [Supabase](https://supabase.com/) project (for auth)
- A [Stripe](https://stripe.com/) account (for payments, optional)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/zapdoc.git
cd zapdoc
```

### 2. Configure environment variables

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your credentials:

```env
GOOGLE_API_KEY=your_gemini_api_key
MONGO_URL=mongodb://ocr_mongo:27017
MONGO_DB=OCR_db
API_KEY=your_secure_api_key          # Change this! Never use the default in production.

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...

MAIL_USERNAME=your@email.com
MAIL_PASSWORD=your_mail_password
MAIL_SERVER=smtp.your-provider.com
```

### 3. Start all containers

```bash
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Frontend (React) | http://localhost:3000 |
| Backend (FastAPI) | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

---

## API Reference

All protected endpoints require the `X-API-KEY` header.

### Core OCR Workflow

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/requests` | Optional | Create a new extraction request |
| `POST` | `/api/v1/requests/{id}/documents` | API Key | Upload document (PDF/image/ZIP, max 20 MB) |
| `POST` | `/api/v1/requests/{id}/extract` | API Key | Trigger async extraction |
| `GET` | `/api/v1/requests/{id}/status` | API Key | Poll processing status |
| `GET` | `/api/v1/requests/{id}/extracted-data/download` | API Key | Download results (JSON/CSV/ZIP) |
| `GET` | `/api/v1/requests/{id}/download/clean` | API Key | Download clean business data only |
| `POST` | `/api/v1/requests/{id}/email` | API Key | Email results to user |

### Payments & Admin

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/payments/webhook` | Stripe Signature | Handle Stripe payment events |
| `GET` | `/api/v1/export/all` | API Key | Bulk export all extracted data |
| `GET` | `/health` | None | Health check |

### Extracted Invoice Schema

```json
{
  "invoice_no": "INV-001",
  "date_of_issue": "2024-01-15",
  "due_date": "2024-02-15",
  "seller": {
    "name": "Acme Corp",
    "address": "123 Main St",
    "tax_id": "GST123456",
    "mobile": "+1-555-0100",
    "email": "billing@acme.com",
    "iban": "GB00BARC..."
  },
  "client": { ... },
  "line_items": [
    {
      "item_no": 1,
      "description": "Consulting Services",
      "hsn_code": "998314",
      "qty": 10,
      "unit": "hrs",
      "rate": 150.00,
      "discount": 0,
      "tax_amount": 270.00,
      "vat_rate": 18,
      "net_amount": 1500.00,
      "total": 1770.00
    }
  ],
  "summary": {
    "sub_total": 1500.00,
    "cgst": 135.00,
    "sgst": 135.00,
    "net_total": 1500.00,
    "vat_total": 270.00,
    "gross_total": 1770.00
  },
  "custom_fields": {}
}
```

---

## Configuration

All settings are managed via Pydantic Settings in `backend/app/core/config.py`.

| Category | Setting | Default |
|----------|---------|---------|
| Limits | `MAX_FILE_SIZE_MB` | `20` |
| Limits | `MAX_PAGES` | `10` |
| OCR | `MAX_RETRIES` | `3` |
| OCR | `INITIAL_BACKOFF` | `1.0s` |
| OCR | `LLM_TIMEOUT` | `120s` |
| OCR | `MAX_WORKERS` | `5` |
| Security | `API_KEY_NAME` | `X-API-KEY` |
| Email | `MAIL_PORT` | `25` |

---

## Testing

The test suite lives in `backend/tests/`:

```
tests/
├── unit/                          # Individual function/module tests
├── integration/                   # End-to-end API flow tests
├── performance/                   # Throughput and latency benchmarks
├── accuracy/                      # OCR extraction accuracy validation
├── comprehensive_test_suite.py    # Full system coverage
├── conftest.py                    # pytest fixtures
└── test_data/                     # 27 sample invoice assets (PDF/images)
```

**Run the test suite:**

```bash
docker exec ocr_backend pytest backend/tests/ -v
```

---

## Project Structure

```
zapdoc/
├── backend/
│   ├── app/
│   │   ├── api/            # REST endpoints (requests, downloads, payments)
│   │   ├── ocr/            # OCR pipeline (model, parser, PDF handling)
│   │   ├── services/       # Business logic (extractor, worker, queue, email)
│   │   ├── core/           # Config, auth, security
│   │   ├── db/             # MongoDB + Supabase clients
│   │   └── utils/          # File I/O, Excel, metrics, ID generation
│   ├── tests/
│   ├── invoices/           # Uploaded invoice storage (Docker volume)
│   ├── output/             # Processed output storage (Docker volume)
│   ├── Dockerfile
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── pages/          # Dashboard, ResultPage
│   │   ├── components/     # 7 reusable components
│   │   └── services/       # api.js (Axios service layer)
│   └── Dockerfile
└── docker-compose.yml
```

---

## Roadmap

### Short-Term
- [ ] Remove commented-out legacy code from `main.py` and `extractor.py`
- [ ] Restrict CORS origins to specific frontend domain(s)
- [ ] Add startup warning if `API_KEY` is set to the default value
- [ ] Replace `print()` statements with Python's `logging` module
- [ ] Pin versions in `requirements.txt`

### Medium-Term
- [ ] Replace `asyncio.Queue` with a persistent broker (Redis / Celery / RabbitMQ)
- [ ] Add API rate limiting with `slowapi`
- [ ] Make AI model configurable via environment variables
- [ ] Implement structured logging with correlation IDs
- [ ] Add database migration support

### Long-Term
- [ ] Frontend login/register UI (Supabase Auth)
- [ ] Analytics dashboard with usage statistics
- [ ] Support for additional AI models (Azure Document Intelligence, AWS Textract)
- [ ] Webhook notifications for extraction completion
- [ ] CI/CD pipeline for automated testing and deployment

---

## Author

## Saravanan.B ##

[![Portfolio](https://img.shields.io/badge/🌐%20Portfolio-Visit%20Now-6366f1?style=for-the-badge)](https://v0-portfolio-saravanan-b.vercel.app/)

[![Email](https://img.shields.io/badge/📧%20Email%20Me-D14836?style=for-the-badge)](mailto:Mrsaravananb@gmail.com)

[![LinkedIn](https://img.shields.io/badge/🔗%20Connect-0077B5?style=for-the-badge)](https://www.linkedin.com/in/saravanan-b-46244b290)

---

## License

This project is proprietary. All rights reserved.

---

*Built with ❤️ using FastAPI · React 18 · MongoDB · Google Gemini 2.5 Flash*
