"""
Test data generators for OCR testing framework.
Provides utilities to generate synthetic invoice data, documents, and test scenarios.
"""

import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, List
from faker import Faker

fake = Faker()


# ===========================
# Invoice Data Generators
# ===========================

def generate_invoice_number() -> str:
    """Generate random invoice number."""
    prefix = random.choice(["INV", "BILL", "RCP"])
    year = datetime.now().year
    number = random.randint(1000, 9999)
    return f"{prefix}-{year}-{number}"


def generate_invoice_date() -> str:
    """Generate random invoice date in YYYY-MM-DD format."""
    start_date = datetime.now() - timedelta(days=365)
    end_date = datetime.now()
    random_date = fake.date_between(start_date=start_date, end_date=end_date)
    return random_date.strftime("%Y-%m-%d")


def generate_vendor_name() -> str:
    """Generate random vendor/company name."""
    return fake.company()


def generate_line_item() -> Dict[str, Any]:
    """Generate single invoice line item."""
    description = fake.catch_phrase()
    quantity = random.randint(1, 10)
    unit_price = round(random.uniform(10.0, 500.0), 2)
    amount = round(quantity * unit_price, 2)
    
    return {
        "description": description,
        "quantity": quantity,
        "unit_price": unit_price,
        "amount": amount
    }


def generate_invoice_items(count: int = None) -> List[Dict[str, Any]]:
    """
    Generate multiple invoice line items.
    
    Args:
        count: Number of items to generate (random 1-5 if None)
    
    Returns:
        List of invoice items
    """
    if count is None:
        count = random.randint(1, 5)
    
    return [generate_line_item() for _ in range(count)]


def calculate_summary(items: List[Dict[str, Any]], tax_rate: float = 0.1) -> Dict[str, float]:
    """
    Calculate invoice summary from items.
    
    Args:
        items: List of invoice items
        tax_rate: Tax rate (default 10%)
    
    Returns:
        Summary dict with subtotal, tax, total
    """
    subtotal = sum(item["amount"] for item in items)
    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)
    
    return {
        "subtotal": subtotal,
        "tax": tax,
        "total": total
    }


def generate_complete_invoice(item_count: int = None) -> Dict[str, Any]:
    """
    Generate complete invoice with all fields.
    
    Args:
        item_count: Number of items (random if None)
    
    Returns:
        Complete invoice dictionary
    """
    items = generate_invoice_items(item_count)
    summary = calculate_summary(items)
    
    invoice = {
        "invoice_no": generate_invoice_number(),
        "date": generate_invoice_date(),
        "vendor": generate_vendor_name(),
        "customer": fake.name(),
        "customer_address": fake.address().replace("\n", ", "),
        "items": items,
        "summary": summary,
        "subtotal": summary["subtotal"],
        "tax": summary["tax"],
        "total": summary["total"]
    }
    
    return invoice


# ===========================
# OCR Response Generators
# ===========================

def generate_ocr_page_result(
    page_number: int,
    status: str = "SUCCESS",
    retry_count: int = 0,
    invoice_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate OCR page result.
    
    Args:
        page_number: Page number
        status: SUCCESS or FAILED
        retry_count: Number of retries
        invoice_data: Invoice data to include (generates random if None)
    
    Returns:
        OCR page result dictionary
    """
    if status == "FAILED":
        return {
            "page_number": page_number,
            "status": "FAILED",
            "retry_count": retry_count,
            "error": {
                "error_code": "OCR_FAILED",
                "message": "Page failed after retries"
            }
        }
    
    if invoice_data is None:
        invoice_data = generate_complete_invoice()
    
    # Generate raw text
    raw_text = f"""
    Invoice Number: {invoice_data['invoice_no']}
    Date: {invoice_data['date']}
    Vendor: {invoice_data['vendor']}
    
    Items:
    """
    
    for item in invoice_data.get("items", []):
        raw_text += f"\n{item['description']} - Qty: {item['quantity']} @ ${item['unit_price']} = ${item['amount']}"
    
    raw_text += f"\n\nSubtotal: ${invoice_data['subtotal']}"
    raw_text += f"\nTax: ${invoice_data['tax']}"
    raw_text += f"\nTotal: ${invoice_data['total']}"
    
    return {
        "page_number": page_number,
        "status": "SUCCESS",
        "retry_count": retry_count,
        "ocr": {
            "raw_text": raw_text.strip(),
            "structured_data": invoice_data
        }
    }


def generate_ocr_response(
    request_id: str = None,
    page_count: int = 1,
    failed_pages: List[int] = None
) -> Dict[str, Any]:
    """
    Generate complete OCR response.
    
    Args:
        request_id: Request ID (generates random if None)
        page_count: Number of pages
        failed_pages: List of page numbers that should fail
    
    Returns:
        Complete OCR response dictionary
    """
    if request_id is None:
        request_id = f"req_{''.join(random.choices(string.ascii_lowercase + string.digits, k=12))}"
    
    if failed_pages is None:
        failed_pages = []
    
    pages = []
    invoice_data = generate_complete_invoice()
    
    for page_num in range(1, page_count + 1):
        if page_num in failed_pages:
            pages.append(generate_ocr_page_result(
                page_number=page_num,
                status="FAILED",
                retry_count=10
            ))
        else:
            pages.append(generate_ocr_page_result(
                page_number=page_num,
                status="SUCCESS",
                retry_count=random.randint(0, 3),
                invoice_data=invoice_data
            ))
    
    successful_pages = page_count - len(failed_pages)
    document_status = "SUCCESS" if successful_pages == page_count else "PARTIAL_SUCCESS"
    
    return {
        "request_id": request_id,
        "status": document_status,
        "document_status": document_status,
        "processing_time_ms": random.randint(1000, 5000),
        "page_summary": {
            "total_pages": page_count,
            "successful_pages": successful_pages,
            "failed_pages": len(failed_pages)
        },
        "errors": [
            {
                "page": page_num,
                "error_code": "OCR_FAILED",
                "message": "Page failed after retries"
            }
            for page_num in failed_pages
        ],
        "pages": pages,
        "merged_result": invoice_data if successful_pages > 0 else None
    }


# ===========================
# MongoDB Document Generators
# ===========================

def generate_request_document(
    request_id: str = None,
    status: str = "PENDING"
) -> Dict[str, Any]:
    """
    Generate MongoDB request document.
    
    Args:
        request_id: Request ID (generates random if None)
        status: Request status
    
    Returns:
        Request document dictionary
    """
    if request_id is None:
        request_id = f"req_{''.join(random.choices(string.ascii_lowercase + string.digits, k=12))}"
    
    doc = {
        "_id": request_id,
        "requestId": request_id,
        "status": status,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    
    if status in ["PROCESSING", "COMPLETED", "FAILED"]:
        doc["startedAt"] = datetime.utcnow()
    
    if status in ["COMPLETED", "FAILED"]:
        doc["completedAt"] = datetime.utcnow()
    
    if status == "COMPLETED":
        doc["extractedData"] = generate_ocr_response(request_id)
        doc["confidence"] = round(random.uniform(0.8, 1.0), 2)
    
    if status == "FAILED":
        doc["error"] = "OCR processing failed"
    
    return doc


# ===========================
# Error Scenario Generators
# ===========================

def generate_corrupted_invoice() -> Dict[str, Any]:
    """Generate invoice with missing or corrupted fields."""
    invoice = generate_complete_invoice()
    
    # Randomly corrupt some fields
    corruptions = [
        lambda: invoice.pop("invoice_no", None),
        lambda: invoice.update({"date": "INVALID_DATE"}),
        lambda: invoice.update({"total": "NOT_A_NUMBER"}),
        lambda: invoice.update({"items": []}),
        lambda: invoice.pop("summary", None)
    ]
    
    # Apply 1-2 random corruptions
    for _ in range(random.randint(1, 2)):
        random.choice(corruptions)()
    
    return invoice


def generate_partial_invoice() -> Dict[str, Any]:
    """Generate invoice with only partial fields."""
    full_invoice = generate_complete_invoice()
    
    # Return only subset of fields
    return {
        "invoice_no": full_invoice["invoice_no"],
        "date": full_invoice.get("date"),
        "total": full_invoice.get("total")
    }
