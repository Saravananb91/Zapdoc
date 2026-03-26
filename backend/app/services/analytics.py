
from app.db.supabase import supabase
from datetime import datetime

async def log_analytics_event(event_type: str, user_id: str, metadata: dict = None):
    if not supabase:
        return
    try:
        data = {
            "event_type": event_type,
            "user_id": user_id,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }
        # Assuming an 'analytics_events' table exists
        supabase.table("analytics_events").insert(data).execute()
    except Exception as e:
        print(f"Failed to log analytics event: {e}")
