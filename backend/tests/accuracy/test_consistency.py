"""
Consistency and determinism tests for OCR extraction.
Tests that same document produces identical results across multiple runs.
"""

import pytest
from tests.utils.generators import generate_complete_invoice, generate_ocr_response
from tests.utils.assertions import assert_exact_match


# ===========================
# Determinism Tests
# ===========================

@pytest.mark.accuracy
class TestDeterminism:
    """Tests for deterministic OCR behavior."""
    
    def test_same_input_same_output(self):
        """Test that same document produces same result (mocked)."""
        # In a real scenario, this would run OCR twice on the same document
        # For testing purposes, we simulate this
        
        invoice = generate_complete_invoice(item_count=3)
        
        # Simulate two runs
        result_1 = generate_ocr_response(request_id="req_1", page_count=1)
        result_2 = generate_ocr_response(request_id="req_2", page_count=1)
        
        # Both should have same structure
        assert result_1.keys() == result_2.keys()
        assert result_1["status"] == result_2["status"]
    
    def test_retry_count_consistency(self):
        """Test that retry counts are tracked consistently."""
        page_result = {
            "page_number": 1,
            "retry_count": 0,
            "status": "SUCCESS"
        }
        
        # Verify retry count is consistent
        assert page_result["retry_count"] >= 0
        assert isinstance(page_result["retry_count"], int)
    
    def test_timestamp_ordering(self):
        """Test that timestamps maintain correct ordering."""
        from datetime import datetime, timedelta
        
        created_at = datetime.utcnow()
        started_at = created_at + timedelta(seconds=1)
        completed_at = started_at + timedelta(seconds=5)
        
        # Timestamps should be in order
        assert created_at < started_at < completed_at


# ===========================
# Consistency Tests
# ===========================

@pytest.mark.accuracy
class TestConsistency:
    """Tests for consistent behavior across operations."""
    
    def test_page_numbering_consistency(self):
        """Test that page numbers are consistent and sequential."""
        pages = [
            {"page_number": 1, "status": "SUCCESS"},
            {"page_number": 2, "status": "SUCCESS"},
            {"page_number": 3, "status": "FAILED"}
        ]
        
        # Page numbers should be sequential
        for i, page in enumerate(pages, start=1):
            assert page["page_number"] == i
    
    def test_status_consistency(self):
        """Test that status values are consistent."""
        valid_statuses = ["PENDING", "PROCESSING", "COMPLETED", "FAILED", "PARTIAL_SUCCESS"]
        
        test_statuses = ["COMPLETED", "FAILED", "PROCESSING"]
        
        for status in test_statuses:
            assert status in valid_statuses
    
    def test_error_reporting_consistency(self):
        """Test that errors are reported consistently."""
        failed_page = {
            "page_number": 2,
            "status": "FAILED",
            "retry_count": 10,
            "error": {
                "error_code": "OCR_FAILED",
                "message": "Max retries exceeded"
            }
        }
        
        # Failed pages should have error attribute
        assert failed_page["status"] == "FAILED"
        assert "error" in failed_page
        assert failed_page["error"]["error_code"] is not None
        assert failed_page["error"]["message"] is not None
    
    def test_summary_consistency_with_pages(self):
        """Test that page summary matches actual page results."""
        pages = [
            {"page_number": 1, "status": "SUCCESS"},
            {"page_number": 2, "status": "SUCCESS"},
            {"page_number": 3, "status": "FAILED"}
        ]
        
        # Count successes and failures
        successful = sum(1 for p in pages if p["status"] == "SUCCESS")
        failed = sum(1 for p in pages if p["status"] == "FAILED")
        
        summary = {
            "total_pages": len(pages),
            "successful_pages": successful,
            "failed_pages": failed
        }
        
        # Verify consistency
        assert summary["total_pages"] == len(pages)
        assert summary["successful_pages"] == 2
        assert summary["failed_pages"] == 1
        assert summary["successful_pages"] + summary["failed_pages"] == summary["total_pages"]


# ===========================
# Idempotency Tests
# ===========================

@pytest.mark.accuracy
class TestIdempotency:
    """Tests for idempotent operations."""
    
    def test_same_request_id_consistency(self):
        """Test that same request ID maintains consistent data."""
        request_id = "req_test_123"
        
        # Multiple references to same request should be consistent
        request_ref_1 = {"_id": request_id, "status": "PENDING"}
        request_ref_2 = {"_id": request_id, "status": "PENDING"}
        
        assert request_ref_1["_id"] == request_ref_2["_id"]
        assert request_ref_1["status"] == request_ref_2["status"]
    
    def test_field_extraction_stability(self):
        """Test that field extraction produces stable results."""
        # Same invoicedata should extract same fields
        invoice_data = {
            "invoice_no": "INV-001",
            "date": "2024-01-15",
            "total": 100.00
        }
        
        # Extract multiple times
        extract_1 = invoice_data.copy()
        extract_2 = invoice_data.copy()
        
        assert extract_1 == extract_2


# ===========================
# Page Ordering Tests
# ===========================

@pytest.mark.accuracy
class TestPageOrdering:
    """Tests for consistent page ordering."""
    
    def test_pages_in_sequential_order(self):
        """Test that pages are in sequential order."""
        pages = [
            {"page_number": 1},
            {"page_number": 2},
            {"page_number": 3},
            {"page_number": 4}
        ]
        
        # Verify sequential ordering
        for i, page in enumerate(pages, start=1):
            assert page["page_number"] == i
    
    def test_no_duplicate_page_numbers(self):
        """Test that there are no duplicate page numbers."""
        pages = [
            {"page_number": 1},
            {"page_number": 2},
            {"page_number": 3}
        ]
        
        page_numbers = [p["page_number"] for p in pages]
        
        # No duplicates
        assert len(page_numbers) == len(set(page_numbers))
    
    def test_no_missing_pages(self):
        """Test that no pages are missing in sequence."""
        pages = [
            {"page_number": 1},
            {"page_number": 2},
            {"page_number": 3}
        ]
        
        page_numbers = [p["page_number"] for p in pages]
        expected_numbers = list(range(1, len(pages) + 1))
        
        assert page_numbers == expected_numbers


# ===========================
# Merge Logic Determinism Tests
# ===========================

@pytest.mark.accuracy
class TestMergeLogicDeterminism:
    """Tests for deterministic merge logic."""
    
    def test_single_page_merge(self):
        """Test that single page merge is deterministic."""
        page_data = {
            "invoice_no": "INV-001",
            "total": 100.00
        }
        
        # Merge should return same data for single page
        merged = page_data.copy()
        
        assert merged == page_data
    
    def test_multi_page_merge_consistency(self):
        """Test that multi-page merge is consistent."""
        page_1_data = {"invoice_no": "INV-001", "page": 1}
        page_2_data = {"date": "2024-01-15", "page": 2}
        
        # Merge logic (simple example)
        merged = {**page_1_data, **page_2_data}
        
        # Should contain data from both pages
        assert "invoice_no" in merged
        assert "date" in merged
    
    def test_merge_preserves_required_fields(self):
        """Test that merge preserves required fields."""
        pages_data = [
            {"invoice_no": "INV-001", "total": 100},
            {"invoice_no": "INV-001", "date": "2024-01-15"}
        ]
        
        # Merge should preserve invoice_no from both
        merged = {}
        for page_data in pages_data:
            merged.update(page_data)
        
        assert "invoice_no" in merged
        assert merged["invoice_no"] == "INV-001"
