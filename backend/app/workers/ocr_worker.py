import time
from app.services.ocr_service import OCRService
from app.services.page_controller import PageController
from app.services.retry_service import RetryService

def run_ocr_job(file_path, request_id, request_service):
    page_controller = PageController()
    retry_service = RetryService()

    request_service.update_status(request_id, "OCR_IN_PROGRESS")

    results = OCRService.process(file_path, request_id)

    page_controller.init_pages(len(results))

    final_results = []

    for page in results:
        try:
            final_results.append(page)
            page_controller.mark_success(page["page"])
        except Exception:
            page_controller.mark_failed(page["page"])

    # retry failed pages
    for page_no, info in page_controller.failed_pages().items():
        if retry_service.handle_retry(page_no, page_controller):
            # retry logic hook
            pass
        else:
            request_service.mark_failed(
                request_id,
                f"Retry limit exceeded on page {page_no}"
            )
            return None

    request_service.update_status(request_id, "LLM_IN_PROGRESS")
    return final_results
