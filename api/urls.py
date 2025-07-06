# api/urls.py

from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    FixtureEligibilityView,
    CreatePaymentIntentView,
    StripeWebhookView # Import the new view
)

urlpatterns = [
    path('auth/signup/', UserRegistrationView.as_view(), name='signup'),
    path('auth/login/', UserLoginView.as_view(), name='login'),
    path('player/fixture_eligibility/', FixtureEligibilityView.as_view(), name='fixture-eligibility'),
    path('payments/create-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    # Add the URL for our new webhook endpoint
    path('stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]