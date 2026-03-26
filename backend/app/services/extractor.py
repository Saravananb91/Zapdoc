# import asyncio
# from datetime import datetime, timezone,time
# from app.db.mongo import requests_col, documents_col
# from app.ocr.pipeline import run_ocr_pipeline


# def compute_overall_confidence(pages):
#     scores = [
#         p["confidence_score"]
#         for p in pages
#         if p.get("status") == "SUCCESS"
#     ]
#     return round(sum(scores) / len(scores), 2) if scores else 0.0


# async def process_extraction(request_id: str):
#     try:
#         document = await documents_col.find_one({"requestId": request_id})
#         if not document:
#             raise Exception("Document not found")

#         file_path = document["docLocation"]

#         # 🧠 Run OCR safely
#         result = await asyncio.to_thread(run_ocr_pipeline, file_path)

#         if not result:
#             raise Exception("OCR pipeline returned None")

#         pages = result.get("pages", [])
#         merged = result.get("merged_result", {})

#         confidence = compute_overall_confidence(pages)

#         extracted_payload = {
#             "documentStatus": result.get("status"),
#             "processingTimeMs": result.get("processing_time_ms"),
#             "pageSummary": result.get("page_summary"),
#             "invoiceData": merged,
#             "pages": pages,
#             "errors": result.get("errors", [])
#         }

#         await requests_col.update_one(
#             {"_id": request_id},
#             {"$set": {
#                 "status": "COMPLETED",
#                 "completedAt": datetime.now(timezone.utc),
#                 "confidence": confidence,
#                 "extractedData": extracted_payload
#             }}
#         )

#     except Exception as e:
#         await requests_col.update_one(
#             {"_id": request_id},
#             {"$set": {
#                 "status": "FAILED",
#                 "error": str(e),
#                 "completedAt": datetime.now(timezone.utc)
#             }}
#         )
        
        
# from app.ocr.pipeline import run_single_page_ocr
# from app.ocr.parser_utils import parse_invoice_text_to_struct

# MAX_RETRIES = 3
# INITIAL_BACKOFF = 1.5
# CONFIDENCE_THRESHOLD = 0.6

# import time

# async def process_page_with_retry(page_path, page_number):
#     retries = 0

#     while retries < MAX_RETRIES:
#         try:
#             text = run_single_page_ocr(page_path)
#             parsed = parse_invoice_text_to_struct(text)

#             return {
#                 "page_number": page_number,
#                 "status": "SUCCESS",
#                 "retry_count": retries,
#                 "ocr": {
#                     "raw_text": text,
#                     "structured_data": parsed
#                 }
#             }

#         except Exception:
#             retries += 1
#             time.sleep(INITIAL_BACKOFF * (2 ** retries))

#     return {
#         "page_number": page_number,
#         "status": "FAILED",
#         "retry_count": retries,
#         "error": "Page failed after retries"
#     }


# # async def process_page_with_retry(page_path: str, page_no: int):
#     retries = 0

#     while retries < MAX_PAGE_RETRIES:
#         try:
#             result = run_single_page_ocr(page_path)

#             if result["confidence"] < CONFIDENCE_THRESHOLD:
#                 raise ValueError("LOW_CONFIDENCE")

#             return {
#                 "page_number": page_no,
#                 "status": "SUCCESS",
#                 "retry_count": retries,
#                 "confidence": result["confidence"],
#                 "ocr": result
#             }

#         except Exception:
#             retries += 1
#             time.sleep(INITIAL_BACKOFF * (2 ** retries))

#     return {
#         "page_number": page_no,
#         "status": "FAILED",
#         "retry_count": retries,
#         "confidence": 0,
#         "error": "Page failed after retries"
#     }



# from datetime import datetime
# from app.db.mongo import requests_col
# from app.ocr.pipeline import process_document


# def extract_document(request_id: str, file_path: str):
#     try:
#         requests_col.update_one(
#             {"_id": request_id},
#             {"$set": {"status": "PROCESSING", "startedAt": datetime.utcnow()}}
#         )

#         result = process_document(file_path)

#         requests_col.update_one(
#             {"_id": request_id},
#             {"$set": {
#                 "status": "COMPLETED",
#                 "extractedData": result,
#                 "confidence": 1 if result["documentStatus"] == "SUCCESS" else 0,
#                 "completedAt": datetime.utcnow()
#             }}
#         )

#     except Exception as e:
#         requests_col.update_one(
#             {"_id": request_id},
#             {"$set": {
#                 "status": "FAILED",
#                 "error": str(e),
#                 "completedAt": datetime.utcnow()
#             }}
#         )




# app/services/extractor.py
from datetime import datetime
from app.db.mongo import requests_col
from app.ocr.pipeline import process_document
from app.services.email_service import send_extraction_email
from app.utils.file_generator import generate_excel_report
from app.services.analytics import log_analytics_event
from pathlib import Path
import os


async def extract_document(request_id: str, file_path: str, custom_fields: list = None):
    try:
        # ---------------------------
        # MARK PROCESSING
        # ---------------------------
        await requests_col.update_one(
            {"_id": request_id},
            {"$set": {
                "status": "PROCESSING",
                "startedAt": datetime.utcnow()
            }}
        )

        # ---------------------------
        # RUN OCR PIPELINE
        # ---------------------------
        result = await process_document(file_path, custom_fields=custom_fields)

        # ---------------------------
        # FINAL DB UPDATE
        # ---------------------------
        await requests_col.update_one(
            {"_id": request_id},
            {"$set": {
                "status": result["document_status"],
                "completedAt": datetime.utcnow(),
                # "confidence": result["confidence"],
                "extractedData": result.get("invoice_data"),
                "processingMetadata": result,
                "error": None
            }}
        )

        # ---------------------------
        # SEND EMAIL
        # ---------------------------
        try:
            req = await requests_col.find_one({"_id": request_id})
            user_email = req.get("user_email")
            user_id = req.get("user_id")
            
            # Log Analytics
            if user_id:
                await log_analytics_event(
                    event_type="document_processed",
                    user_id=user_id,
                    metadata={
                        "request_id": request_id,
                        "status": result["document_status"],
                        "file_path": file_path
                    }
                )
            
            if user_email and result["document_status"] == "SUCCESS":
                excel_path = generate_excel_report(result.get("invoice_data", {}), result.get("pages", []))
                await send_extraction_email(user_email, [Path(excel_path)], request_id)
                
                # Cleanup
                if os.path.exists(excel_path):
                    os.remove(excel_path)
                    
        except Exception as email_error:
            print(f"Failed to send email or log analytics for {request_id}: {email_error}")

    except Exception as e:
        await requests_col.update_one(
            {"_id": request_id},
            {"$set": {
                "status": "FAILED",
                "completedAt": datetime.utcnow(),
                "error": str(e)
            }}
        )
