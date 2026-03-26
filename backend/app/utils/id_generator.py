from datetime import datetime
from uuid import uuid4

def generate_request_id() -> str:
    year = datetime.utcnow().year
    unique = uuid4().hex[:6].upper()
    return f"REQ-{year}-{datetime.utcnow().strftime('%d%m%y')}{unique}"

