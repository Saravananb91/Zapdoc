
from supabase import create_client, Client
from app.core.config import settings

try:
    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    else:
        print("WARNING: Supabase credentials not found. Supabase client disabled.")
        supabase = None
except Exception as e:
    print(f"WARNING: Failed to initialize Supabase client: {e}")
    supabase = None
