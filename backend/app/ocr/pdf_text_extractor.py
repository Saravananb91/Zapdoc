# app/ocr/pdf_text_extractor.py

import fitz  # PyMuPDF


def extract_text_with_pymupdf(pdf_path: str) -> str:
    """
    Extract text from a PDF using PyMuPDF.
    Works ONLY for text-based (digital) PDFs.
    Returns combined text from all pages as STRING.
    """

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise RuntimeError(f"Unable to open PDF: {e}")

    extracted_pages = []

    for page_index in range(len(doc)):
        page = doc.load_page(page_index)

        # 'text' mode preserves line breaks reasonably well
        page_text = page.get_text("text")

        if page_text:
            extracted_pages.append(page_text)

    doc.close()

    # 🔥 IMPORTANT: always return STRING (not list)
    return "\n".join(extracted_pages).strip()
