
import time
from app.ocr.pipeline_helpers import process_page, merge_pages
from app.ocr.pdf_fallback import pdf_to_images, cleanup_tmp_files
from app.ocr.pdf_text_extractor import extract_text_with_pymupdf
import asyncio
from app.core.config import settings


async def process_document(file_path: str, custom_fields: list = None) -> dict:
    start_time = time.time()
    pages = []
    page_results = []
    zip_extract_dir = None
    
    try:
        # ---------------------------
        # PAGE PREPARATION
        # ---------------------------
        if file_path.lower().endswith(".pdf"):
            text = await asyncio.to_thread(extract_text_with_pymupdf, file_path)

            if isinstance(text, str) and len(text.strip()) > 300:
                # searchable PDF -> single logical page
                pages = [file_path]
            else:
                pages = await asyncio.to_thread(pdf_to_images, file_path)
        
        elif file_path.lower().endswith(".zip"):
             # EXTRACT ZIP
             import zipfile
             import os
             import tempfile
             
             # Create temp dir for this request's extraction
             # We use the file_path's directory + _extracted suffix or similar
             zip_extract_dir = file_path + "_extracted"
             os.makedirs(zip_extract_dir, exist_ok=True)
             
             def extract_zip_sync(path, out_dir):
                 with zipfile.ZipFile(path, 'r') as zip_ref:
                     zip_ref.extractall(out_dir)
                 return [
                     os.path.join(dp, f) 
                     for dp, dn, filenames in os.walk(out_dir) 
                     for f in filenames 
                     if f.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf'))
                 ]

             extracted_files = await asyncio.to_thread(extract_zip_sync, file_path, zip_extract_dir)
             
             # Process extracted files (handle inner PDFs)
             final_pages = []
             for f in extracted_files:
                 if f.lower().endswith(".pdf"):
                      # Recursively handle PDFs inside ZIP
                      # Note: We won't recursive zip-in-zip to avoid complexity
                      text = await asyncio.to_thread(extract_text_with_pymupdf, f)
                      if isinstance(text, str) and len(text.strip()) > 300:
                           final_pages.append(f)
                      else:
                           pdf_imgs = await asyncio.to_thread(pdf_to_images, f)
                           final_pages.extend(pdf_imgs)
                 else:
                      final_pages.append(f)
             
             pages = final_pages
        
        else:
            pages = [file_path]

        page_results = []

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(settings.MAX_WORKERS)
        
        async def _process_with_limit(p, i, extra_fields):
            async with semaphore:
                return await process_page(p, i, custom_fields=extra_fields)

        # Launch all pages in parallel
        tasks = [_process_with_limit(page, idx, custom_fields) for idx, page in enumerate(pages, start=1)]
        if tasks:
            page_results = await asyncio.gather(*tasks)
        else:
            page_results = []

    finally:
        # ---------------------------
        # CLEANUP TEMP FILES
        # ---------------------------
        if file_path.lower().endswith(".pdf") and pages:
             pass
        
        # Cleanup ZIP extracted directory
        if zip_extract_dir and os.path.exists(zip_extract_dir):
            import shutil
            try:
                shutil.rmtree(zip_extract_dir, ignore_errors=True)
            except Exception:
                pass
            
            # Re-using original cleanup logic but in finally block
            # But we need to know if we should cleanup.
            # safely:
            try:
                 await asyncio.to_thread(cleanup_tmp_files, pages)
            except Exception:
                 pass

    # ---------------------------
    # STATUS COMPUTATION
    # ---------------------------
    total_pages = len(page_results)
    successful = [p for p in page_results if p["status"] == "SUCCESS"]
    failed = [p for p in page_results if p["status"] == "FAILED"]

    if len(successful) == total_pages:
        status = "SUCCESS"
    elif len(successful) > 0:
        status = "PARTIAL_SUCCESS"
    else:
        status = "FAILED"

    # ---------------------------
    # MERGE DATA
    # ---------------------------
    # merge_pages now returns a LIST of invoices (smart splitting)
    all_invoices = merge_pages(successful)
    
    # Backward compatibility: "invoice_data" is the first invoice found
    primary_invoice = all_invoices[0] if all_invoices else {}

    # ---------------------------
    # ERROR SUMMARY
    # ---------------------------
    errors = [
        {
            "page": p["page_number"],
            "error_code": p["error"]["error_code"],
            "message": p["error"]["message"]
        }
        for p in failed
    ]

    return {
        "document_status": status,
        "processing_time_ms": int((time.time() - start_time) * 1000),
        "total_pages": total_pages,
        "successful_pages": len(successful),
        "failed_pages": len(failed),
        # "confidence": round(confidence, 2),
        "errors": errors,
        "pages": page_results,
        "invoice_data": primary_invoice,
        "invoices": all_invoices # New Field
    }
