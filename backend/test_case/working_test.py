"""
FIXED Test Suite - Properly loads .env and tests OCR accuracy
"""
import os
import json
import time
from pathlib import Path

# CRITICAL: Load .env FIRST before importing app modules
from dotenv import load_dotenv
load_dotenv()  # This loads GOOGLE_API_KEY

print(f"✓ API Key loaded: {os.getenv('GOOGLE_API_KEY')[:20]}...")

# Now import app modules
import sys
sys.path.insert(0, r"C:\Users\HP Victus 16\ocr pipeline\backend")

from app.ocr.pipeline import process_document

IMAGES_DIR = r"C:\Users\HP Victus 16\ocr pipeline\backend\test_case\images"
GT_DIR = r"C:\Users\HP Victus 16\ocr pipeline\backend\test_case\ground_truth"

def normalize(s):
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = s.replace(",", "").replace(" ", "").replace("/", "").replace("-", "")
    return s

def load_gt_first_object(filename):
    """Load FIRST JSON object from ground truth"""
    base = Path(filename).stem
    gt_path = Path(GT_DIR) / f"{base}.json"
    
    with open(gt_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        brace_count = 0
        for i, char in enumerate(content):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return json.loads(content[:i+1])
    return {}

def calculate_accuracy(gt, pred_data):
    """Calculate accuracy - pred_data is structured_data from OCR"""
    
    total = 0
    correct = 0
    details = {}
    
    # Check invoice number
    if gt.get("invoice_number"):
        total += 1
        gt_val = normalize(gt["invoice_number"])
        pred_val = normalize(pred_data.get("invoice_no") or pred_data.get("invoice_number"))
        if gt_val == pred_val:
            correct += 1
            details["invoice_no"] = "✓"
        else:
            details["invoice_no"] = f"✗ (exp:{gt['invoice_number']}, got:{pred_data.get('invoice_no')})"
    
    # Check date
    if gt.get("date_of_issue"):
        total += 1
        gt_val = normalize(gt["date_of_issue"])
        pred_val = normalize(pred_data.get("date_of_issue"))
        if gt_val == pred_val:
            correct += 1
            details["date"] = "✓"
        else:
            details["date"] = f"✗"
    
    # Check seller
    if gt.get("seller", {}).get("name"):
        total += 1
        gt_val = normalize(gt["seller"]["name"])
        pred_val = normalize(pred_data.get("seller_name"))
        if gt_val == pred_val:
            correct += 1
            details["seller"] = "✓"
        else:
            details["seller"] = f"✗"
    
    # Check gross total
    if gt.get("summary", {}).get("gross_worth_total"):
        total += 1
        gt_val = normalize(gt["summary"]["gross_worth_total"])
        pred_val = normalize(pred_data.get("gross_total"))
        if gt_val == pred_val:
            correct += 1
            details["total"] = "✓"
        else:
            details["total"] = f"✗"
    
    accuracy = (correct / total * 100) if total > 0 else 0
    return accuracy, correct, total, details

print("="*70)
print("OCR ACCURACY TEST - WITH PROPER .ENV LOADING")
print("="*70)

results = []
processing_times = []

# Test PDFs (and some JPGs)
test_files = sorted([f for f in os.listdir(IMAGES_DIR)])[:10]  # Test first 10

for filename in test_files:
    filepath = os.path.join(IMAGES_DIR, filename)
    
    try:
        print(f"\n{'='*70}")
        print(f"Testing: {filename}")
        print('='*70)
        
        gt = load_gt_first_object(filename)
        
        start = time.time()
        ocr_result = process_document(filepath)
        proc_time = time.time() - start
        processing_times.append(proc_time)
        
        doc_status = ocr_result.get("document_status", "UNKNOWN")
        print(f"Document Status: {doc_status}")
        
        if doc_status == "FAILED":
            print(f"❌ Errors: {json.dumps(ocr_result.get('errors', []), indent=2)}")
        
        print(f"Processing Time: {proc_time:.2f}s")
        
        # Get structured data from the new top-level invoice_data field
        structured_data = ocr_result.get("invoice_data", {})
        
        if not structured_data:
            print("✗ No structured data extracted")
            results.append({
                "filename": filename,
                "status": doc_status,
                "accuracy": 0,
                "note": "No data extracted"
            })
            continue
        
        # Calculate accuracy
        accuracy, correct, total, details = calculate_accuracy(gt, structured_data)
        
        print(f"\nAccuracy: {accuracy:.1f}% ({correct}/{total})")
        print(f"Field Results:")
        for field, result in details.items():
            print(f"  {field}: {result}")
        
        results.append({
            "filename": filename,
            "status": doc_status,
            "accuracy": accuracy,
            "correct": correct,
            "total": total,
            "time_s": round(proc_time, 2),
            "details": details
        })
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        results.append({"filename": filename, "error": str(e)})

# Summary
successful = [r for r in results if "accuracy" in r and r.get("status") == "SUCCESS"]

print("\n" + "="*70)
print("FINAL RESULTS")
print("="*70)
print(f"Files Tested: {len(results)}")
print(f"Successful: {len(successful)}")

if successful:
    avg_acc = sum(r["accuracy"] for r in successful) / len(successful)
    avg_time = sum(processing_times) / len(processing_times)
    
    print(f"Average Accuracy: {avg_acc:.1f}%")
    print(f"Average Time: {avg_time:.2f}s")
    
    if avg_acc >= 85:
        print(f"\n🎉 TARGET ACHIEVED! {avg_acc:.1f}% >= 85%")
    else:
        print(f"\n⚠️  Accuracy: {avg_acc:.1f}% (target: 85%)")
    
    # Save report
    report_path = Path(GT_DIR).parent / "accuracy_report_working.json"
    with open(report_path, 'w') as f:
        json.dump({"results": results, "avg_accuracy": avg_acc}, f, indent=2)
    print(f"\nReport saved: {report_path}")
else:
    print("✗ No successful extractions")

print("="*70)
