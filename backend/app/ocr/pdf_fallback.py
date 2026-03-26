# app/ocr/pdf_fallback.py
import os
import tempfile
import time
import fitz  # PyMuPDF


def pdf_to_images(pdf_path: str):
    """
    Convert PDF pages to images using PyMuPDF.
    OCR-safe, Windows-safe.
    Returns list of image file paths.
    """

    doc = fitz.open(pdf_path)

    # Dedicated temp folder
    temp_dir = tempfile.mkdtemp(prefix="ocr_pdf_")
    image_paths = []

    # zoom = 2 → ~300 DPI equivalent
    zoom = 2
    mat = fitz.Matrix(zoom, zoom)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        img_path = os.path.join(temp_dir, f"page_{page_num + 1}.png")
        pix.save(img_path)
        image_paths.append(img_path)

    doc.close()
    return image_paths


import os
import time

def cleanup_tmp_files(paths):
    for p in paths:
        try:
            time.sleep(0.2)  # allow file handles to release
            if os.path.exists(p):
                os.remove(p)
        except PermissionError:
            print(f"[WARN] Could not delete temp file now: {p}")
        except Exception as e:
            print(f"[WARN] Temp cleanup error: {e}")

