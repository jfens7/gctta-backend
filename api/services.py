# api/services.py
    
import stripe
from django.conf import settings
from django.utils import timezone
from .models import Season

stripe.api_key = settings.STRIPE_SECRET_KEY

def get_payment_amount_and_description(payment_type: str):
    """
    Determines the payment amount in cents and a description.
    Returns a tuple: (amount, description)
    """
    amount = 0
    description = ""
    
    if payment_type == 'fixture_fee':
        today = timezone.now().date()
        current_season = Season.objects.filter(start_date__lte=today, end_date__gte=today).first()
        if current_season:
            amount = int(current_season.fixture_fee_amount * 100)
            description = f"Payment for {current_season.name}"
            
    elif payment_type == 'social_card_purchase':
        amount = 5000  # Placeholder for $50.00
        description = "Purchase of 10-Session Social Card"
        
    return amount, description

def create_stripe_payment_intent(payment_type: str, user):
    """
    Creates a Stripe Payment Intent and returns its client_secret.
    """
    amount_in_cents, description = get_payment_amount_and_description(payment_type)
    
    if amount_in_cents <= 0:
        raise ValueError("Could not determine payment amount for the specified type.")

    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency='aud',
            automatic_payment_methods={'enabled': True},
            receipt_email=user.email,
            description=description
        )
        return payment_intent.client_secret
    except Exception as e:
        raise e