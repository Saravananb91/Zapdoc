from datetime import datetime
from app.db.mongo import requests_col
from app.ocr.pipeline import merge_pages


async def save_final_result(request_id: str, page_results: list):

    successful = [p for p in page_results if p["status"] == "SUCCESS"]
    merged_data = merge_pages(successful)

    status = (
        "COMPLETED" if successful else "FAILED"
    )

    await requests_col.update_one(
        {"_id": request_id},
        {"$set": {
            "status": status,
            "completedAt": datetime.utcnow(),
            "confidence": (
                sum(p.get("confidence_score", 0) for p in successful) / max(1, len(successful))
            ),
            "extractedData": {
                "documentStatus": status,
                "pageSummary": {
                    "total_pages": len(page_results),
                    "successful_pages": len(successful),
                    "failed_pages": len(page_results) - len(successful)
                },
                "invoiceData": merged_data,
                "pages": page_results,
                "errors": [p.get("error") for p in page_results if p["status"] == "FAILED"]
            }
        }}
    )

