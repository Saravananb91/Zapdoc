
import time
from app.ocr.model_utils import ocr_once
from app.ocr.parser_utils import parse_invoice_text_to_struct
from app.ocr.config import MAX_RETRIES, INITIAL_BACKOFF
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


async def process_page(image_path: str, page_number: int) -> dict:
    """
    Process a single page using ONLY rule-based parsing.
    
    NO LLM dependencies.
    NO confidence gating.
    Returns structured data or error after retries.
    """
    
@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=INITIAL_BACKOFF, min=1, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
async def _extract_and_parse(image_path: str, custom_fields: list = None):
    # Step 1: Extract text from image using OCR (Async wrapper)
    text = await asyncio.to_thread(ocr_once, image_path, custom_fields)

    # Step 2: Validate we got meaningful text
    if not text or len(text.strip()) < 20:
        raise ValueError("EMPTY_OCR_TEXT")

    # Step 3: Parse text to structured data using RULES ONLY
    return parse_invoice_text_to_struct(text), text


async def process_page(image_path: str, page_number: int, custom_fields: list = None) -> dict:
    """
    Process a single page using ONLY rule-based parsing.
    NO LLM dependencies (except OCR).
    Returns structured data or error after retries.
    """
    try:
        structured, raw_text = await _extract_and_parse(image_path, custom_fields)
        
        return {
            "page_number": page_number,
            "status": "SUCCESS",
            "retry_count": 0, # Tenacity hides the count by default, but we assume success if we got here
            "ocr": {
                "raw_text": raw_text,
                "structured_data": structured
            },
            "warnings": []
        }

    except Exception as e:
        return {
            "page_number": page_number,
            "status": "FAILED",
            "retry_count": MAX_RETRIES,
            "error": {
                "error_code": str(e),
                "message": "Page failed after retries"
            }
        }


def group_pages_by_invoice(pages: list) -> list:
    """
    Group pages into sub-lists, where each sub-list is one distinct invoice.
    Heuristic: Start new group if a page has a distinct 'invoice_no' field found.
    """
    groups = []
    current_group = []
    current_invoice_no = None

    for page in pages:
        data = page.get("ocr", {}).get("structured_data", {})
        if not data and "structured_data" in page:
             data = page["structured_data"]
        
        inv_no = data.get("invoice_no")
        # DEBUG LOGGING
        with open("detailed_debug.log", "a") as logf:
            logf.write(f"DEBUG: Page {page.get('page_number')} Inv No: {inv_no}\n")
        
        inv_no_norm = str(inv_no).strip().lower() if inv_no else None
        curr_inv_norm = str(current_invoice_no).strip().lower() if current_invoice_no else None

        # Logic: If we find a specific Invoice No that differs from the running context, split.
        # But be careful of pages that have NO invoice number (extensions).
        is_new_invoice = False
        
        if inv_no_norm:
            if not current_group:
                # First page of first group
                is_new_invoice = False
                current_invoice_no = inv_no
            elif current_invoice_no and inv_no_norm != curr_inv_norm:
                # Detected DIFFERENT invoice number
                is_new_invoice = True
            elif not current_invoice_no:
                 # Group started without number, now found one. Is it new? 
                 # Assume same invoice if it's the first time we see a number.
                 current_invoice_no = inv_no

        if is_new_invoice:
            groups.append(current_group)
            current_group = [page]
            current_invoice_no = inv_no
        else:
            current_group.append(page)

    if current_group:
        groups.append(current_group)
        
    return groups


def merge_pages(success_pages: list) -> list:
    """
    Merge pages intelligently.
    Returns A LIST of merged invoice objects (dicts).
    """
    
    # 1. Group pages by invoice number
    groups = group_pages_by_invoice(success_pages)
    
    invoices = []
    
    for group in groups:
        merged = {
            "invoice_no": None,
            "date_of_issue": None,
            "seller_name": None,
            "seller_address": None,
            "seller_tax_id": None,
            "seller_iban": None,
            "client_name": None,
            "client_address": None,
            "client_tax_id": None,
            "client_iban": None,
            "net_total": None,
            "vat_total": None,
            "gross_total": None,
            "items": []
        }

        for page in group:
            # Get structured data (already flat)
            data = page.get("ocr", {}).get("structured_data", {})
            if not data and "structured_data" in page:
                 data = page["structured_data"]

            # Invoice number - take first non-empty
            if not merged["invoice_no"] and data.get("invoice_no"):
                merged["invoice_no"] = data.get("invoice_no")

            # Date - take first non-empty
            if not merged["date_of_issue"] and data.get("date_of_issue"):
                merged["date_of_issue"] = data.get("date_of_issue")

            # Seller - take first non-empty (already flat)
            if not merged["seller_name"] and data.get("seller_name"):
                merged["seller_name"] = data.get("seller_name")
                merged["seller_address"] = data.get("seller_address")
                merged["seller_tax_id"] = data.get("seller_tax_id")
                merged["seller_iban"] = data.get("seller_iban")

            # Client - take first non-empty (already flat)
            if not merged["client_name"] and data.get("client_name"):
                merged["client_name"] = data.get("client_name")
                merged["client_address"] = data.get("client_address")
                merged["client_tax_id"] = data.get("client_tax_id")
                merged["client_iban"] = data.get("client_iban")

            # Summary - take last (usually on last page, already flat)
            if data.get("net_total") is not None:
                merged["net_total"] = data.get("net_total")
            if data.get("vat_total") is not None:
                merged["vat_total"] = data.get("vat_total")
            if data.get("gross_total") is not None:
                merged["gross_total"] = data.get("gross_total")

            # Items - concatenate all items from all pages
            if data.get("items"):
                merged["items"].extend(data["items"])
        
        invoices.append(merged)

    return invoices
