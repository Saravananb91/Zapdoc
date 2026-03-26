# app/api/requests.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from datetime import datetime
import os
import asyncio
from fastapi.responses import JSONResponse
import csv
import io
import zipfile
import json
from app.utils.email import send_email_with_attachment
from pydantic import BaseModel

from app.db.mongo import requests_col
from app.services.queue import PAGE_QUEUE
from app.services.extractor import extract_document
from app.ocr.config import MAX_PAGES
from app.utils.id_generator import generate_request_id
from fastapi.responses import StreamingResponse
from fastapi import Security, Depends
from app.core.config import settings
from app.core.security import get_api_key
from app.core.auth import get_current_user
from app.services.credit_service import check_credits, deduct_credits
from app.utils.file_generator import generate_excel_report


router = APIRouter()
STORAGE_DIR = "storage"
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".zip"}


# ---------------------------
# CREATE REQUEST
# ---------------------------
from app.schemas import RequestCreate

# ---------------------------
# CREATE REQUEST
# ---------------------------
@router.post("/api/v1/requests")
async def create_request(
    body: RequestCreate = Body(
        None, 
        description="Optional user data", 
        example={"email": "user@example.com"}
    ),
):
    # This endpoint is now public to allow email capture flow
    request_id = generate_request_id()
    
    user_id = None
    user_email = None
    
    if body and body.email:
        user_email = body.email

    doc = {
        "_id": request_id,
        "user_id": user_id,
        "user_email": user_email,
        "custom_fields": body.custom_fields if body else None,
        "status": "RECEIVED",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
        "filePath": None,
        "extractedData": None,
        # "confidence": 0,
        "startedAt": None,
        "completedAt": None,
        "error": None,
    }

    await requests_col.insert_one(doc)

    return {
        "requestId": request_id,
        "status": "RECEIVED",
    }


# ---------------------------
# UPLOAD DOCUMENT
# ---------------------------
@router.post("/api/v1/requests/{requestId}/documents")
async def upload_document(
    requestId: str,
    file: UploadFile = File(...),
):
    # ---------------------------
    # SIZE LIMIT CHECK
    # ---------------------------
    # Read file to check size (and usage)
    content = await file.read()
    
    if len(content) > settings.MAX_FILE_SIZE_BYTES:
         raise HTTPException(
            413, 
            f"File too large. Max size is {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Reset cursor for writing later? No, we used `content`. 
    # We will use `content` directly.

    req = await requests_col.find_one({"_id": requestId})
    if not req:
        raise HTTPException(404, "Request not found")

    if req["status"] != "RECEIVED":
        raise HTTPException(
            400, f"Cannot upload document in status {req['status']}"
        )

    # Validate file type
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    req_dir = os.path.join(STORAGE_DIR, requestId)
    os.makedirs(req_dir, exist_ok=True)

    file_path = os.path.join(req_dir, file.filename)
    # content is already read above
    # content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    await requests_col.update_one(
        {"_id": requestId},
        {"$set": {
            "filePath": file_path,
            "status": "DOCUMENT_UPLOADED",
            "updatedAt": datetime.utcnow(),
        }},
    )

    return {
        "requestId": requestId,
        "status": "DOCUMENT_UPLOADED",
        "filePath": file_path,
    }


# ---------------------------
# TRIGGER EXTRACTION (ASYNC)
# ---------------------------
@router.post("/api/v1/requests/{requestId}/extract")
async def extract_request(requestId: str):

    req = await requests_col.find_one({"_id": requestId})
    if not req:
        raise HTTPException(404, "Request not found")

    if req["status"] != "DOCUMENT_UPLOADED":
        raise HTTPException(
            400, f"Cannot extract in status {req['status']}"
        )

    file_path = req.get("filePath")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(400, "Uploaded document not found")

    # ---------------------------
    # PAGE LIMIT CHECK (PDF)
    # ---------------------------
    # ---------------------------
    # PAGE LIMIT CHECK (PDF) & CREDITS
    # ---------------------------
    page_count = 1
    if file_path.lower().endswith(".pdf"):
        from app.ocr.pdf_fallback import pdf_to_images
        pages = await asyncio.to_thread(pdf_to_images, file_path)
        page_count = len(pages)
        if page_count > settings.MAX_PAGES:
            raise HTTPException(
                400,
                f"PDF has {page_count} pages. Max allowed is {settings.MAX_PAGES}",
            )
            
    # Check and Deduct Credits
    # We use the user_id from the request document (or current user)
    user_id = req.get("user_id")
    if user_id:
        try:
            await deduct_credits(user_id, amount=page_count)
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(500, f"Credit deduction failed: {e}")

    # ---------------------------
    # QUEUE BACKGROUND JOB
    # ---------------------------
    custom_fields = req.get("custom_fields", [])

    async def job():
        await extract_document(requestId, file_path, custom_fields=custom_fields)

    await PAGE_QUEUE.put(job)

    # mark processing immediately
    await requests_col.update_one(
        {"_id": requestId},
        {"$set": {
            "status": "PROCESSING",
            "startedAt": datetime.utcnow(),
        }},
    )

    return {
        "requestId": requestId,
        "status": "PROCESSING",
    }


# ---------------------------
# STATUS API
# ---------------------------
@router.get("/api/v1/requests/{requestId}/status")
async def get_status(requestId: str):
    req = await requests_col.find_one({"_id": requestId})
    if not req:
        raise HTTPException(404, "Request not found")

    return {
        "requestId": requestId,
        "status": req["status"],
        "startedAt": req.get("startedAt"),
        "completedAt": req.get("completedAt"),
        "error": req.get("error"),
    }


# ---------------------------
# DOWNLOAD RESULT
# ---------------------------

@router.get("/api/v1/requests/{requestId}/extracted-data/download")
async def download_result(requestId: str, format: str = "zip"):
    
    req = await requests_col.find_one({"_id": requestId})
    if not req or not req.get("extractedData"):
        raise HTTPException(404, "Result not found")

    extracted_data = req["extractedData"]
    # If the extractedData is just the invoice_data (flat), wrap it? 
    # Or handled by the fact that earlier we saw extractedData CAN be nested.
    # Actually, based on my previous fix, extractedData IS invoice_data (flat)
    # But let's handle both cases to be safe or just use the current DB state.
    # The previous code expected:
    # invoice_data = extracted_data.get("invoiceData", {})
    # But now extractedData MIGHT BE the invoiceData itself.
    
    # ADAPTATION FOR NEW DB SCHEMA (Simple Flat) vs OLD (Nested)
    if "invoice_no" in extracted_data:
        # It's the flat structure we switched to
        invoice_data = extracted_data
        page_summary = req.get("processingMetadata", {}).get("pageSummary", {})
        pages = req.get("processingMetadata", {}).get("pages", [])
    else:
        # Old structure
        invoice_data = extracted_data.get("invoiceData", {})
        page_summary = extracted_data.get("pageSummary", {})
        pages = extracted_data.get("pages", [])

    
    # Calculate processing time safely
    started_at = req.get("startedAt")
    completed_at = req.get("completedAt")
    processing_time_ms = 0
    
    if started_at and completed_at:
        try:
            # Ensure both are datetime objects
            if isinstance(started_at, str):
                started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            if isinstance(completed_at, str):
                completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                
            processing_time_ms = int((completed_at - started_at).total_seconds() * 1000)
        except Exception as e:
            print(f"Error calculating processing time: {e}")
            pass
    
    # -----------------------------
    # 1. GENERATE JSON
    # -----------------------------
    # User wants "multi pages ... like page wise"
    # So we MUST return the full structure (with pages), not just the flat invoice_data.
    # processingMetadata contains the whole pipeline result (including pages).
    full_export = req.get("processingMetadata") or extracted_data
    json_str = json.dumps(full_export, indent=2, default=str)

    if format == "json":
        return StreamingResponse(
            io.BytesIO(json_str.encode('utf-8')),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=invoice_{requestId}.json"}
        )

    # -----------------------------
    # 2. GENERATE CSV
    # ----------------------------- 
    raw_text_all_pages = []
    
    # Setup Items with Page Numbers
    # Instead of taking flat invoice_data["items"], we iterate pages to get Page No.
    items_with_page = []
    
    if pages:
        for page in pages:
            if page.get("status") == "SUCCESS":
                # Text
                raw_text = page.get("ocr", {}).get("raw_text", "")
                if raw_text:
                    raw_text_all_pages.append(f"[Page {page.get('page_number')}] {raw_text}")
                
                # Items
                structured_data = page.get("ocr", {}).get("structured_data") or {}
                p_items = structured_data.get("items") or []
                for it in p_items:
                    # Create a copy to not mutate DB object (in memory relevant)
                    it_copy = it.copy()
                    it_copy["_page_num"] = page.get("page_number")
                    items_with_page.append(it_copy)
    
    # Fallback if no pages found (e.g. pure text PDF path where pages=[] but invoiceData exists)
    if not items_with_page and invoice_data.get("items"):
        items_with_page = invoice_data.get("items", [])

    combined_raw_text = " || ".join(raw_text_all_pages)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Request ID", "Status", "Started At", "Completed At", "Processing Time (ms)",
        "Total Pages", "Successful Pages", "Failed Pages",
        "Raw OCR Text",
        "Invoice Number", "Date of Issue", 
        "Seller Name", "Seller Address", "Seller Tax ID", "Seller IBAN",
        "Client Name", "Client Address", "Client Tax ID", "Client IBAN",
        "Net Total", "VAT Total", "Gross Total", "Items Count"
    ])
    
    # Data Row
    writer.writerow([
        requestId,
        req.get("status", ""),
        started_at.isoformat() if started_at else "",
        completed_at.isoformat() if completed_at else "",
        processing_time_ms or "",
        page_summary.get("total_pages", 0),
        page_summary.get("successful_pages", 0),
        page_summary.get("failed_pages", 0),
        combined_raw_text,
        invoice_data.get("invoice_no", ""),
        invoice_data.get("date_of_issue", ""),
        invoice_data.get("seller_name", ""),
        invoice_data.get("seller_address", ""),
        invoice_data.get("seller_tax_id", ""),
        invoice_data.get("seller_iban", ""),
        invoice_data.get("client_name", ""),
        invoice_data.get("client_address", ""),
        invoice_data.get("client_tax_id", ""),
        invoice_data.get("client_iban", ""),
        invoice_data.get("net_total", ""),
        invoice_data.get("vat_total", ""),
        invoice_data.get("gross_total", ""),
        len(items_with_page)
    ])
    
    # Items
    if items_with_page:
        writer.writerow([])
        writer.writerow(["ITEMS DETAILS"])
        writer.writerow(["Page No", "Item No", "Description", "Quantity", "Unit", "Unit Price", "Net Amount", "VAT Rate (%)", "Gross Amount"])
        for item in items_with_page:
            writer.writerow([
                item.get("_page_num", "1"), # Default to 1 if missing
                item.get("item_no", ""),
                item.get("description", ""),
                item.get("qty", ""),
                item.get("unit", ""),
                item.get("unit_price", ""),
                item.get("net_amount", ""),
                item.get("vat_rate", ""),
                item.get("gross_amount", "")
            ])
            
    csv_str = output.getvalue()
    output.close()

    if format == "csv":
        return StreamingResponse(
            io.BytesIO(csv_str.encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=invoice_{requestId}.csv"}
        )

    # -----------------------------
    # 3. GENERATE EXCEL
    # -----------------------------
    if format == "xlsx":
        from app.utils.file_generator import generate_excel_report
        xlsx_path = generate_excel_report(invoice_data, pages)
        
        # Stream the file
        def iterfile():
            with open(xlsx_path, mode="rb") as file_like:
                yield from file_like
            # Clean up after streaming is a bit tricky with StreamingResponse, 
            # ideally use BackgroundTask but for now we rely on OS temp cleanup or small files.
            # Using BackgroundTask is better practice:
            os.remove(xlsx_path)

        from starlette.background import BackgroundTask
        return StreamingResponse(
            open(xlsx_path, mode="rb"),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=invoice_{requestId}.xlsx"},
            background=BackgroundTask(lambda: os.remove(xlsx_path))
        )

    # -----------------------------
    # 4. GENERATE ZIP (DEFAULT)
    # -----------------------------
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"invoice_{requestId}.json", json_str)
        zf.writestr(f"invoice_{requestId}.csv", csv_str)
        
        # Also include Excel in ZIP? Maybe not to keep it light, or yes?
        # Let's keep ZIP as just JSON+CSV for now as per "Download ZIP" expectation 
        # or add valid requirement. The user removed ZIP button, so this block is only for fallback/API.
    
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=invoice_{requestId}.zip"}
    )


# ---------------------------
# EMAIL ENDPOINT
# ---------------------------
class EmailRequest(BaseModel):
    email: str | None = None

@router.post("/api/v1/requests/{requestId}/email")
async def send_email_result(requestId: str, body: EmailRequest = Body(None)):
    """
    Generates the result files (CSV/ZIP) and emails them to the user.
    Uses the email from the request document if not provided in body.
    """
    # 1. Fetch Request
    req = await requests_col.find_one({"_id": requestId})
    if not req:
        raise HTTPException(404, "Request not found")

    # 2. Determine Email
    target_email = None
    if body and body.email:
        target_email = body.email
    elif req.get("user_email"):
        target_email = req.get("user_email")
    else:
        raise HTTPException(400, "No email provided and no email found in request")

    # 3. Reuse Download Logic to Generate Content
    # (We duplicate the logic slightly here to avoid refactoring the whole function into a helper right now, 
    #  but ideally `generate_export_data` should be a separate function.)
    
    # --- START GENERATION LOGIC ---
    extracted_data = req.get("extractedData", {})
    
    if "invoice_no" in extracted_data:
        invoice_data = extracted_data
        page_summary = req.get("processingMetadata", {}).get("pageSummary", {})
        pages = req.get("processingMetadata", {}).get("pages", [])
    else:
        invoice_data = extracted_data.get("invoiceData", {})
        page_summary = extracted_data.get("pageSummary", {})
        pages = extracted_data.get("pages", [])

    # Calculate processing time (Simplified for email)
    
    # JSON Generation (Optional - removed for email to keep it clean, or we can add it?)
    # User asked for "end excel format only", implies they want just the excel file.
    
    # --- EXCEL GENERATION LOGIC ---
    try:
        xlsx_path = generate_excel_report(invoice_data, pages)
        
        with open(xlsx_path, "rb") as f:
            attachment_bytes = f.read()
            
        attachment_filename = f"invoice_{invoice_data.get('invoice_no', requestId)}.xlsx"
        
        # Cleanup temp file
        os.remove(xlsx_path)
        
    except Exception as e:
        print(f"Error generating excel for email: {e}")
        return JSONResponse(status_code=500, content={"message": "Failed to generate Excel report"})

    # --- END GENERATION LOGIC ---

    # 4. Send Email
    subject = f"OCR Results: Invoice {invoice_data.get('invoice_no', requestId)}"
    body = f"""
Hello,

Your OCR request ({requestId}) has been processed successfully.
Please find the extracted data attached in Excel format.

Invoice: {invoice_data.get('invoice_no', 'N/A')}
Date: {invoice_data.get('date_of_issue', 'N/A')}
Total: {invoice_data.get('gross_total', 'N/A')}

Best,
OCR Agent Team
    """

    success = send_email_with_attachment(
        to_email=target_email,
        subject=subject,
        body=body,
        attachment_bytes=attachment_bytes,
        attachment_filename=attachment_filename
    )

    if not success:
        # If configured, but failed (or not configured and logged error)
        # We return 200 but with a warning in message, or just 200 if we assume it's async/fire-and-forget.
        # But user wants "fully functional", so we should probably tell them if it failed.
        return JSONResponse(
            status_code=500, 
            content={"message": "Failed to send email. Check server logs for SMTP config issues."}
        )

    return {"status": "success", "message": f"Email sent to {target_email}"}

# @router.get("/api/v1/requests/{requestId}/extracted-data/download")
# async def download_result(requestId: str):
#     req = await asyncio.to_thread(
#         requests_col.find_one, {"_id": requestId}
#     )
#     if not req or not req.get("extractedData"):
#         raise HTTPException(404, "Result not found")

#     return JSONResponse(
#         content=req["extractedData"],
#         headers={
#             "Content-Disposition": f"attachment; filename={requestId}.json"
#         },
#     )

