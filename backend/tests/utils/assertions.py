"""
Custom assertion utilities for OCR testing.
Provides specialized assertions for OCR responses, accuracy metrics, and API responses.
"""

from typing import Dict, Any, List, Optional
import pytest


# ===========================
# OCR Response Assertions
# ===========================

def assert_ocr_response_structure(response: Dict[str, Any]):
    """
    Assert that OCR response has required structure.
    
    Args:
        response: OCR response dictionary
    
    Raises:
        AssertionError: If response structure is invalid
    """
    required_fields = [
        "request_id", "status", "processing_time_ms",
        "page_summary", "errors", "pages"
    ]
    
    for field in required_fields:
        assert field in response, f"Missing required field: {field}"
    
    # Validate page_summary
    assert "total_pages" in response["page_summary"]
    assert "successful_pages" in response["page_summary"]
    assert "failed_pages" in response["page_summary"]
    
    # Validate pages list
    assert isinstance(response["pages"], list)
    assert len(response["pages"]) == response["page_summary"]["total_pages"]
    
    # Validate each page
    for page in response["pages"]:
        assert "page_number" in page
        assert "status" in page
        assert "retry_count" in page
        
        if page["status"] == "SUCCESS":
            assert "ocr" in page
            assert "raw_text" in page["ocr"]
            assert "structured_data" in page["ocr"]
        elif page["status"] == "FAILED":
            assert "error" in page


def assert_page_result_valid(page: Dict[str, Any], expected_status: str = None):
    """
    Assert that page result is valid.
    
    Args:
        page: Page result dictionary
        expected_status: Expected status (SUCCESS/FAILED)
    """
    assert "page_number" in page
    assert "status" in page
    assert "retry_count" in page
    
    if expected_status:
        assert page["status"] == expected_status
    
    if page["status"] == "SUCCESS":
        assert "ocr" in page
        assert page["ocr"] is not None
    elif page["status"] == "FAILED":
        assert "error" in page
        assert page["error"] is not None


# ===========================
# Accuracy Assertions
# ===========================

def assert_accuracy_above_threshold(
    actual: Dict[str, Any],
    expected: Dict[str, Any],
    threshold: float,
    field: str = None
):
    """
    Assert that accuracy is above threshold.
    
    Args:
        actual: Actual OCR result
        expected: Expected ground truth
        threshold: Minimum accuracy threshold (0.0 to 1.0)
        field: Specific field to check (None for all fields)
    """
    if field:
        # Check specific field
        actual_value = actual.get(field)
        expected_value = expected.get(field)
        
        if actual_value == expected_value:
            accuracy = 1.0
        else:
            accuracy = 0.0
        
        assert accuracy >= threshold, \
            f"Field '{field}' accuracy {accuracy} below threshold {threshold}"
    else:
        # Check all fields
        total_fields = len(expected)
        matching_fields = sum(
            1 for key in expected
            if actual.get(key) == expected.get(key)
        )
        
        accuracy = matching_fields / total_fields if total_fields > 0 else 0.0
        
        assert accuracy >= threshold, \
            f"Overall accuracy {accuracy:.2%} below threshold {threshold:.2%}"


def assert_exact_match(
    actual: Any,
    expected: Any,
    field_name: str = "value"
):
    """
    Assert exact match between actual and expected values.
    
    Args:
        actual: Actual value
        expected: Expected value
        field_name: Field name for error message
    """
    assert actual == expected, \
        f"{field_name}: expected '{expected}', got '{actual}'"


def assert_numeric_tolerance(
    actual: float,
    expected: float,
    tolerance: float = 0.01,
    field_name: str = "value"
):
    """
    Assert numeric values match within tolerance.
    
    Args:
        actual: Actual numeric value
        expected: Expected numeric value
        tolerance: Absolute tolerance
        field_name: Field name for error message
    """
    diff = abs(actual - expected)
    assert diff <= tolerance, \
        f"{field_name}: expected {expected}, got {actual}, diff {diff} > tolerance {tolerance}"


def assert_items_match(
    actual_items: List[Dict[str, Any]],
    expected_items: List[Dict[str, Any]],
    min_accuracy: float = 0.8
):
    """
    Assert that line items match with minimum accuracy.
    
    Args:
        actual_items: Actual extracted items
        expected_items: Expected ground truth items
        min_accuracy: Minimum item accuracy threshold
    """
    if not expected_items:
        return
    
    assert actual_items is not None, "Actual items should not be None"
    
    # Check item count
    expected_count = len(expected_items)
    actual_count = len(actual_items)
    
    count_accuracy = min(actual_count, expected_count) / expected_count
    
    assert count_accuracy >= min_accuracy, \
        f"Item count accuracy {count_accuracy:.2%} below threshold {min_accuracy:.2%}"
    
    # Check item field matching
    if actual_count > 0 and expected_count > 0:
        # Sample check on first item
        first_actual = actual_items[0]
        first_expected = expected_items[0]
        
        # Check that at least some fields match
        matching_fields = sum(
            1 for key in first_expected
            if first_actual.get(key) == first_expected.get(key)
        )
        
        field_accuracy = matching_fields / len(first_expected)
        
        assert field_accuracy > 0, \
            "No matching fields found in line items"


# ===========================
# API Response Assertions
# ===========================

def assert_api_success(response, expected_status: int = 200):
    """
    Assert that API response indicates success.
    
    Args:
        response: HTTP response object
        expected_status: Expected status code
    """
    assert response.status_code == expected_status, \
        f"Expected status {expected_status}, got {response.status_code}: {response.text}"


def assert_api_error(response, expected_status: int, error_substring: str = None):
    """
    Assert that API response indicates expected error.
    
    Args:
        response: HTTP response object
        expected_status: Expected error status code
        error_substring: Substring to find in error message
    """
    assert response.status_code == expected_status, \
        f"Expected error status {expected_status}, got {response.status_code}"
    
    if error_substring:
        error_message = response.json().get("detail", "")
        assert error_substring.lower() in error_message.lower(), \
            f"Expected error containing '{error_substring}', got: {error_message}"


def assert_mongodb_state(
    collection,
    request_id: str,
    expected_status: str,
    additional_checks: Dict[str, Any] = None
):
    """
    Assert MongoDB document has expected state.
    
    Args:
        collection: MongoDB collection
        request_id: Request ID to check
        expected_status: Expected status field value
        additional_checks: Additional field:value pairs to check
    """
    doc = collection.find_one({"_id": request_id})
    
    assert doc is not None, f"Document {request_id} not found in database"
    assert doc["status"] == expected_status, \
        f"Expected status '{expected_status}', got '{doc['status']}'"
    
    if additional_checks:
        for field, expected_value in additional_checks.items():
            actual_value = doc.get(field)
            assert actual_value == expected_value, \
                f"Field '{field}': expected '{expected_value}', got '{actual_value}'"


# ===========================
# Timing Assertions
# ===========================

def assert_timing_within_bounds(
    actual_ms: int,
    min_ms: int = None,
    max_ms: int = None
):
    """
    Assert that timing is within expected bounds.
    
    Args:
        actual_ms: Actual time in milliseconds
        min_ms: Minimum expected time
        max_ms: Maximum expected time
    """
    if min_ms is not None:
        assert actual_ms >= min_ms, \
            f"Processing time {actual_ms}ms below minimum {min_ms}ms"
    
    if max_ms is not None:
        assert actual_ms <= max_ms, \
            f"Processing time {actual_ms}ms exceeds maximum {max_ms}ms"


def assert_retry_count_valid(retry_count: int, max_retries: int = 10):
    """
    Assert that retry count is valid.
    
    Args:
        retry_count: Actual retry count
        max_retries: Maximum allowed retries
    """
    assert 0 <= retry_count <= max_retries, \
        f"Retry count {retry_count} out of valid range [0, {max_retries}]"


# ===========================
# Queue State Assertions
# ===========================

def assert_queue_empty(queue):
    """
    Assert that async queue is empty.
    
    Args:
        queue: asyncio.Queue to check
    """
    assert queue.empty(), \
        f"Expected empty queue, but queue has {queue.qsize()} items"


def assert_queue_size(queue, expected_size: int):
    """
    Assert that queue has expected size.
    
    Args:
        queue: asyncio.Queue to check
        expected_size: Expected queue size
    """
    actual_size = queue.qsize()
    assert actual_size == expected_size, \
        f"Expected queue size {expected_size}, got {actual_size}"
