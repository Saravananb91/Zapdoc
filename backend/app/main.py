


# from fastapi import FastAPI, UploadFile, File, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# import tempfile
# import os
# import time

# from app.pipeline import process_document
# from app.schemas import OCRResponse

# # --------------------------------------------------
# # FastAPI App
# # --------------------------------------------------
# app = FastAPI(
#     title="OCR Agent API",
#     description="Production-grade OCR Agent with page-level retry support",
#     version="3.0.0"
# )

# # --------------------------------------------------
# # CORS (Frontend / External Integration)
# # --------------------------------------------------
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],   # restrict in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --------------------------------------------------
# # Health Check
# # --------------------------------------------------
# @app.get("/health")
# def health():
#     return {
#         "status": "ok",
#         "service": "ocr-agent"
#     }

# # --------------------------------------------------
# # OCR Endpoint
# # --------------------------------------------------
# @app.post("/ocr", response_model=OCRResponse)
# async def ocr_document(file: UploadFile = File(...)):
#     """
#     OCR a document (PDF/Image) with:
#     - Max 10 pages
#     - Page-level retry (max 3)
#     - Partial success support
#     - Standard JSON response
#     """

#     # -----------------------------
#     # Validate file type
#     # -----------------------------
#     if not file.filename.lower().endswith(
#         (".pdf", ".png", ".jpg", ".jpeg")
#     ):
#         raise HTTPException(
#             status_code=400,
#             detail="Unsupported file type. Upload PDF or image."
#         )

#     # -----------------------------
#     # Save uploaded file temporarily
#     # -----------------------------
#     with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
#         tmp.write(await file.read())
#         tmp_path = tmp.name

#     # -----------------------------
#     # Process document
#     # -----------------------------
#     try:
#         start = time.time()
#         result = process_document(tmp_path)
#         return result

#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"OCR processing failed: {str(e)}"
#         )

#     finally:
#         # -----------------------------
#         # Cleanup temp file
#         # -----------------------------
#         try:
#             os.remove(tmp_path)
#         except Exception:
#             pass


# from fastapi.responses import FileResponse
# import csv
# import uuid
# import tempfile

# @app.post("/ocr/csv")
# async def ocr_to_csv(file: UploadFile = File(...)):
#     # Reuse OCR pipeline
#     with tempfile.NamedTemporaryFile(delete=False) as tmp:
#         tmp.write(await file.read())
#         tmp_path = tmp.name

#     try:
#         result = process_document(tmp_path)
#         merged = result.get("merged_result", {})

#         # Create CSV
#         csv_name = f"invoice_{uuid.uuid4().hex}.csv"
#         csv_path = os.path.join(tempfile.gettempdir(), csv_name)

#         with open(csv_path, "w", newline="", encoding="utf-8") as f:
#             writer = csv.writer(f)
#             writer.writerow(["FIELD", "VALUE"])

#             for k, v in merged.items():
#                 if k != "items":
#                     writer.writerow([k, v])

#             # Items
#             writer.writerow([])
#             writer.writerow(["ITEMS"])
#             if merged.get("items"):
#                 writer.writerow(merged["items"][0].keys())
#                 for item in merged["items"]:
#                     writer.writerow(item.values())

#         return FileResponse(
#             csv_path,
#             media_type="text/csv",
#             filename="invoice_extracted.csv"
#         )

#     finally:
#         os.remove(tmp_path)


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.requests import router as requests_router
from app.api.downloads import router as downloads_router

app = FastAPI(
    title="OCR Extraction Platform",
    version="1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(requests_router)
app.include_router(downloads_router)

from app.api.payments import router as payments_router
app.include_router(payments_router)


@app.get("/health")
def health():
    return {"status": "ok"}



import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path().parent / ".env"
load_dotenv(dotenv_path=env_path)

print("ENV PATH EXISTS:", env_path.exists())
print("GOOGLE_API_KEY =", os.getenv("GOOGLE_API_KEY"))


import asyncio
from app.services.worker import page_worker

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(page_worker())


