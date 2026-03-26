from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import asyncio
import io
import json
import csv
from app.db.mongo import requests_col
from app.utils.file_generator import generate_excel_report
import os
from starlette.background import BackgroundTask

router = APIRouter()

def clean_invoice_data(data):
    """
    Remove raw data and internal metadata. 
    Keep ONLY: invoice_no, date, seller, client, summary, items.
    """
    # 1. Start with empty dict or shallow copy if flat
    clean = {}
    
    # 2. Extract Key Fields (Flat Structure based on latest parser logic)
    fields_to_keep = [
        "invoice_no", "date_of_issue", "due_date",
        "seller_name", "seller_address", "seller_tax_id", "seller_mobile", "seller_email", "seller_iban",
        "client_name", "client_address", "client_tax_id", "client_mobile", "client_email", "client_iban",
        "sub_total", "cgst", "sgst",
        "net_total", "vat_total", "gross_total"
    ]
    
    for f in fields_to_keep:
        clean[f] = data.get(f)

    # 3. Extract Items (Clean them too)
    clean["items"] = []
    raw_items = data.get("items", [])
    if isinstance(raw_items, list):
        for item in raw_items:
            # Keep only business fields, remove internal processing flags if any
            clean_item = {
                "item_no": item.get("item_no"),
                "description": item.get("description"),
                "hsn_code": item.get("hsn_code"),
                "qty": item.get("qty"),
                "unit": item.get("unit"),
                "rate": item.get("rate") or item.get("unit_price"),
                "net_amount": item.get("net_amount"),
                "discount": item.get("discount"),
                "tax_amount": item.get("tax_amount"),
                "vat_rate": item.get("vat_rate"),
                "total": item.get("total") or item.get("gross_amount")
            }
            # Remove none/empty keys if desired, or keep structure
            clean["items"].append(clean_item)

    return clean

@router.get("/api/v1/requests/{requestId}/download/clean")
async def download_clean_data(requestId: str, format: str = "json"):
    """
    Download ONLY the extracted business data (Clean JSON or CSV).
    Excludes: status, timestamps, processing errors, raw OCR text, page stats.
    """
    
    # 1. Fetch Request
    req = await requests_col.find_one({"_id": requestId})
    if not req or not req.get("extractedData"):
        raise HTTPException(404, "Result not found")

    # 2. Get Data (Handle potential structure variations)
    raw_data = req["extractedData"]
    
    # 3. Clean Data
    data = clean_invoice_data(raw_data)
    
    # -----------------------------
    # JSON EXPORT
    # -----------------------------
    if format == "json":
        json_str = json.dumps(data, indent=2, default=str)
        return StreamingResponse(
            io.BytesIO(json_str.encode('utf-8')),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=invoice_clean_{requestId}.json"}
        )

    # -----------------------------
    # CSV EXPORT
    # -----------------------------
    elif format == "csv":
        return StreamingResponse(
            io.BytesIO(create_csv_string(data).encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=invoice_clean_{requestId}.csv"}
        )

    # -----------------------------
    # ZIP EXPORT
    # -----------------------------
    elif format == "zip":
        import zipfile
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add JSON
            zf.writestr(f"invoice_clean_{requestId}.json", json.dumps(data, indent=2, default=str))
            # Add CSV
            zf.writestr(f"invoice_clean_{requestId}.csv", create_csv_string(data))
        
        zip_buffer.seek(0)
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=invoice_clean_{requestId}.zip"}
        )

    # -----------------------------
    # EXCEL EXPORT
    # -----------------------------
    elif format == "xlsx":
        # We need to pass pages=None or empty list because download_clean_data
        # works on pre-cleaned data, but generate_excel_report expects similar dict structure.
        # generate_excel_report uses "items" list, which we have in `data`.
        xlsx_path = generate_excel_report(data, pages=[])
        
        return StreamingResponse(
            open(xlsx_path, mode="rb"),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=invoice_clean_{requestId}.xlsx"},
            background=BackgroundTask(lambda: os.remove(xlsx_path))
        )

    else:
        raise HTTPException(400, "Invalid format. Use 'json', 'csv', 'xlsx' or 'zip'")

def create_csv_string(data):
    """Helper to generate CSV string from clean data"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Section 1: Header Info (Key-Value rows)
    writer.writerow(["--- INVOICE HEADER ---"])
    headers = [k for k in data.keys() if k != "items"]
    for k in headers:
        writer.writerow([k.replace("_", " ").title(), data[k]])

    writer.writerow([])
    writer.writerow(["--- LINE ITEMS ---"])
    
    # Section 2: Items Table
    items = data.get("items", [])
    if items:
        # Get all keys from first item or predefined list
        item_keys = [
            "item_no", "description", "hsn_code", "qty", "unit", 
            "rate", "net_amount", "discount", "tax_amount", "vat_rate", "total"
        ]
        
        # Header Row
        writer.writerow([k.replace("_", " ").title() for k in item_keys])
        
        # Data Rows
        for item in items:
            row = [item.get(k, "") for k in item_keys]
            writer.writerow(row)
    else:
        writer.writerow(["No items found"])

    return output.getvalue()


# -----------------------------
# BULK EXPORT (ALL INVOICES)
# -----------------------------
@router.get("/api/v1/export/all")
async def export_all_data(format: str = "csv"):
    """
    Export ALL processed invoices in the database as a single file.
    CSV: Master CSV with one row per line item (parent details repeated).
    JSON: List of clean invoice objects.
    ZIP: Contains the Master CSV and Master JSON.
    """
    
    # 1. Fetch All Requests with status "COMPLETED" or "SUCCESS" or just everything that has data
    cursor = requests_col.find({"extractedData": {"$ne": None}})
    all_docs = await asyncio.to_thread(list, cursor)
    
    if not all_docs:
        raise HTTPException(404, "No data found to export")

    # 2. Clean All Data
    clean_docs = []
    for doc in all_docs:
        try:
            # Add Request ID to the data for reference
            clean_data = clean_invoice_data(doc["extractedData"])
            clean_data["request_id"] = doc["_id"]
            clean_docs.append(clean_data)
        except Exception:
            continue

    # -----------------------------
    # JSON EXPORT
    # -----------------------------
    if format == "json":
        json_str = json.dumps(clean_docs, indent=2, default=str)
        return StreamingResponse(
            io.BytesIO(json_str.encode('utf-8')),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=all_invoices_export.json"}
        )

    # -----------------------------
    # CSV EXPORT (Master Sheet)
    # -----------------------------
    elif format == "csv":
        return StreamingResponse(
            io.BytesIO(create_master_csv(clean_docs).encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=all_invoices_export.csv"}
        )

    # -----------------------------
    # ZIP EXPORT
    # -----------------------------
    elif format == "zip":
        import zipfile
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"all_invoices.json", json.dumps(clean_docs, indent=2, default=str))
            zf.writestr(f"all_invoices.csv", create_master_csv(clean_docs))
        
        zip_buffer.seek(0)
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=all_invoices_export.zip"}
        )

    # -----------------------------
    # EXCEL EXPORT
    # -----------------------------
    elif format == "xlsx":
        # For bulk Excel, we might need a different generator or adapt the existing one.
        # Existing `generate_excel_report` is for ONE invoice.
        # We need a new helper `generate_bulk_excel_report`.
        # OR we can just return CSV if user asks for Excel in bulk? 
        # No, let's create a quick bulk excel generator here or use pandas (if available, but we resist adding deps).
        # We can use openpyxl directly here.
        
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "All Invoices"
        
        # Headers from create_master_csv logic
        parent_headers = [
            "request_id", "invoice_no", "date_of_issue", 
            "seller_name", "seller_iban", "client_name", "client_iban",
            "net_total", "vat_total", "gross_total"
        ]
        item_headers = [
            "item_no", "description", "hsn_code", "qty", "unit", 
            "rate", "net_amount", "discount", "tax_amount", "vat_rate", "total"
        ]
        
        ws.append([h.replace("_", " ").title() for h in parent_headers + item_headers])
        
        for doc in clean_docs:
            parent_row = [doc.get(h, "") for h in parent_headers]
            items = doc.get("items", [])
            if items:
                for item in items:
                    item_row = [item.get(h, "") for h in item_headers]
                    ws.append(parent_row + item_row)
            else:
                ws.append(parent_row + [""] * len(item_headers))
        
        
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        wb.save(tmp.name)
        tmp.close()
        
        return StreamingResponse(
            open(tmp.name, mode="rb"),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=all_invoices_export.xlsx"},
            background=BackgroundTask(lambda: os.remove(tmp.name))
        )
    
    else:
        raise HTTPException(400, "Invalid format. Use 'json', 'csv', 'xlsx' or 'zip'")


def create_master_csv(clean_docs_list):
    """
    Generate a SINGLE CSV for ALL invoices.
    Structure: One row per Line Item.
    Columns: [RequestID, InvoiceNo, Date, Seller..., Client..., ItemNo, Desc, Qty..., Total]
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Define Columns
    # Parent Headers
    parent_headers = [
        "request_id", "invoice_no", "date_of_issue", 
        "seller_name", "seller_iban", "client_name", "client_iban",
        "net_total", "vat_total", "gross_total"
    ]
    
    # Item Headers
    item_headers = [
        "item_no", "description", "hsn_code", "qty", "unit", 
        "rate", "net_amount", "discount", "tax_amount", "vat_rate", "total"
    ]
    
    # Write Header
    writer.writerow([h.replace("_", " ").title() for h in parent_headers + item_headers])
    
    for doc in clean_docs_list:
        # Prepare parent data
        parent_row = [doc.get(h, "") for h in parent_headers]
        
        items = doc.get("items", [])
        if items:
            for item in items:
                # Prepare item data
                item_row = [item.get(h, "") for h in item_headers]
                # Combine
                writer.writerow(parent_row + item_row)
        else:
            # No items, just write parent info with empty item slots
            writer.writerow(parent_row + [""] * len(item_headers))

    return output.getvalue()
