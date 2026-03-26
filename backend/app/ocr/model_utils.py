6

# app/ocr/model_utils.py
import os
import google.generativeai as genai
from app.ocr.config import LLM_TIMEOUT

_configured = False

def configure_api():
    global _configured
    if _configured:
        return
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_API_KEY not set")
    genai.configure(api_key=key)
    _configured = True


def choose_model():
    return "models/gemini-2.5-flash"


def ocr_once(file_path: str, custom_fields: list = None) -> str:
    """
    Run OCR ONCE.
    NO retry here. Retry handled by pipeline.
    """
    configure_api()

    model = genai.GenerativeModel(choose_model())
    file = genai.upload_file(file_path)

    response = model.generate_content(
        [file, """
         You are an expert invoice extraction AI. Extract structured data from this invoice image/PDF.
         
         ### 🔍 LAYOUT DETECTION & EXTRACTION LOGIC
         1. **Check Layout**:
            - **Type 1 (Solaris)**: Look for "HSN Code", "Discount". -> Extract HSN, Discount, Tax Amount.
            - **Type 2 (General/VAT)**: Look for "UM", "Net price", "Net worth", "VAT [%]", "Gross worth". 
              -> Extract **Unit** (UM), **Net Amount** (Net worth), **VAT Rate** (VAT %).

         2. **Parties Extraction (Critical)**
            - **Seller**: The entity ISSUING the invoice. Look for header/logo. Extract Mobile, Email, Tax ID/GSTIN if present.
            - **Client**: The entity BILL TO. Extract Mobile, Email, Tax ID if present.

         3. **Items Table Extraction (Critical)**
            - **Unified Mapping**:
              - "Qty" -> qty
              - "UM" / "Unit" -> unit
              - "Rate" / "Unit Price" / "Net price" -> rate
              - "Net worth" / "Net Amount" -> net_amount
              - "Discount" -> discount
              - "Tax" / "Tax Amount" -> tax_amount
              - "VAT [%]" / "VAT Rate" -> vat_rate (e.g. "10%")
              - "Total" / "Gross worth" / "Gross Amount" -> total
              - "HSN" -> hsn_code

         4. **Custom Fields Extraction**:
             {f'- The user requested these additional fields: {", ".join(custom_fields)}.' if custom_fields else ''}
             {'- Extract them if present and put them in "custom_fields" object.' if custom_fields else ''}

         ### 📝 JSON OUTPUT SCHEMA
         {
           "invoice_no": "string or null",
           "date_of_issue": "YYYY-MM-DD or null",
           "due_date": "YYYY-MM-DD or null",
           
           "seller": {
             "name": "string or null",
             "address": "string or null",
             "tax_id": "string or null",
             "mobile": "string or null",
             "email": "string or null",
             "iban": "string or null"
           },
           "client": {
             "name": "string or null",
             "address": "string or null",
             "tax_id": "string or null",
             "mobile": "string or null",
             "email": "string or null",
             "iban": "string or null"
           },
           
           "items": [
             {
               "item_no": number,
               "description": "string",
               "hsn_code": "string or null",
               "qty": "number as string",
               "unit": "string or null",
               "rate": "number as string",
               "discount": "string or null",
               "tax_amount": "number as string", 
               "vat_rate": "string or null",
               "net_amount": "number as string",
               "total": "number as string"
             }
           ],
           
           "summary": {
             "sub_total": "number as string",
             "cgst": "string or null",
             "sgst": "string or null",
             "net_total": "number as string",
             "vat_total": "number as string",
             "gross_total": "number as string"
           },
           
           "custom_fields": {
             "field1": "value1",
             "field2": "value2"
           }
         }

         ### STRICT OUTPUT RULES
         1. Return ONLY valid JSON. No markdown.
         2. Missing fields = null.
         3. Dates = YYYY-MM-DD.
         4. **Numbers**: Keep 2 decimal places where possible.
         """
        ],
        request_options={"timeout": LLM_TIMEOUT}
    )
    
    text = response.text or ""
    text = text.replace("```json", "").replace("```", "").strip()

    if len(text) < 20:
        raise ValueError("EMPTY_OCR_TEXT")

    return text

    # if not response.text or not response.text.strip():
    #     raise ValueError("EMPTY_OCR_OUTPUT")

    # return response.text
