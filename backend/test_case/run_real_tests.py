"""
REAL OCR Test Suite - 21 Invoices with Ground Truth  
Generates comprehensive accuracy report for meeting
"""
import os
import json
import time
from pathlib import Path
from app.ocr.pipeline import process_document

IMAGES_DIR = r"C:\Users\HP Victus 16\ocr pipeline\backend\test_case\images"
GT_DIR = r"C:\Users\HP Victus 16\ocr pipeline\backend\test_case\ground_truth"

def normalize(s):
    """Normalize values for comparison"""
    if s is None:
        return ""
    return str(s).strip().lower().replace(",", "").replace(" ", "")

def load_gt(filename):
    """Load first JSON object from ground truth file"""
    base = Path(filename).stem
    gt_path = Path(GT_DIR) / f"{base}.json"
    
    with open(gt_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # Handle multiple JSON objects - take first one
        # Split by '}\n{' pattern
        parts = content.strip().split('}\n{')
        if len(parts) > 1:
            first_json = parts[0] + '}'
        else:
            first_json = content
        return json.loads(first_json)

def extract_data_from_result(result):
    """Extract structured data from OCR result"""
    # Try different possible structures
    if "pages" in result and len(result["pages"]) > 0:
        for page in result["pages"]:
            if page.get("status") == "SUCCESS":
                ocr_data = page.get("ocr", {})
                return ocr_data.get("structured_data", {})
    return {}

def field_match(gt_val, pred_val):
    """Check if field matches"""
    return normalize(gt_val) == normalize(pred_val)

print("="*70)
print("REAL OCR ACCURACY TEST - 21 INVOICES")
print("="*70)

results = []
total_files = 0
processing_times = []

for filename in sorted(os.listdir(IMAGES_DIR)):
    filepath = os.path.join(IMAGES_DIR, filename)
    
    try:
        print(f"\nProcessing: {filename}")
        
        # Load ground truth
        gt = load_gt(filename)
        
        # Run actual OCR
        start = time.time()
        ocr_result = process_document(filepath)
        proc_time = time.time() - start
        processing_times.append(proc_time)
        
        # Extract predicted data  
        predicted = extract_data_from_result(ocr_result)
        
        # Compare key fields
        invoice_no_match = field_match(
            gt.get("invoice_number"), 
            predicted.get("invoice_no")
        )
        
        date_match = field_match(
            gt.get("date_of_issue"),
            predicted.get("date_of_issue")
        )
        
        seller_match = field_match(
            gt.get("seller", {}).get("name"),
            predicted.get("seller_name")
        )
        
        # Count correct fields
        fields_checked = 3
        fields_correct = sum([invoice_no_match, date_match, seller_match])
        accuracy = fields_correct / fields_checked if fields_checked > 0 else 0
        
        result_entry = {
            "filename": filename,
            "status": ocr_result.get("document_status", "UNKNOWN"),
            "processing_time": round(proc_time, 2),
            "accuracy": round(accuracy, 3),
            "fields_correct": fields_correct,
            "fields_total": fields_checked,
            "invoice_no_match": invoice_no_match,
            "date_match": date_match,
            "seller_match": seller_match,
            "gt_invoice_no": gt.get("invoice_number"),
            "pred_invoice_no": predicted.get("invoice_no"),
        }
        
        results.append(result_entry)
        total_files += 1
        
        print(f"  Status: {result_entry['status']}")
        print(f"  Time: {proc_time:.2f}s")
        print(f"  Accuracy: {accuracy*100:.1f}% ({fields_correct}/{fields_checked})")
        
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append({
            "filename": filename,
            "status": "ERROR",
            "error": str(e)
        })

# Calculate summary statistics
successful = [r for r in results if r.get("status") not in ["ERROR", "FAILED"]]
avg_accuracy = sum(r.get("accuracy", 0) for r in successful) / len(successful) if successful else 0
avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
success_rate = len(successful) / len(results) if results else 0

invoice_no_correct = sum(1 for r in successful if r.get("invoice_no_match"))
total_checked = len(successful)

print("\n" + "="*70)
print("FINAL RESULTS SUMMARY")
print("="*70)
print(f"Total Invoices Tested:    {len(results)}")
print(f"Successfully Processed:   {len(successful)} ({success_rate*100:.1f}%)")
print(f"Average Accuracy:         {avg_accuracy*100:.1f}%")
print(f"Invoice Number Accuracy:  {invoice_no_correct}/{total_checked} ({invoice_no_correct/total_checked*100:.1f}% if total_checked else 0)")
print(f"Average Processing Time:  {avg_time:.2f}s")
print(f"Min Processing Time:      {min(processing_times):.2f}s" if processing_times else "N/A")
print(f"Max Processing Time:      {max(processing_times):.2f}s" if processing_times else "N/A")
print("="*70)

# Save detailed report
report = {
    "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
    "total_invoices": len(results),
    "successful": len(successful),
    "summary": {
        "avg_accuracy": round(avg_accuracy, 3),
        "success_rate": round(success_rate, 3),
        "avg_processing_time": round(avg_time, 2),
        "invoice_no_accuracy": round(invoice_no_correct/total_checked if total_checked else 0, 3)
    },
    "detailed_results": results
}

report_path = Path(r"C:\Users\HP Victus 16\ocr pipeline\backend\test_case") / f"test_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
with open(report_path, 'w') as f:
    json.dump(report, f, indent=2)

print(f"\nDetailed report saved: {report_path}")
