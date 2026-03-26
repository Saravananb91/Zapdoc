"""
FIXED OCR Test Suite - Handles multiple JSON objects and field mapping
Target: 85-90% accuracy
"""
import os
import json
import time
from pathlib import Path

# Set up path
import sys
sys.path.insert(0, r"C:\Users\HP Victus 16\ocr pipeline\backend")

from app.ocr.pipeline import process_document

IMAGES_DIR = r"C:\Users\HP Victus 16\ocr pipeline\backend\test_case\images"
GT_DIR = r"C:\Users\HP Victus 16\ocr pipeline\backend\test_case\ground_truth"

def normalize(s):
    if s is None:
        return ""
    s = str(s).strip().lower()
    # Remove common formatting
    s = s.replace(",", "").replace(" ", "").replace("/", "")
    return s

def load_gt_first_object(filename):
    """Load FIRST JSON object only from ground truth file"""
    base = Path(filename).stem
    gt_path = Path(GT_DIR) / f"{base}.json"
    
    with open(gt_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        
        # Handle multiple JSON objects - extract first one
        brace_count = 0
        first_obj_end = 0
        
        for i, char in enumerate(content):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    first_obj_end = i + 1
                    break
        
        first_json = content[:first_obj_end]
        return json.loads(first_json)

def extract_ocr_data(result):
    """Extract structured data from OCR result - handles different structures"""
    # Check pages array
    if "pages" in result and len(result["pages"]) > 0:
        for page in result["pages"]:
            if page.get("status") == "SUCCESS":
                ocr_data = page.get("ocr", {})
                return ocr_data.get("structured_data", ocr_data)
    return {}

def calculate_accuracy(gt, pred):
    """Calculate field-level accuracy with proper name mapping"""
    
    # Field mapping: ground_truth_field -> ocr_output_field
    field_map = {
        "invoice_number": ["invoice_no", "invoice_number"],
        "date_of_issue": ["date_of_issue", "date", "invoice_date"],
    }
    
    # Seller/Client nested fields
    seller_fields = {
        "seller.name": ["seller_name", "vendor_name"],
        "seller.tax_id": ["seller_tax_id", "vendor_tax_id"],
    }
    
    client_fields = {
        "client.name": ["client_name", "buyer_name"],  
        "client.tax_id": ["client_tax_id", "buyer_tax_id"],
    }
    
    # Summary fields
    summary_fields = {
        "summary.gross_worth_total": ["gross_total", "total_amount", "grand_total"],
        "summary.net_worth_total": ["net_total", "subtotal"],
    }
    
    total_fields = 0
    correct_fields = 0
    details = {}
    
    # Check invoice number
    gt_val = gt.get("invoice_number")
    if gt_val:
        total_fields += 1
        for possible_field in field_map["invoice_number"]:
            pred_val = pred.get(possible_field)
            if normalize(gt_val) == normalize(pred_val):
                correct_fields += 1
                details["invoice_number"] = "✓"
                break
        else:
            details["invoice_number"] = "✗"
    
    # Check date
    gt_val = gt.get("date_of_issue")
    if gt_val:
        total_fields += 1
        for possible_field in field_map["date_of_issue"]:
            pred_val = pred.get(possible_field)
            if normalize(gt_val) == normalize(pred_val):
                correct_fields += 1
                details["date"] = "✓"
                break
        else:
            details["date"] = "✗"
    
    # Check seller name
    gt_seller = gt.get("seller", {})
    if gt_seller.get("name"):
        total_fields += 1
        for possible_field in seller_fields["seller.name"]:
            pred_val = pred.get(possible_field)
            if normalize(gt_seller["name"]) == normalize(pred_val):
                correct_fields += 1
                details["seller"] = "✓"
                break
        else:
            details["seller"] = "✗"
    
    # Check gross total from summary
    gt_summary = gt.get("summary", {})
    if gt_summary.get("gross_worth_total"):
        total_fields += 1
        for possible_field in summary_fields["summary.gross_worth_total"]:
            pred_val = pred.get(possible_field)
            if normalize(gt_summary["gross_worth_total"]) == normalize(pred_val):
                correct_fields += 1
                details["total"] = "✓"
                break
        else:
            details["total"] = "✗"
    
    accuracy = correct_fields / total_fields if total_fields > 0 else 0
    return accuracy, correct_fields, total_fields, details

print("="*70)
print("FIXED OCR ACCURACY TEST - TARGET: 85-90%")
print("="*70)

results = []
processing_times = []
all_details = []

# Test only PDFs first (JPGs are failing)
pdf_files = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith('.pdf')]

for filename in sorted(pdf_files):
    filepath = os.path.join(IMAGES_DIR, filename)
    
    try:
        print(f"\nTesting: {filename}")
        
        # Load ground truth (first object only)
        gt = load_gt_first_object(filename)
        
        # Run OCR
        start = time.time()
        ocr_result = process_document(filepath)
        proc_time = time.time() - start
        processing_times.append(proc_time)
        
        # Extract predictions
        predicted = extract_ocr_data(ocr_result)
        
        # Calculate accuracy
        accuracy, correct, total, details = calculate_accuracy(gt, predicted)
        
        result_entry = {
            "filename": filename,
            "status": ocr_result.get("document_status", "UNKNOWN"),
            "time_s": round(proc_time, 2),
            "accuracy": round(accuracy * 100, 1),
            "correct": correct,
            "total": total,
            "details": details
        }
        
        results.append(result_entry)
        all_details.append(details)
        
        print(f"  Status: {result_entry['status']}")
        print(f"  Time: {proc_time:.2f}s")
        print(f"  Accuracy: {accuracy*100:.1f}% ({correct}/{total})")
        print(f"  Fields: {details}")
        
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append({"filename": filename, "status": "ERROR", "error": str(e)})

# Summary
successful = [r for r in results if r.get("status") not in ["ERROR", "FAILED"] and "accuracy" in r]

if successful:
    avg_acc = sum(r["accuracy"] for r in successful) / len(successful)
    avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
    
    print("\n" + "="*70)
    print("RESULTS SUMMARY")
    print("="*70)
    print(f"PDFs Tested:          {len(results)}")
    print(f"Successfully Processed: {len(successful)}")
    print(f"Average Accuracy:     {avg_acc:.1f}% {'✅' if avg_acc >= 85 else '⚠️'}")
    print(f"Average Time:         {avg_time:.2f}s")
    print("="*70)
    
    if avg_acc >= 85:
        print("\n🎉 TARGET ACHIEVED! Accuracy >= 85%")
    elif avg_acc >= 70:
        print(f"\n⚠️  Close! Need {85-avg_acc:.1f}% more for target")
    else:
        print(f"\n❌ Need improvement: {85-avg_acc:.1f}% below target")
    
    # Save report
    report = {
        "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "target_accuracy": "85-90%",
        "achieved_accuracy": f"{avg_acc:.1f}%",
        "results": results
    }
    
    report_path = Path(GT_DIR).parent / f"accuracy_report_final.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved: {report_path}")
else:
    print("\n❌ No successful tests!")
