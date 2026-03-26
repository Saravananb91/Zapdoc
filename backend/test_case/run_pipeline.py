from app.ocr.pipeline import process_document

def run_model(file_path):
    result = process_document(file_path)

    # Assume single-page invoice
    page = result["pages"][0]

    # This is your final extracted output
    return page["structured_data"]
