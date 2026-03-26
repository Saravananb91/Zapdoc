# app/services/queue.py
import asyncio

# Global async queue for OCR jobs
PAGE_QUEUE: asyncio.Queue = asyncio.Queue(maxsize=10)
