import os
from datetime import datetime

BASE_UPLOAD_DIR = "data/uploads"

def save_uploaded_file(request_id: str, filename: str, content: bytes) -> str:
    os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)

    safe_name = f"{request_id}_{filename}"
    file_path = os.path.join(BASE_UPLOAD_DIR, safe_name)

    with open(file_path, "wb") as f:
        f.write(content)

    return file_path
