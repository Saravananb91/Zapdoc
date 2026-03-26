from pydantic import BaseModel
from typing import Optional, Dict


class CreateRequestPayload(BaseModel):
    sourceType: str                 # "3pfs" | "upload"
    documentType: str               # "pdf" | "image"
    sourceReference: Optional[str] = None
    metadata: Optional[Dict] = {}
