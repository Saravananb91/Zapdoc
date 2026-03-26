import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def send_email_with_attachment(to_email: str, subject: str, body: str, attachment_bytes: bytes, attachment_filename: str):
    """
    Sends an email with an attachment using SMTP settings from config.
    """
    if not to_email:
        logger.warning("No recipient email provided. Skipping email send.")
        return False

    msg = MIMEMultipart()
    msg['From'] = settings.MAIL_FROM
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    # Attach file
    part = MIMEApplication(attachment_bytes, Name=attachment_filename)
    part['Content-Disposition'] = f'attachment; filename="{attachment_filename}"'
    msg.attach(part)

    try:
        # Connect to SMTP Server
        if settings.MAIL_SSL:
            server = smtplib.SMTP_SSL(settings.MAIL_SERVER, settings.MAIL_PORT)
        else:
            server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT)
            if settings.MAIL_TLS:
                server.starttls()

        # Login if credentials provided
        if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)

        # Send
        server.send_message(msg)
        server.quit()
        logger.info(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        # Don't raise error to avoid blocking the API response, just log it.
        # But for the API to know, maybe we should raise or return False.
        # Returning False allows the caller to handle the user message.
        return False
