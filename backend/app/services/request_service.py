from datetime import datetime

VALID_TRANSITIONS = {
    "CREATED": ["DOCUMENT_UPLOADED"],
    "DOCUMENT_UPLOADED": ["QUEUED"],
    "QUEUED": ["OCR_IN_PROGRESS"],
    "OCR_IN_PROGRESS": ["LLM_IN_PROGRESS", "RETRYING", "FAILED"],
    "LLM_IN_PROGRESS": ["POST_PROCESSING", "FAILED"],
    "POST_PROCESSING": ["COMPLETED", "FAILED"],
    "RETRYING": ["OCR_IN_PROGRESS", "FAILED"]
}

class RequestService:
    def __init__(self, db):
        self.db = db

    def create_request(self, request_id):
        self.db.requests.insert({
            "id": request_id,
            "status": "CREATED",
            "created_at": datetime.utcnow()
        })

    def update_status(self, request_id, new_status):
        req = self.db.requests.get(request_id)

        if new_status not in VALID_TRANSITIONS.get(req["status"], []):
            raise Exception(
                f"Invalid transition {req['status']} → {new_status}"
            )

        self.db.requests.update(
            request_id,
            {
                "status": new_status,
                "updated_at": datetime.utcnow()
            }
        )

    def mark_failed(self, request_id, error):
        self.db.requests.update(
            request_id,
            {
                "status": "FAILED",
                "error_message": error,
                "completed_at": datetime.utcnow()
            }
        )

    def mark_completed(self, request_id):
        self.db.requests.update(
            request_id,
            {
                "status": "COMPLETED",
                "completed_at": datetime.utcnow()
            }
        )
