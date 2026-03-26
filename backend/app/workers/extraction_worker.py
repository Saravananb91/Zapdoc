# from concurrent.futures import ThreadPoolExecutor
# from app.ocr.pipeline import process_document
# from app.db.mongo import requests_col
# from datetime import datetime

# executor = ThreadPoolExecutor(max_workers=5)  


# def run_extraction_async(request_id: str, file_path: str):
#     future = executor.submit(process_document, file_path)

#     def callback(f):
#         result = f.result()
#         requests_col.update_one(
#             {"_id": request_id},
#             {"$set": {
#                 "status": result["documentStatus"],
#                 "extractedData": result,
#                 "completedAt": datetime.utcnow()
#             }}
#         )

#     future.add_done_callback(callback)


import threading
from app.services.extractor import extract_document


def start_extraction_thread(request_id: str, file_path: str):
    t = threading.Thread(
        target=extract_document,
        args=(request_id, file_path),
        daemon=True
    )
    t.start()

