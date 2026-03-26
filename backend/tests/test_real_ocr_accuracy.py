"""
REAL OCR Accuracy Test Suite
Tests actual OCR pipeline with real invoices and ground truth data

Directory Structure Expected:
backend/tests/test_data/
├── invoices/               # Put your PDF/image files here
│   ├── invoice_001.pdf
│   ├── invoice_002.png
│   └── ...
└── ground_truth/          # Put individual JSON files here
    ├── invoice_001.json   # Same name as invoice file
    ├── invoice_002.json
    └── ...

Ground Truth JSON Format (per file):
{
  "invoice_no": "INV-2024-001",
  "date_of_issue": "2024-01-15",
  "seller_name": "ABC Corp",
  "seller_address": "123 Street",
  "client_name": "XYZ Ltd",
  "gross_total": "5250.00",
  "net_total": "5000.00",
  "vat_total": "250.00",
  "items": [
    {
      "description": "Product A",
      "qty": "10",
      "unit_price": "500.00"
    }
  ]
}
"""

import pytest
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Import your actual OCR pipeline
from app.ocr.pipeline import process_document


# ===========================
# CONFIGURATION
# ===========================

TEST_DATA_DIR = Path(__file__).parent / "test_data"
INVOICES_DIR = TEST_DATA_DIR / "invoices"
GROUND_TRUTH_DIR = TEST_DATA_DIR / "ground_truth"


# ===========================
# HELPER FUNCTIONS
# ===========================

def normalize_value(value):
    """Normalize values for comparison"""
    if value is None:
        return ""
    
    value = str(value).strip().lower()
    # Remove common formatting
    value = value.replace(",", "").replace(" ", "")
    return value


def calculate_field_accuracy(predicted: str, expected: str) -> float:
    """Calculate accuracy for a single field"""
    pred_norm = normalize_value(predicted)
    exp_norm = normalize_value(expected)
    
    if not exp_norm:
        return 1.0 if not pred_norm else 0.0
    
    if pred_norm == exp_norm:
        return 1.0
    
    # Partial credit for numeric fields
    if exp_norm.replace(".", "").replace("-", "").isdigit():
        try:
            pred_float = float(pred_norm)
            exp_float = float(exp_norm)
            error = abs(pred_float - exp_float) / exp_float if exp_float != 0 else 1.0
            return max(0.0, 1.0 - error)
        except:
            pass
    
    return 0.0


def compare_results(predicted: Dict, ground_truth: Dict) -> Dict:
    """Compare OCR results with ground truth"""
    
    results = {
        "total_fields": 0,
        "correct_fields": 0,
        "field_scores": {},
        "overall_accuracy": 0.0
    }
    
    # Key fields to compare
    key_fields = [
        "invoice_no",
        "date_of_issue", 
        "seller_name",
        "seller_address",
        "client_name",
        "gross_total",
        "net_total",
        "vat_total"
    ]
    
    for field in key_fields:
        if field in ground_truth:
            results["total_fields"] += 1
            
            pred_value = predicted.get(field, "")
            exp_value = ground_truth[field]
            
            accuracy = calculate_field_accuracy(pred_value, exp_value)
            results["field_scores"][field] = {
                "expected": exp_value,
                "predicted": pred_value,
                "accuracy": accuracy
            }
            
            if accuracy >= 0.95:  # 95% threshold for "correct"
                results["correct_fields"] += 1
    
    # Calculate overall accuracy
    if results["total_fields"] > 0:
        results["overall_accuracy"] = results["correct_fields"] / results["total_fields"]
    
    return results


def load_ground_truth(invoice_filename: str) -> Dict:
    """Load ground truth JSON for an invoice"""
    # Get base name without extension
    base_name = Path(invoice_filename).stem
    json_path = GROUND_TRUTH_DIR / f"{base_name}.json"
    
    if not json_path.exists():
        raise FileNotFoundError(f"Ground truth not found: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_test_invoices() -> List[Path]:
    """Get all invoice files from test data directory"""
    if not INVOICES_DIR.exists():
        return []
    
    valid_extensions = {'.pdf', '.png', '.jpg', '.jpeg'}
    invoices = []
    
    for file in INVOICES_DIR.iterdir():
        if file.suffix.lower() in valid_extensions:
            invoices.append(file)
    
    return sorted(invoices)


# ===========================
# PYTEST FIXTURES
# ===========================

@pytest.fixture(scope="session")
def test_invoices():
    """Get all test invoice files"""
    invoices = get_test_invoices()
    if not invoices:
        pytest.skip("No test invoices found in tests/test_data/invoices/")
    return invoices


# ===========================
# ACCURACY TESTS
# ===========================

@pytest.mark.accuracy
class TestRealOCRAccuracy:
    """Real OCR accuracy tests with ground truth comparison"""
    
    def test_invoice_count(self, test_invoices):
        """Verify test data is loaded"""
        assert len(test_invoices) > 0, "No test invoices found"
        print(f"\n✓ Found {len(test_invoices)} test invoices")
    
    @pytest.mark.parametrize("invoice_path", get_test_invoices())
    def test_individual_invoice_accuracy(self, invoice_path):
        """Test OCR accuracy for each individual invoice"""
        
        print(f"\n{'='*60}")
        print(f"Testing: {invoice_path.name}")
        print(f"{'='*60}")
        
        # Load ground truth
        try:
            ground_truth = load_ground_truth(invoice_path.name)
        except FileNotFoundError as e:
            pytest.skip(f"No ground truth for {invoice_path.name}")
        
        # Run actual OCR
        start_time = time.time()
        ocr_result = process_document(str(invoice_path))
        processing_time = time.time() - start_time
        
        # Extract data from OCR result
        # Adjust this based on your actual OCR output structure
        predicted_data = ocr_result.get("invoiceData", {})
        if "pages" in ocr_result and len(ocr_result["pages"]) > 0:
            # Try to get from first successful page
            for page in ocr_result["pages"]:
                if page.get("status") == "SUCCESS":
                    predicted_data = page.get("ocr", {}).get("structured_data", {})
                    break
        
        # Compare with ground truth
        comparison = compare_results(predicted_data, ground_truth)
        
        # Print detailed results
        print(f"\nProcessing Time: {processing_time:.2f}s")
        print(f"Status: {ocr_result.get('document_status', 'UNKNOWN')}")
        print(f"\nAccuracy: {comparison['overall_accuracy']*100:.1f}%")
        print(f"Correct Fields: {comparison['correct_fields']}/{comparison['total_fields']}")
        
        print(f"\nField-by-Field Results:")
        for field, scores in comparison['field_scores'].items():
            symbol = "✓" if scores['accuracy'] >= 0.95 else "✗"
            print(f"  {symbol} {field:20s}: {scores['accuracy']*100:5.1f}%")
            print(f"      Expected:  '{scores['expected']}'")
            print(f"      Predicted: '{scores['predicted']}'")
        
        # Assert minimum accuracy threshold
        assert comparison['overall_accuracy'] >= 0.70, \
            f"Accuracy {comparison['overall_accuracy']*100:.1f}% below 70% threshold"


@pytest.mark.accuracy  
class TestAccuracySummary:
    """Generate overall accuracy summary report"""
    
    def test_generate_accuracy_report(self, test_invoices):
        """Generate comprehensive accuracy report across all invoices"""
        
        report = {
            "test_date": datetime.now().isoformat(),
            "total_invoices": len(test_invoices),
            "results": [],
            "summary": {
                "avg_accuracy": 0.0,
                "avg_processing_time": 0.0,
                "success_rate": 0.0
            }
        }
        
        total_accuracy = 0.0
        total_time = 0.0
        successful = 0
        
        for invoice_path in test_invoices:
            try:
                # Load ground truth
                ground_truth = load_ground_truth(invoice_path.name)
                
                # Run OCR
                start = time.time()
                ocr_result = process_document(str(invoice_path))
                proc_time = time.time() - start
                
                # Get predicted data
                predicted_data = ocr_result.get("invoiceData", {})
                if "pages" in ocr_result and len(ocr_result["pages"]) > 0:
                    for page in ocr_result["pages"]:
                        if page.get("status") == "SUCCESS":
                            predicted_data = page.get("ocr", {}).get("structured_data", {})
                            break
                
                # Compare
                comparison = compare_results(predicted_data, ground_truth)
                
                invoice_report = {
                    "filename": invoice_path.name,
                    "status": ocr_result.get("document_status"),
                    "processing_time_s": round(proc_time, 2),
                    "accuracy": round(comparison['overall_accuracy'], 3),
                    "correct_fields": comparison['correct_fields'],
                    "total_fields": comparison['total_fields'],
                    "field_details": comparison['field_scores']
                }
                
                report["results"].append(invoice_report)
                
                total_accuracy += comparison['overall_accuracy']
                total_time += proc_time
                
                if ocr_result.get("document_status") == "SUCCESS":
                    successful += 1
                    
            except Exception as e:
                report["results"].append({
                    "filename": invoice_path.name,
                    "status": "ERROR",
                    "error": str(e)
                })
        
        # Calculate summary
        if len(test_invoices) > 0:
            report["summary"]["avg_accuracy"] = round(total_accuracy / len(test_invoices), 3)
            report["summary"]["avg_processing_time"] = round(total_time / len(test_invoices), 2)
            report["summary"]["success_rate"] = round(successful / len(test_invoices), 3)
        
        # Save report
        report_path = TEST_DATA_DIR / f"accuracy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"ACCURACY REPORT SUMMARY")
        print(f"{'='*60}")
        print(f"Total Invoices:        {report['total_invoices']}")
        print(f"Average Accuracy:      {report['summary']['avg_accuracy']*100:.1f}%")
        print(f"Success Rate:          {report['summary']['success_rate']*100:.1f}%")
        print(f"Avg Processing Time:   {report['summary']['avg_processing_time']:.2f}s")
        print(f"\nDetailed report saved: {report_path}")
        print(f"{'='*60}\n")
        
        # Assert overall performance
        assert report['summary']['avg_accuracy'] >= 0.75, \
            f"Overall accuracy {report['summary']['avg_accuracy']*100:.1f}% below 75% threshold"


# ===========================
# PERFORMANCE TESTS WITH REAL DATA
# ===========================

@pytest.mark.performance
class TestRealPerformance:
    """Performance tests with actual invoices"""
    
    def test_average_processing_time(self, test_invoices):
        """Measure average processing time across all invoices"""
        
        times = []
        
        for invoice_path in test_invoices[:5]:  # Test first 5
            start = time.time()
            process_document(str(invoice_path))
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"{invoice_path.name}: {elapsed:.2f}s")
        
        avg_time = sum(times) / len(times)
        print(f"\nAverage Processing Time: {avg_time:.2f}s")
        
        assert avg_time < 10.0, f"Average time {avg_time:.2f}s exceeds 10s limit"
