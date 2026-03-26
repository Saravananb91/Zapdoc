
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings
from pathlib import Path
from typing import List

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_TLS,
    MAIL_SSL_TLS=settings.MAIL_SSL,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS
)

async def send_extraction_email(email_to: str, file_paths: List[Path], request_id: str):
    
    html = f"""
    <p>Hello,</p>
    <p>Your document extraction for Request ID <strong>{request_id}</strong> is complete.</p>
    <p>Please find the extracted results attached.</p>
    <br>
    <p>Best regards,</p>
    <p>The OCR Agent Team</p>
    """

    # Convert Paths to strings for FastAPI-Mail
    attachment_paths = [str(p) for p in file_paths]

    message = MessageSchema(
        subject=f"OCR Extraction Result - {request_id}",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
        attachments=attachment_paths
    )

    fm = FastMail(conf)
    await fm.send_message(message)
