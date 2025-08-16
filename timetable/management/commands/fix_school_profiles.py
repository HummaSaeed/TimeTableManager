from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from timetable.models import SchoolProfile
from datetime import time


class Command(BaseCommand):
    help = 'Fix existing school profiles with missing required fields'

    def handle(self, *args, **options):
        # Get all users without school profiles
        users_without_profiles = User.objects.filter(school_profile__isnull=True)
        
        self.stdout.write(f"Found {users_without_profiles.count()} users without school profiles")
        
        for user in users_without_profiles:
            try:
                # Create school profile with default values
                SchoolProfile.objects.create(
                    user=user,
                    school_name=f"School for {user.username}",
                    school_code=f"SCH{user.id:03d}",
                    school_start_time=time(8, 0),
                    school_end_time=time(15, 0),
                    number_of_classes=5,
                    period_duration_minutes=45,
                    total_periods_per_day=8,
                    break_time=time(12, 0),
                    friday_closing_time=time(14, 0),
                    working_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                    academic_year="2024-2025"
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Created school profile for user {user.username}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to create school profile for user {user.username}: {str(e)}")
                )
        
        # Fix existing profiles with missing required fields
        profiles_to_fix = SchoolProfile.objects.filter(
            school_start_time__isnull=True
        ) | SchoolProfile.objects.filter(
            school_end_time__isnull=True
        ) | SchoolProfile.objects.filter(
            break_time__isnull=True
        ) | SchoolProfile.objects.filter(
            friday_closing_time__isnull=True
        )
        
        self.stdout.write(f"Found {profiles_to_fix.count()} profiles with missing required fields")
        
        for profile in profiles_to_fix:
            try:
                if not profile.school_start_time:
                    profile.school_start_time = time(8, 0)
                if not profile.school_end_time:
                    profile.school_end_time = time(15, 0)
                if not profile.break_time:
                    profile.break_time = time(12, 0)
                if not profile.friday_closing_time:
                    profile.friday_closing_time = time(14, 0)
                if not profile.number_of_classes:
                    profile.number_of_classes = 5
                if not profile.period_duration_minutes:
                    profile.period_duration_minutes = 45
                if not profile.total_periods_per_day:
                    profile.total_periods_per_day = 8
                if not profile.working_days:
                    profile.working_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                if not profile.academic_year:
                    profile.academic_year = "2024-2025"
                
                profile.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Fixed school profile for user {profile.user.username}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to fix school profile for user {profile.user.username}: {str(e)}")
                )
        
        self.stdout.write(
            self.style.SUCCESS("School profile fix completed successfully!")
        ) 