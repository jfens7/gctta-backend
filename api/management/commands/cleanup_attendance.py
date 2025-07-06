# api/management/commands/cleanup_attendance.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from api.models import AttendanceLog

class Command(BaseCommand):
    help = 'Finds attendance logs from the previous day with no exit_time and updates them to 11:59 PM.'

    def handle(self, *args, **options):
        yesterday = timezone.now().date() - timedelta(days=1)

        self.stdout.write(f"Starting cleanup job for date: {yesterday}...")

        # This represents 11:59:59 PM of the previous day
        end_of_yesterday = timezone.make_aware(
            timezone.datetime.combine(yesterday, timezone.datetime.max.time())
        )

        # Find all logs from yesterday where exit_time is NULL
        logs_to_update = AttendanceLog.objects.filter(
            date_of_play=yesterday,
            exit_time__isnull=True
        )

        # Update the found records with the end-of-day timestamp
        count = logs_to_update.update(exit_time=end_of_yesterday)

        if count > 0:
            self.stdout.write(self.style.SUCCESS(f"Successfully cleaned up {count} attendance log(s)."))
        else:
            self.stdout.write("No attendance logs needed cleanup for yesterday.")