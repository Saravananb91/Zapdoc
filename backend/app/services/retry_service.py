MAX_PAGE_RETRY = 10

class RetryService:
    def should_retry(self, page_info):
        return page_info["retry_count"] < MAX_PAGE_RETRY

    def handle_retry(self, page_no, page_controller):
        page_controller.increment_retry(page_no)

        if not self.should_retry(page_controller.pages[page_no]):
            return False  # stop retry

        return True
