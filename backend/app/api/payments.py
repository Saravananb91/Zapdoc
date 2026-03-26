
from fastapi import APIRouter, Header, HTTPException, Request
import stripe
from app.core.config import settings
from app.services.credit_service import supabase

router = APIRouter()

stripe.api_key = settings.STRIPE_SECRET_KEY

@router.post("/api/v1/payments/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    sig_header = stripe_signature
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Retrieve user_id from client_reference_id or metadata
        user_id = session.get("client_reference_id")
        amount_total = session.get("amount_total") # amount in cents
        
        # Determine credits based on amount (logic depends on pricing)
        # For simplicity, 1 USD = 10 Credits (example)
        credits_to_add = int(amount_total / 100) * 10 
        
        if user_id:
            try:
                # Add credits via RPC or update
                response = supabase.table("profiles").select("credits").eq("id", user_id).single().execute()
                current_credits = response.data.get("credits", 0)
                new_credits = current_credits + credits_to_add
                
                supabase.table("profiles").update({"credits": new_credits}).eq("id", user_id).execute()
                print(f"Added {credits_to_add} credits to user {user_id}")
            except Exception as e:
                print(f"Error updating credits for user {user_id}: {e}")
                raise HTTPException(status_code=500, detail="Database update failed")

    return {"status": "success"}
