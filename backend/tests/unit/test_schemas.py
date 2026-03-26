"""
Unit tests for Pydantic schemas.
Tests schema validation, serialization, and edge cases.
"""

import pytest
from pydantic import ValidationError
from app.schemas import (
    PageError,
    AggregatedError,
    OCRContent,
    OCRPageResult,
    PageSummary,
    OCRResponse
)


# ===========================
# PageError Schema Tests
# ===========================

@pytest.mark.unit
class TestPageError:
    """Tests for PageError schema."""
    
    def test_page_error_valid(self):
        """Test valid PageError creation."""
        error = PageError(
            error_code="OCR_FAILED",
            message="Failed to process page"
        )
        
        assert error.error_code == "OCR_FAILED"
        assert error.message == "Failed to process page"
    
    def test_page_error_missing_fields(self):
        """Test PageError with missing required fields."""
        with pytest.raises(ValidationError):
            PageError(error_code="OCR_FAILED")  # Missing message
    
    def test_page_error_serialization(self):
        """Test PageError serialization to dict."""
        error = PageError(
            error_code="TIMEOUT",
            message="Processing timeout"
        )
        
        data = error.model_dump()
        assert data["error_code"] == "TIMEOUT"
        assert data["message"] == "Processing timeout"


# ===========================
# AggregatedError Schema Tests
# ===========================

@pytest.mark.unit
class TestAggregatedError:
    """Tests for AggregatedError schema."""
    
    def test_aggregated_error_valid(self):
        """Test valid AggregatedError creation."""
        error = AggregatedError(
            page=2,
            error_code="OCR_FAILED",
            message="Page 2 failed"
        )
        
        assert error.page == 2
        assert error.error_code == "OCR_FAILED"
        assert error.message == "Page 2 failed"
    
    def test_aggregated_error_invalid_page(self):
        """Test AggregatedError with invalid page number."""
        # Page should be an integer
        with pytest.raises(ValidationError):
            AggregatedError(
                page="two",  # String instead of int
                error_code="ERROR",
                message="Test"
            )


# ===========================
# OCRContent Schema Tests
# ===========================

@pytest.mark.unit
class TestOCRContent:
    """Tests for OCRContent schema."""
    
    def test_ocr_content_valid(self):
        """Test valid OCRContent creation."""
        content = OCRContent(
            raw_text="Invoice #12345",
            structured_data={"invoice_no": "12345"}
        )
        
        assert content.raw_text == "Invoice #12345"
        assert content.structured_data == {"invoice_no": "12345"}
    
    def test_ocr_content_optional_fields(self):
        """Test OCRContent with optional fields as None."""
        content = OCRContent()
        
        assert content.raw_text is None
        assert content.structured_data is None
    
    def test_ocr_content_partial(self):
        """Test OCRContent with only some fields."""
        content = OCRContent(raw_text="Test text")
        
        assert content.raw_text == "Test text"
        assert content.structured_data is None


# ===========================
# OCRPageResult Schema Tests
# ===========================

@pytest.mark.unit
class TestOCRPageResult:
    """Tests for OCRPageResult schema."""
    
    def test_page_result_success(self):
        """Test successful page result."""
        page_result = OCRPageResult(
            page_number=1,
            status="SUCCESS",
            retry_count=0,
            ocr=OCRContent(
                raw_text="Test",
                structured_data={"key": "value"}
            )
        )
        
        assert page_result.page_number == 1
        assert page_result.status == "SUCCESS"
        assert page_result.retry_count == 0
        assert page_result.ocr is not None
        assert page_result.error is None
    
    def test_page_result_failed(self):
        """Test failed page result."""
        page_result = OCRPageResult(
            page_number=2,
            status="FAILED",
            retry_count=10,
            error=PageError(
                error_code="OCR_FAILED",
                message="Max retries exceeded"
            )
        )
        
        assert page_result.page_number == 2
        assert page_result.status == "FAILED"
        assert page_result.retry_count == 10
        assert page_result.error is not None
        assert page_result.ocr is None
    
    def test_page_result_missing_required_fields(self):
        """Test page result with missing required fields."""
        with pytest.raises(ValidationError):
            OCRPageResult(
                page_number=1,
                status="SUCCESS"
                # Missing retry_count
            )


# ===========================
# PageSummary Schema Tests
# ===========================

@pytest.mark.unit
class TestPageSummary:
    """Tests for PageSummary schema."""
    
    def test_page_summary_valid(self):
        """Test valid PageSummary creation."""
        summary = PageSummary(
            total_pages=5,
            successful_pages=4,
            failed_pages=1
        )
        
        assert summary.total_pages == 5
        assert summary.successful_pages == 4
        assert summary.failed_pages == 1
    
    def test_page_summary_all_success(self):
        """Test PageSummary with all pages successful."""
        summary = PageSummary(
            total_pages=3,
            successful_pages=3,
            failed_pages=0
        )
        
        assert summary.total_pages == 3
        assert summary.successful_pages == 3
        assert summary.failed_pages == 0
    
    def test_page_summary_validation(self):
        """Test PageSummary field type validation."""
        with pytest.raises(ValidationError):
            PageSummary(
                total_pages="five",  # Should be int
                successful_pages=4,
                failed_pages=1
            )


# ===========================
# OCRResponse Schema Tests
# ===========================

@pytest.mark.unit
class TestOCRResponse:
    """Tests for OCRResponse schema."""
    
    def test_ocr_response_complete(self):
        """Test complete OCR response."""
        response = OCRResponse(
            request_id="req_123",
            status="SUCCESS",
            processing_time_ms=1500,
            page_summary=PageSummary(
                total_pages=1,
                successful_pages=1,
                failed_pages=0
            ),
            errors=[],
            pages=[
                OCRPageResult(
                    page_number=1,
                    status="SUCCESS",
                    retry_count=0,
                    ocr=OCRContent(
                        raw_text="Test",
                        structured_data={"key": "value"}
                    )
                )
            ],
            merged_result={"key": "value"}
        )
        
        assert response.request_id == "req_123"
        assert response.status == "SUCCESS"
        assert response.processing_time_ms == 1500
        assert response.page_summary.total_pages == 1
        assert len(response.pages) == 1
        assert len(response.errors) == 0
        assert response.merged_result is not None
    
    def test_ocr_response_with_errors(self):
        """Test OCR response with errors."""
        response = OCRResponse(
            request_id="req_456",
            status="PARTIAL_SUCCESS",
            processing_time_ms=2000,
            page_summary=PageSummary(
                total_pages=2,
                successful_pages=1,
                failed_pages=1
            ),
            errors=[
                AggregatedError(
                    page=2,
                    error_code="OCR_FAILED",
                    message="Page 2 failed"
                )
            ],
            pages=[
                OCRPageResult(
                    page_number=1,
                    status="SUCCESS",
                    retry_count=0,
                    ocr=OCRContent(raw_text="Page 1")
                ),
                OCRPageResult(
                    page_number=2,
                    status="FAILED",
                    retry_count=10,
                    error=PageError(
                        error_code="OCR_FAILED",
                        message="Failed"
                    )
                )
            ],
            merged_result={"partial": True}
        )
        
        assert response.status == "PARTIAL_SUCCESS"
        assert len(response.errors) == 1
        assert response.page_summary.failed_pages == 1
    
    def test_ocr_response_serialization(self):
        """Test OCR response serialization."""
        response = OCRResponse(
            request_id="req_789",
            status="SUCCESS",
            processing_time_ms=1000,
            page_summary=PageSummary(
                total_pages=1,
                successful_pages=1,
                failed_pages=0
            ),
            errors=[],
            pages=[
                OCRPageResult(
                    page_number=1,
                    status="SUCCESS",
                    retry_count=0
                )
            ]
        )
        
        data = response.model_dump()
        
        assert isinstance(data, dict)
        assert data["request_id"] == "req_789"
        assert data["status"] == "SUCCESS"
        assert "page_summary" in data
        assert "pages" in data
