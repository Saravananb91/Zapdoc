"""
Field-level accuracy tests for OCR extraction.
Tests exact matching, fuzzy matching, and field-level precision.
"""

import pytest
from tests.utils.generators import generate_complete_invoice
from tests.utils.assertions import (
    assert_exact_match,
    assert_numeric_tolerance,
    assert_accuracy_above_threshold
)


# ===========================
# Exact Match Tests
# ===========================

@pytest.mark.accuracy
class TestFieldExactMatch:
    """Tests for exact field matching."""
    
    def test_invoice_number_exact_match(self):
        """Test invoice number exact match."""
        ground_truth = {"invoice_no": "INV-2024-001"}
        prediction = {"invoice_no": "INV-2024-001"}
        
        assert_exact_match(
            prediction.get("invoice_no"),
            ground_truth.get("invoice_no"),
            "invoice_no"
        )
    
    def test_date_exact_match(self):
        """Test date field exact match."""
        ground_truth = {"date": "2024-01-15"}
        prediction = {"date": "2024-01-15"}
        
        assert_exact_match(
            prediction.get("date"),
            ground_truth.get("date"),
            "date"
        )
    
    def test_vendor_exact_match(self):
        """Test vendor name exact match."""
        ground_truth = {"vendor": "Test Vendor Inc."}
        prediction = {"vendor": "Test Vendor Inc."}
        
        assert_exact_match(
            prediction.get("vendor"),
            ground_truth.get("vendor"),
            "vendor"
        )
    
    def test_field_mismatch_raises_assertion(self):
        """Test that mismatched fields raise assertion error."""
        ground_truth = {"invoice_no": "INV-001"}
        prediction = {"invoice_no": "INV-002"}
        
        with pytest.raises(AssertionError):
            assert_exact_match(
                prediction.get("invoice_no"),
                ground_truth.get("invoice_no"),
                "invoice_no"
            )


# ===========================
# Numeric Field Tests
# ===========================

@pytest.mark.accuracy
class TestNumericFieldAccuracy:
    """Tests for numeric field accuracy with tolerance."""
    
    def test_total_within_tolerance(self):
        """Test total amount within tolerance."""
        ground_truth = {"total": 1250.50}
        prediction = {"total": 1250.51}
        
        assert_numeric_tolerance(
            prediction.get("total"),
            ground_truth.get("total"),
            tolerance=0.10,
            field_name="total"
        )
    
    def test_tax_within_tolerance(self):
        """Test tax amount within tolerance."""
        ground_truth = {"tax": 125.05}
        prediction = {"tax": 125.04}
        
        assert_numeric_tolerance(
            prediction.get("tax"),
            ground_truth.get("tax"),
            tolerance=0.05,
            field_name="tax"
        )
    
    def test_subtotal_exact_match(self):
        """Test subtotal exact match (zero tolerance)."""
        ground_truth = {"subtotal": 1000.00}
        prediction = {"subtotal": 1000.00}
        
        assert_numeric_tolerance(
            prediction.get("subtotal"),
            ground_truth.get("subtotal"),
            tolerance=0.0,
            field_name="subtotal"
        )
    
    def test_numeric_outside_tolerance_fails(self):
        """Test numeric value outside tolerance fails."""
        ground_truth = {"total": 1000.00}
        prediction = {"total": 1050.00}
        
        with pytest.raises(AssertionError):
            assert_numeric_tolerance(
                prediction.get("total"),
                ground_truth.get("total"),
                tolerance=10.0,
                field_name="total"
            )


# ===========================
# Field Coverage Tests
# ===========================

@pytest.mark.accuracy
class TestFieldCoverage:
    """Tests for field extraction coverage."""
    
    def test_all_required_fields_present(self):
        """Test all required fields are extracted."""
        required_fields = ["invoice_no", "date", "total"]
        
        prediction = {
            "invoice_no": "INV-001",
            "date": "2024-01-15",
            "total": 100.00,
            "tax": 10.00
        }
        
        for field in required_fields:
            assert field in prediction, f"Required field '{field}' missing"
    
    def test_missing_field_detection(self):
        """Test detection of missing fields."""
        ground_truth = {
            "invoice_no": "INV-001",
            "date": "2024-01-15",
            "vendor": "Test Vendor"
        }
        
        prediction = {
            "invoice_no": "INV-001",
            "date": "2024-01-15"
            # Missing 'vendor'
        }
        
        missing_fields = [
            field for field in ground_truth.keys()
            if field not in prediction
        ]
        
        assert len(missing_fields) == 1
        assert "vendor" in missing_fields
    
    def test_extra_field_detection(self):
        """Test detection of extra fields not in ground truth."""
        ground_truth = {
            "invoice_no": "INV-001",
            "total": 100.00
        }
        
        prediction = {
            "invoice_no": "INV-001",
            "total": 100.00,
            "extra_field": "unexpected"
        }
        
        extra_fields = [
            field for field in prediction.keys()
            if field not in ground_truth
        ]
        
        assert len(extra_fields) == 1
        assert "extra_field" in extra_fields


# ===========================
# Overall Field Accuracy Tests
# ===========================

@pytest.mark.accuracy
class TestOverallFieldAccuracy:
    """Tests for overall field-level accuracy metrics."""
    
    def test_perfect_accuracy(self):
        """Test 100% field accuracy."""
        ground_truth = {
            "invoice_no": "INV-001",
            "date": "2024-01-15",
            "total": 100.00
        }
        
        prediction = {
            "invoice_no": "INV-001",
            "date": "2024-01-15",
            "total": 100.00
        }
        
        assert_accuracy_above_threshold(
            prediction,
            ground_truth,
            threshold=1.0
        )
    
    def test_partial_accuracy(self):
        """Test partial field accuracy."""
        ground_truth = {
            "invoice_no": "INV-001",
            "date": "2024-01-15",
            "vendor": "Test Vendor",
            "total": 100.00
        }
        
        prediction = {
            "invoice_no": "INV-001",
            "date": "2024-01-15",
            "vendor": "Wrong Vendor",  # Incorrect
            "total": 100.00
        }
        
        # 3 out of 4 fields correct = 75% accuracy
        assert_accuracy_above_threshold(
            prediction,
            ground_truth,
            threshold=0.70
        )
    
    def test_zero_accuracy(self):
        """Test zero accuracy (no matching fields)."""
        ground_truth = {
            "invoice_no": "INV-001",
            "date": "2024-01-15"
        }
        
        prediction = {
            "invoice_no": "WRONG",
            "date": "WRONG"
        }
        
        with pytest.raises(AssertionError):
            assert_accuracy_above_threshold(
                prediction,
                ground_truth,
                threshold=0.1
            )


# ===========================
# Field Type Validation Tests
# ===========================

@pytest.mark.accuracy
class TestFieldTypeValidation:
    """Tests for field type validation."""
    
    def test_numeric_field_type(self):
        """Test numeric fields are actually numbers."""
        prediction = {
            "total": 100.00,
            "tax": 10.00,
            "subtotal": 90.00
        }
        
        numeric_fields = ["total", "tax", "subtotal"]
        
        for field in numeric_fields:
            assert isinstance(prediction[field], (int, float)), \
                f"Field '{field}' should be numeric"
    
    def test_string_field_type(self):
        """Test string fields are actually strings."""
        prediction = {
            "invoice_no": "INV-001",
            "vendor": "Test Vendor",
            "date": "2024-01-15"
        }
        
        string_fields = ["invoice_no", "vendor", "date"]
        
        for field in string_fields:
            assert isinstance(prediction[field], str), \
                f"Field '{field}' should be string"
    
    def test_field_type_mismatch_detection(self):
        """Test detection of field type mismatches."""
        # Total should be numeric but is string
        prediction = {
            "total": "100.00"  # String instead of float
        }
        
        # This should fail numeric operations
        with pytest.raises(TypeError):
            _ = prediction["total"] + 10.0


# ===========================
# Case Sensitivity Tests
# ===========================

@pytest.mark.accuracy
class TestCaseSensitivity:
    """Tests for case sensitivity in field matching."""
    
    def test_case_sensitive_match(self):
        """Test case-sensitive exact match."""
        ground_truth = {"vendor": "ABC Company"}
        prediction = {"vendor": "ABC Company"}
        
        assert_exact_match(
            prediction.get("vendor"),
            ground_truth.get("vendor"),
            "vendor"
        )
    
    def test_case_mismatch_fails(self):
        """Test case mismatch causes failure."""
        ground_truth = {"vendor": "ABC Company"}
        prediction = {"vendor": "abc company"}
        
        with pytest.raises(AssertionError):
            assert_exact_match(
                prediction.get("vendor"),
                ground_truth.get("vendor"),
                "vendor"
            )
    
    def test_case_insensitive_comparison(self):
        """Test case-insensitive comparison when needed."""
        ground_truth = {"vendor": "ABC Company"}
        prediction = {"vendor": "abc company"}
        
        # Manual case-insensitive check
        assert prediction["vendor"].lower() == ground_truth["vendor"].lower()
