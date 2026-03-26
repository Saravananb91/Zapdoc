from pydantic import BaseModel
from typing import List, Dict, Any

class PageResult(BaseModel):
    page: int
    ocr_text: str
    confidence: float | None

class FinalOCRResponse(BaseModel):
    request_id: str
    status: str
    pages: List[PageResult]
    extracted_data: Dict[str, Any]
    metadata: Dict[str, Any]
