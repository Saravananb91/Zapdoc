from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# -----------------------------
# Page-level error
# -----------------------------
class PageError(BaseModel):
    error_code: str = Field(..., example="OCR_FAILED")
    message: str = Field(..., example="Page failed after retries")


# -----------------------------
# Aggregated document error
# -----------------------------
class AggregatedError(BaseModel):
    page: int = Field(..., example=2)
    error_code: str = Field(..., example="OCR_FAILED")
    message: str = Field(..., example="Low confidence after retries")


# -----------------------------
# OCR content per page
# -----------------------------
class OCRContent(BaseModel):
    raw_text: Optional[str] = Field(
        None,
        description="Raw OCR extracted text"
    )
    structured_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Parsed key-value OCR data"
    )


# -----------------------------
# Page OCR result
# -----------------------------
class OCRPageResult(BaseModel):
    page_number: int
    status: str
    retry_count: int
    # confidence_score: float

    ocr: Optional[OCRContent] = None
    error: Optional[PageError] = None


# -----------------------------
# Page summary
# -----------------------------
class PageSummary(BaseModel):
    total_pages: int
    successful_pages: int
    failed_pages: int


# -----------------------------
# Final OCR response
# -----------------------------
class OCRResponse(BaseModel):
    request_id: str
    status: str
    processing_time_ms: int

    page_summary: PageSummary

    errors: List[AggregatedError]

    pages: List[OCRPageResult]

    merged_result: Optional[Dict[str, Any]] = None


# -----------------------------
# Request Creation
# -----------------------------
class RequestCreate(BaseModel):
    email: Optional[str] = Field(None, description="User email for notifications (optional)")
    custom_fields: Optional[List[str]] = Field(None, description="List of additional fields to extract")
