
import concurrent.futures
import time
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded
load_dotenv()

# Import pipeline
try:
    from app.ocr.pipeline import process_document
    from app.ocr.config import MAX_WORKERS
except ImportError:
    # Fix python path if run from wrong dir
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from app.ocr.pipeline import process_document
    from app.ocr.config import MAX_WORKERS

IMAGES_DIR = r"C:\Users\HP Victus 16\ocr pipeline\backend\test_case\images"

def task_wrapper(file_path):
    fn = os.path.basename(file_path)
    start = time.time()
    try:
        # Simulate API request context if needed, but here we test direct pipeline
        val = process_document(file_path)
        dur = time.time() - start
        return {"file": fn, "status": val.get("document_status"), "time": dur, "error": None}
    except Exception as e:
        dur = time.time() - start
        return {"file": fn, "status": "ERROR", "time": dur, "error": str(e)}

def run_concurrency_test():
    print("="*60)
    print(f"🚀 STARTING CONCURRENCY TEST (Workers={MAX_WORKERS})")
    print("="*60)

    # Pick a subset of files to stress test (e.g., all 15 images)
    # Avoid PDFs for now if they are known timeout-prone, or include them to test fixes.
    # Let's take first 5 images for a quick concurrency check
    all_files = sorted([os.path.join(IMAGES_DIR, f) for f in os.listdir(IMAGES_DIR) if f.lower().endswith('.jpg')])
    
    # Use 10 files if available
    test_files = all_files[:10]
    
    if not test_files:
        print("No JPG files found for concurrency test.")
        return

    print(f"Queueing {len(test_files)} files...")
    
    start_global = time.time()
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_file = {executor.submit(task_wrapper, f): f for f in test_files}
        
        for future in concurrent.futures.as_completed(future_to_file):
            res = future.result()
            results.append(res)
            print(f"  Completed: {res['file']} | Status: {res['status']} | Time: {res['time']:.2f}s")
            
    end_global = time.time()
    total_time = end_global - start_global
    
    # Analysis
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    print("-" * 60)
    print(f"Total Time: {total_time:.2f}s")
    print(f"Throughput: {len(test_files) / total_time * 60:.2f} docs/min")
    print(f"Success Rate: {success_count}/{len(test_files)}")
    
    print("="*60)
    print("GATE 5 CHECK:")
    if success_count == len(test_files):
        print("✅ PASSED: All concurrent requests handled successfully.")
    else:
        print("⚠️ WARNING: Some requests failed under load.")
    print("="*60)

if __name__ == "__main__":
    run_concurrency_test()
