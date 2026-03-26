
import re
import json
from dateutil import parser as dateparser

def normalize_amount(amount_str):

    if not amount_str:
        return None
    
    try:
        # Remove spaces and commas
        cleaned = str(amount_str).replace(',', '').replace(' ', '').strip()
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def clean(val):
    """Clean string values"""
    if val is None:
        return None
    return str(val).strip() if val else None


# ======================================================
# DETECT INPUT TYPE
# ======================================================

def detect_input_type(text):
    """Detect if input is JSON or plain text"""
    text = text.strip()
    if text.startswith('{') or text.startswith('['):
        try:
            json.loads(text)
            return 'json'
        except:
            return 'text'
    return 'text'

# JSON PARSING (for LLM OCR output)

def parse_json_invoice(json_text):
    try:
        data = json.loads(json_text)
    except:
        return None
    
    # Ensure correct keys even if LLM slightly deviates
    seller = data.get("seller", {}) or {}
    client = data.get("client", {}) or {}
    summary = data.get("summary", {}) or {}
    
    # FLAT STRUCTURE (matching merge_pages expectations)
    structured = {
        "invoice_no": data.get("invoice_no") or data.get("invoice_number"),
        "date_of_issue": data.get("date_of_issue") or data.get("date"),
        
        # Seller - FLAT
        "seller_name": seller.get("name"),
        "seller_address": seller.get("address"),
        "seller_tax_id": seller.get("tax_id"),
        "seller_mobile": seller.get("mobile"),
        "seller_email": seller.get("email"),
        "seller_iban": seller.get("iban"),
        
        # Client - FLAT
        "client_name": client.get("name"),
        "client_address": client.get("address"),
        "client_tax_id": client.get("tax_id"),
        "client_mobile": client.get("mobile"),
        "client_email": client.get("email"),
        "client_iban": client.get("iban"),
        
        # Items
        "items": data.get("items", []),
        
        # Summary - FLAT
        "sub_total": summary.get("sub_total"),
        "cgst": summary.get("cgst"),
        "sgst": summary.get("sgst"),
        "net_total": summary.get("net_total") or summary.get("net_worth_total"),
        "vat_total": summary.get("vat_total"),
        "gross_total": summary.get("gross_total") or summary.get("gross_worth_total")
    }
    
    return structured

def extract_invoice_no(text):
    m = re.search(r"invoice\s*(number|no)?[:\s]+(\d+)", text, re.I)
    return m.group(2) if m else None


def extract_invoice_date(text):
    m = re.search(r"date\s*of\s*issue[:\s]+([0-9\-]+)", text, re.I)
    return dateparser.parse(m.group(1)).date().isoformat() if m else None


def extract_party_block(text: str, label: str):

    
    # Check if text contains party labels at all
    if "Seller:" not in text and "seller:" not in text.lower():
        return "", "", None
    
    # Find section containing Seller and Client
    party_section_pattern = r"Seller:\s*(.*?)(?=\n\s*ITEMS|ITEM|$)"
    party_section_match = re.search(party_section_pattern, text, re.DOTALL | re.IGNORECASE)
    
    if not party_section_match:
        return "", "", None
    
    party_section = party_section_match.group(1)
    
    if not party_section.strip():
        return "", "", None
    
    lines = party_section.split('\n')
    is_seller = label.lower() == "seller"
    
    name_lines = []
    address_lines = []
    tax_id = None
    
    for line in lines:
        line = line.rstrip()
        
        if not line.strip():
            continue
        
        # Extract Tax IDs
        if "Tax Id:" in line or "Tax ID:" in line or "tax id:" in line.lower():
            all_tax_ids = re.findall(r"Tax\s*Id:\s*([\d\-]+)", line, re.I)
            
            if is_seller:
                # Seller gets first Tax ID (left column)
                if all_tax_ids:
                    tax_id = all_tax_ids[0]
            else:
                # Client gets second Tax ID (right column) if exists
                if len(all_tax_ids) >= 2:
                    tax_id = all_tax_ids[1]
                elif len(all_tax_ids) == 1:
                    # Only one tax ID - check position by whitespace
                    left_part = line.split("Tax")[0]
                    if len(left_part) > 20:  # Significant whitespace = right column
                        tax_id = all_tax_ids[0]
            continue
        
        # Skip IBAN line
        if "IBAN:" in line or "iban:" in line.lower():
            continue
        
        # Split by significant whitespace (2+ spaces = column separator)
        parts = re.split(r'\s{2,}', line)
        
        if len(parts) >= 2:
            # Side-by-side layout detected
            if is_seller:
                content = parts[0].strip()
            else:
                # Client is on the right
                content = None
                for part in parts[1:]:
                    part = part.strip()
                    if part and "Seller:" not in part and "Client:" not in part:
                        content = part
                        break
                if not content:
                    content = parts[-1].strip()
        else:
            # Single column line - might be continuation
            content = line.strip()
            # Skip if it's just the label
            if content.lower() in ["seller:", "client:"]:
                continue
        
        if content and content.strip():
            # First non-empty line is name
            if not name_lines:
                # Remove "Seller:" or "Client:" prefix if present
                content = re.sub(r"^(Seller|Client):\s*", "", content, flags=re.I)
                name_lines.append(content)
            else:
                # Subsequent lines are address
                address_lines.append(content)
    
    name = name_lines[0] if name_lines else ""
    address = " ".join(address_lines) if address_lines else ""
    
    return name, address, tax_id


def extract_items_kv_style(text):
    items = []
    blocks = re.split(r"\n(?=Item:)", text)

    for block in blocks:
        if not block.strip().startswith("Item"):
            continue

        desc = re.search(r"Item:\s*(.+)", block)
        qty = re.search(r"Item Quantity:\s*([\d.]+)", block)
        um = re.search(r"Item Unit of Measure:\s*(\w+)", block)
        net_price = re.search(r"Item Net Price:\s*([\d.]+)", block)
        net = re.search(r"Item Net Worth:\s*([\d.]+)", block)
        vat = re.search(r"Item VAT\s*%:\s*([\d.]+)", block)
        gross = re.search(r"Item Gross Worth:\s*([\d.]+)", block)

        if not (desc and gross):
            continue

        items.append({
            "item_no": len(items) + 1,
            "description": clean(desc.group(1)),
            "qty": normalize_amount(qty.group(1)) if qty else None,
            "unit": um.group(1) if um else None,
            "unit_price": normalize_amount(net_price.group(1)) if net_price else None,
            "net_amount": normalize_amount(net.group(1)) if net else None,
            "vat_rate": normalize_amount(vat.group(1)) if vat else None,
            "gross_amount": normalize_amount(gross.group(1))
        })

    return items

def extract_summary_kv_totals(text):
    """
    Extract summary totals from invoice text.
    
    Handles multiple formats:
    - "Total Net Worth: 1234.56"
    - "Net Total: 1234.56"
    - "TOTAL NET: 1234.56"
    - "Subtotal: 1234.56"
    - And similar variations for VAT and Gross
    
    Returns:
        dict with net_total, vat_total, gross_total or None if not found
    """
    
    # Try to find SUMMARY section first
    summary_match = re.search(r'SUMMARY\s*\n(.+?)(?:\n\s*\n|$)', text, re.IGNORECASE | re.DOTALL)
    search_text = summary_match.group(1) if summary_match else text
    
    # Extract Net Total (try multiple patterns)
    net_total = None
    net_patterns = [
        r"Total\s+Net\s+Worth\s*:?\s*([\d,]+\.?\d*)",  # Total Net Worth: 1234.56
        r"Net\s+Total\s*:?\s*([\d,]+\.?\d*)",           # Net Total: 1234.56
        r"Subtotal\s*:?\s*([\d,]+\.?\d*)",              # Subtotal: 1234.56
        r"Total\s+Net\s*:?\s*([\d,]+\.?\d*)",           # Total Net: 1234.56
        r"Net\s+Amount\s*:?\s*([\d,]+\.?\d*)",          # Net Amount: 1234.56
        r"Net\s+Worth\s*:?\s*([\d,]+\.?\d*)",           # Net Worth: 1234.56
    ]
    
    for pattern in net_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            net_total = normalize_amount(match.group(1))
            break
    
    # Extract VAT Total (try multiple patterns)
    vat_total = None
    vat_patterns = [
        r"Total\s+VAT\s*:?\s*([\d,]+\.?\d*)",           # Total VAT: 123.45
        r"VAT\s+Total\s*:?\s*([\d,]+\.?\d*)",           # VAT Total: 123.45
        r"VAT\s+Amount\s*:?\s*([\d,]+\.?\d*)",          # VAT Amount: 123.45
        r"Tax\s+Total\s*:?\s*([\d,]+\.?\d*)",           # Tax Total: 123.45
        r"Total\s+Tax\s*:?\s*([\d,]+\.?\d*)",           # Total Tax: 123.45
        r"VAT\s*:?\s*([\d,]+\.?\d*)",                   # VAT: 123.45
    ]
    
    for pattern in vat_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            vat_total = normalize_amount(match.group(1))
            break
    
    # Extract Gross Total (try multiple patterns)
    gross_total = None
    gross_patterns = [
        r"Total\s+Gross\s+Worth\s*:?\s*([\d,]+\.?\d*)", # Total Gross Worth: 1358.01
        r"Gross\s+Total\s*:?\s*([\d,]+\.?\d*)",         # Gross Total: 1358.01
        r"Total\s+Gross\s*:?\s*([\d,]+\.?\d*)",         # Total Gross: 1358.01
        r"Grand\s+Total\s*:?\s*([\d,]+\.?\d*)",         # Grand Total: 1358.01
        r"Total\s+Amount\s*:?\s*([\d,]+\.?\d*)",        # Total Amount: 1358.01
        r"Amount\s+Due\s*:?\s*([\d,]+\.?\d*)",          # Amount Due: 1358.01
        r"Total\s*:?\s*([\d,]+\.?\d*)",                 # Total: 1358.01 (last resort)
    ]
    
    for pattern in gross_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            gross_total = normalize_amount(match.group(1))
            break
    
    # Return None if we couldn't find ANY totals
    if net_total is None and vat_total is None and gross_total is None:
        return None
    
    # Return what we found (some fields may be None)
    return {
        "net_total": net_total,
        "vat_total": vat_total,
        "gross_total": gross_total
    }


def parse_text_invoice(text):
    
    # Extract basic fields
    invoice_no = extract_invoice_no(text)
    date = extract_invoice_date(text)

    # Extract seller (returns tuple: name, address, tax_id)
    seller_name, seller_address, seller_tax_id = extract_party_block(text, "Seller")
    
    # Extract client (returns tuple: name, address, tax_id)
    client_name, client_address, client_tax_id = extract_party_block(text, "Client")

    # Extract items (returns list of objects)
    items = extract_items_kv_style(text)
    
    # Extract summary (returns dict or None)
    summary = extract_summary_kv_totals(text)
    
    # Build FLAT structure
    structured = {
        "invoice_no": invoice_no,
        "date_of_issue": date,
        
        # Seller - FLAT
        "seller_name": seller_name or None,
        "seller_address": seller_address or None,
        "seller_tax_id": seller_tax_id,
        
        # Client - FLAT
        "client_name": client_name or None,
        "client_address": client_address or None,
        "client_tax_id": client_tax_id,
        
        # Summary - FLAT
        "net_total": summary.get("net_total") if summary else None,
        "vat_total": summary.get("vat_total") if summary else None,
        "gross_total": summary.get("gross_total") if summary else None,
        
        # Items - array of objects
        "items": items or []
    }
    
    return structured


def flatten_for_db(nested_data):
    """
    DEPRECATED: This function is no longer needed since parse functions
    now return flat structure directly.
    
    Kept for backward compatibility only.
    """
    # If data is already flat, return as-is
    if "seller_name" in nested_data:
        return nested_data
    
    # Otherwise flatten (old nested format)
    if not nested_data:
        return None
    
    flat = {
        "invoice_no": nested_data.get("invoice_no"),
        "date_of_issue": nested_data.get("date_of_issue"),
    }
    
    # Flatten seller
    seller = nested_data.get("seller") or {}
    flat["seller_name"] = seller.get("name") if isinstance(seller, dict) else None
    flat["seller_address"] = seller.get("address") if isinstance(seller, dict) else None
    flat["seller_tax_id"] = seller.get("tax_id") if isinstance(seller, dict) else None
    
    # Flatten client
    client = nested_data.get("client") or {}
    flat["client_name"] = client.get("name") if isinstance(client, dict) else None
    flat["client_address"] = client.get("address") if isinstance(client, dict) else None
    flat["client_tax_id"] = client.get("tax_id") if isinstance(client, dict) else None
    
    # Items
    flat["items"] = nested_data.get("items") or []
    
    # Flatten summary
    summary = nested_data.get("summary") or {}
    flat["net_total"] = summary.get("net_total") if isinstance(summary, dict) else None
    flat["vat_total"] = summary.get("vat_total") if isinstance(summary, dict) else None
    flat["gross_total"] = summary.get("gross_total") if isinstance(summary, dict) else None
    
    return flat

# MAIN ENTRY POINT - AUTO-DETECTS JSON OR TEXT

def parse_invoice_text_to_struct(text, flat_output=True):
    """
    Main parsing function that auto-detects JSON or text format
    
    NOW ALWAYS RETURNS FLAT STRUCTURE (flat_output parameter kept for compatibility)
    
    Args:
        text: Either JSON string from LLM OCR or key-value formatted text
        flat_output: Kept for backward compatibility (ignored, always returns flat)
        
    Returns:
        FLAT structured dict:
        {
            "invoice_no": "...",
            "date_of_issue": "...",
            "seller_name": "...",      # FLAT
            "seller_address": "...",   # FLAT
            "seller_tax_id": "...",    # FLAT
            "client_name": "...",      # FLAT
            "client_address": "...",   # FLAT
            "client_tax_id": "...",    # FLAT
            "net_total": 123.45,       # FLAT
            "vat_total": 12.34,        # FLAT
            "gross_total": 135.79,     # FLAT
            "items": [...]             # Array of objects
        }
    """
    
    # Handle empty input
    if not text or not text.strip():
        return {
            "invoice_no": None,
            "date_of_issue": None,
            "seller_name": None,
            "seller_address": None,
            "seller_tax_id": None,
            "client_name": None,
            "client_address": None,
            "client_tax_id": None,
            "net_total": None,
            "vat_total": None,
            "gross_total": None,
            "items": []
        }
    
    # Detect input type
    input_type = detect_input_type(text)
    
    # Parse based on type
    if input_type == 'json':
        result = parse_json_invoice(text)
        if result:
            return result
        else:
            # JSON parsing failed, fallback to text
            print("JSON parsing failed, falling back to text parsing")
            return parse_text_invoice(text)
    else:
        return parse_text_invoice(text)
