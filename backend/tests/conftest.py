"""
Test-specific fixtures and utilities.
Additional fixtures that complement the root conftest.py.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List


# ===========================
# Sample OCR Response Fixtures
# ===========================

@pytest.fixture
def sample_ocr_page_result() -> Dict[str, Any]:
    """Sample successful OCR page result."""
    return {
        "page_number": 1,
        "status": "SUCCESS",
        "retry_count": 0,
        "ocr": {
            "raw_text": "Invoice #12345\nDate: 2024-01-15\nTotal: $100.00",
            "structured_data": {
                "invoice_no": "12345",
                "date": "2024-01-15",
                "total": 100.00
            }
        }
    }


@pytest.fixture
def sample_ocr_response() -> Dict[str, Any]:
    """Sample complete OCR response."""
    return {
        "request_id": "test_req_123",
        "status": "SUCCESS",
        "processing_time_ms": 1500,
        "document_status": "SUCCESS",
        "page_summary": {
            "total_pages": 1,
            "successful_pages": 1,
            "failed_pages": 0
        },
        "errors": [],
        "pages": [
            {
                "page_number": 1,
                "status": "SUCCESS",
                "retry_count": 0,
                "ocr": {
                    "raw_text": "Invoice #12345",
                    "structured_data": {
                        "invoice_no": "12345",
                        "date": "2024-01-15",
                        "total": 100.00
                    }
                }
            }
        ],
        "merged_result": {
            "invoice_no": "12345",
            "date": "2024-01-15",
            "total": 100.00,
            "items": []
        }
    }


@pytest.fixture
def sample_failed_page_result() -> Dict[str, Any]:
    """Sample failed OCR page result."""
    return {
        "page_number": 2,
        "status": "FAILED",
        "retry_count": 10,
        "error": {
            "error_code": "OCR_FAILED",
            "message": "Page failed after max retries"
        }
    }


# ===========================
# Ground Truth Fixtures
# ===========================

@pytest.fixture
def sample_ground_truth() -> Dict[str, Any]:
    """Sample ground truth data for accuracy testing."""
    return {
        "invoice_no": "INV-2024-001",
        "date": "2024-01-15",
        "vendor": "Test Vendor Inc.",
        "total": 1250.50,
        "tax": 125.05,
        "subtotal": 1125.45,
        "items": [
            {
                "description": "Product A",
                "quantity": 2,
                "unit_price": 500.00,
                "amount": 1000.00
            },
            {
                "description": "Product B",
                "quantity": 1,
                "unit_price": 125.45,
                "amount": 125.45
            }
        ],
        "summary": {
            "subtotal": 1125.45,
            "tax": 125.05,
            "total": 1250.50
        }
    }


# ===========================
# MongoDB Document Fixtures
# ===========================

@pytest.fixture
def sample_request_document() -> Dict[str, Any]:
    """Sample MongoDB request document."""
    return {
        "_id": "req_test_001",
        "requestId": "req_test_001",
        "status": "PENDING",
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc)
    }


@pytest.fixture
def sample_completed_request() -> Dict[str, Any]:
    """Sample completed MongoDB request document."""
    return {
        "_id": "req_test_002",
        "requestId": "req_test_002",
        "status": "COMPLETED",
        "createdAt": datetime.now(timezone.utc),
        "startedAt": datetime.now(timezone.utc),
        "completedAt": datetime.now(timezone.utc),
        "extractedData": {
            "invoice_no": "12345",
            "total": 100.00
        },
        "confidence": 0.95
    }


# ===========================
# Helper Functions
# ===========================

@pytest.fixture
def create_ground_truth_file(ground_truth_dir):
    """
    Factory fixture to create ground truth JSON files.
    Usage: create_ground_truth_file("invoice_1", {...})
    """
    def _create(filename: str, data: Dict[str, Any]) -> Path:
        file_path = ground_truth_dir / f"{filename}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return file_path
    
    return _create


@pytest.fixture
def load_ground_truth_file(ground_truth_dir):
    """
    Factory fixture to load ground truth JSON files.
    Usage: load_ground_truth_file("invoice_1")
    """
    def _load(filename: str) -> Dict[str, Any]:
        file_path = ground_truth_dir / f"{filename}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Ground truth file not found: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    return _load
