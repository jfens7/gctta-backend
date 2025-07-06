# api/admin.py

from django.contrib import admin
from .models import User, SocialCard, Season, PlayerSeasonFee, AttendanceLog

# We are registering each of our models here so that they appear
# in the Django admin interface. This allows us to easily add,
# view, and edit data in our database tables.

admin.site.register(User)
admin.site.register(SocialCard)
admin.site.register(Season)
admin.site.register(PlayerSeasonFee)
admin.site.register(AttendanceLog)