# api/models.py

import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# This class manages how users are created
class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)  # This automatically hashes the password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, first_name, last_name, password, **extra_fields)

# This is our custom User table
class User(AbstractBaseUser, PermissionsMixin):
    class MembershipType(models.TextChoices):
        GENERIC_USER = 'GENERIC_USER', 'Generic User'
        SOCIAL_CARD_HOLDER = 'SOCIAL_CARD_HOLDER', 'Social Card Holder'
        GOLD_ANNUAL = 'GOLD_ANNUAL', 'Gold Annual'
        SILVER_ANNUAL = 'SILVER_ANNUAL', 'Silver Annual'

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    # THIS IS THE LINE I CHANGED
    dob = models.DateField(null=True, blank=True)
    membership_type = models.CharField(max_length=20, choices=MembershipType.choices, default=MembershipType.GENERIC_USER)
    is_active_annual_member = models.BooleanField(default=False)
    annual_membership_expiry_date = models.DateField(null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

# This is the Social Cards table
class SocialCard(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        USED_UP = 'USED_UP', 'Used Up'
        EXPIRED = 'EXPIRED', 'Expired'

    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_cards')
    card_id_string = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    sessions_total = models.IntegerField(default=10)
    sessions_remaining = models.IntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    def __str__(self):
        return f"{self.player.email} - {self.sessions_remaining} sessions left"

# This is the Seasons table
class Season(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    fixture_fee_amount = models.DecimalField(max_digits=6, decimal_places=2)
    fixture_fee_due_date = models.DateField()

    def __str__(self):
        return self.name

# This is the Player Season Fees table
class PlayerSeasonFee(models.Model):
    class PaymentStatus(models.TextChoices):
        PAID = 'PAID', 'Paid'
        PENDING = 'PENDING', 'Pending'
        WAIVED_GOLD = 'WAIVED_GOLD', 'Waived Gold'

    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='player_season_fees')
    season = models.ForeignKey(Season, on_delete=models.PROTECT, related_name='player_season_fees')
    payment_status = models.CharField(max_length=15, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    stripe_charge_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.player.email} - {self.season.name} - {self.payment_status}"

# This is the Attendance Logs table
class AttendanceLog(models.Model):
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_logs')
    date_of_play = models.DateField()
    entry_time = models.DateTimeField()
    exit_time = models.DateTimeField(null=True, blank=True)
    daily_session_consumed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.player.email} on {self.date_of_play}"