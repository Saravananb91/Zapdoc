class PageController:
    def __init__(self):
        self.pages = {}

    def init_pages(self, total_pages):
        for i in range(1, total_pages + 1):
            self.pages[i] = {
                "status": "PENDING",
                "retry_count": 0
            }

    def mark_success(self, page_no):
        self.pages[page_no]["status"] = "SUCCESS"

    def mark_failed(self, page_no):
        self.pages[page_no]["status"] = "FAILED"

    def increment_retry(self, page_no):
        self.pages[page_no]["retry_count"] += 1

    def failed_pages(self):
        return {
            p: v for p, v in self.pages.items()
            if v["status"] == "FAILED"
        }
