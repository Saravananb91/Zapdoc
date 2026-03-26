# app/services/worker.py

# from datetime import datetime
# from app.db.mongo import requests_col
# from app.ocr.pipeline import process_document

# import asyncio
# from app.services.queue import PAGE_QUEUE
# from app.services.extractor import process_page_with_retry

# async def page_worker():
#     while True:
#         task = await PAGE_QUEUE.get()

#         try:
#             await task()
#         except Exception as e:
#             print("Worker error:", e)

#         PAGE_QUEUE.task_done()

# def run_extraction_job(request_id: str, file_path: str):
#     """
#     Background OCR worker
#     """

#     try:
#         # Mark processing
#         requests_col.update_one(
#             {"_id": request_id},
#             {"$set": {
#                 "status": "PROCESSING",
#                 "startedAt": datetime.utcnow()
#             }}
#         )

#         # Run OCR pipeline
#         result = process_document(file_path)

#         # Save result
#         requests_col.update_one(
#             {"_id": request_id},
#             {"$set": {
#                 "status": result["documentStatus"],
#                 "extractedData": result,
#                 "confidence": result.get("confidence", 0),
#                 "completedAt": datetime.utcnow(),
#                 "error": None
#             }}
#         )

#     except Exception as e:
#         requests_col.update_one(
#             {"_id": request_id},
#             {"$set": {
#                 "status": "FAILED",
#                 "completedAt": datetime.utcnow(),
#                 "error": str(e)
#             }}
#         )


# app/services/worker.py
import asyncio
import traceback
from app.services.queue import PAGE_QUEUE

async def page_worker():
    """
    Background worker that continuously consumes OCR jobs
    from the async queue and executes them safely.
    """

    print("[WORKER] OCR worker started")

    while True:
        job = await PAGE_QUEUE.get()

        try:
            if asyncio.iscoroutinefunction(job):
                await job()
            else:
                raise TypeError("Queue job must be an async function")
        except Exception as e:
            print("[WORKER ERROR]", str(e))
            traceback.print_exc()
        finally:
            PAGE_QUEUE.task_done()
