
from app.ocr.parser_utils import parse_invoice_text_to_struct
from app.services.prase_llmt import gemini_llm_client

def process_invoice(raw_text: str):
    structured_data = parse_invoice_text_to_struct(
        raw_text,
        llm_client=gemini_llm_client
    )

    return structured_data