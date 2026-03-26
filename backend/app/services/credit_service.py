
from app.db.supabase import supabase
from fastapi import HTTPException

async def check_credits(user_id: str, required_credits: int = 1):
    if not supabase:
         raise HTTPException(500, "Supabase not configured (Credits disabled)")
    # Fetch user profile/credits from Supabase
    # Assuming a 'profiles' or 'users_credits' table
    # This might need adjustment based on actual Supabase schema
    try:
        response = supabase.table("profiles").select("credits").eq("id", user_id).single().execute()
        if not response.data:
            # Create profile if not exists? Or error.
            # For now, error.
            raise HTTPException(400, "User profile not found")
        
        current_credits = response.data.get("credits", 0)
        if current_credits < required_credits:
            raise HTTPException(402, "Insufficient credits")
        
        return current_credits
    except Exception as e:
        # Handle case where table might not exist in early dev
        print(f"Credit check error: {e}")
        # For now, pass if dev mode? No, fail safe.
        raise e

async def deduct_credits(user_id: str, amount: int = 1):
    # Use RPC for atomic update if available, or just update
    # RPC is safer: create a postgres function 'deduct_credits'
    # For this implementation, we will use a direct update for simplicity but acknowledge race conditions
    # Ideally: supabase.rpc('deduct_credits', {'user_id': user_id, 'amount': amount}).execute()
    
    try:
        # Optimistic locking or just decrement
        # Fetch first to ensure enough
        await check_credits(user_id, amount)
        
        # Decrement
        # Note: This is NOT atomic without RPC or extensive locking. 
        # But for MVP, we read, then write.
        response = supabase.table("profiles").select("credits").eq("id", user_id).single().execute()
        current = response.data.get("credits", 0)
        new_balance = current - amount
        
        supabase.table("profiles").update({"credits": new_balance}).eq("id", user_id).execute()
        return new_balance
    except Exception as e:
        raise HTTPException(500, f"Failed to deduct credits: {str(e)}")
