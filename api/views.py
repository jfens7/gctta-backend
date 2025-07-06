# api/views.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import UserRegistrationSerializer, UserSerializer
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Season, PlayerSeasonFee, User
from .services import create_stripe_payment_intent

# New imports for the webhook
import stripe
from django.conf import settings
from django.http import HttpResponse


class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'token': str(refresh.access_token),
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    def post(self, request):
        if 'email' not in request.data or 'password' not in request.data:
            return Response({'error': 'Please provide both email and password'}, status=status.HTTP_400_BAD_REQUEST)
        
        email = request.data['email']
        password = request.data['password']
        user = authenticate(username=email, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            user_data = UserSerializer(user).data 
            return Response({
                'token': str(refresh.access_token),
                'user': user_data
            }, status=status.HTTP_200_OK)
        
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class FixtureEligibilityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()

        if user.membership_type == User.MembershipType.GOLD_ANNUAL:
            return Response({"is_fee_owed": False, "reason": "Gold Annual Members have fees included."})

        try:
            current_season = Season.objects.get(start_date__lte=today, end_date__gte=today)
        except Season.DoesNotExist:
            return Response({"error": "No active season found."}, status=status.HTTP_404_NOT_FOUND)
        
        is_paid = PlayerSeasonFee.objects.filter(player=user, season=current_season, payment_status=PlayerSeasonFee.PaymentStatus.PAID).exists()

        if is_paid:
            return Response({"is_fee_owed": False, "season_name": current_season.name})
        else:
            return Response({
                "is_fee_owed": True,
                "amount_owed": str(current_season.fixture_fee_amount),
                "season_name": current_season.name,
                "due_date": current_season.fixture_fee_due_date
            })

class CreatePaymentIntentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payment_type = request.data.get('payment_type')
        if not payment_type:
            return Response({'error': 'A payment_type is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client_secret = create_stripe_payment_intent(payment_type, request.user)
            return Response({'client_secret': client_secret})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'An error occurred while communicating with the payment provider.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# This is the new View for handling Stripe's notifications
class StripeWebhookView(APIView):
    """
    Stripe webhook handler.
    This view does not have authentication because it's called by Stripe's servers.
    Security is handled by verifying the webhook signature.
    """
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            # Invalid payload
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return HttpResponse(status=400)

        # Handle the payment_intent.succeeded event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            user_email = payment_intent.get('receipt_email')
            description = payment_intent.get('description', '')

            if not user_email:
                return HttpResponse(status=400)
            
            try:
                user = User.objects.get(email=user_email)

                # Update the database based on the payment description
                if 'Fixture Fee' in description:
                    today = timezone.now().date()
                    current_season = Season.objects.filter(start_date__lte=today, end_date__gte=today).first()
                    if current_season:
                        # Mark the fee as paid for this user and season
                        PlayerSeasonFee.objects.update_or_create(
                            player=user,
                            season=current_season,
                            defaults={'payment_status': PlayerSeasonFee.PaymentStatus.PAID}
                        )
                        print(f"SUCCESS: Updated fixture fee for {user.email}")
                
                # You can add more 'elif' blocks here to handle other payment types
                # elif 'Social Card' in description:
                #     ... create a new social card ...

            except User.DoesNotExist:
                print(f"ERROR: User with email {user_email} not found for successful payment.")
        else:
            print(f"Unhandled event type {event['type']}")

        return HttpResponse(status=200)