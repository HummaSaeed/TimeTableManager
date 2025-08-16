from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import time, datetime, timedelta

# Create your models here.

class SchoolProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='school_profile')
    school_name = models.CharField(max_length=255, default='My School')
    school_code = models.CharField(max_length=50, unique=True, default='SCH001')
    school_start_time = models.TimeField(default=time(8, 0))  # 8:00 AM
    school_end_time = models.TimeField(default=time(15, 0))  # 3:00 PM
    number_of_classes = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)], default=5)
    sections_per_class = models.JSONField(default=dict)  # e.g., {"1": ["A", "B"], "2": ["A"]}
    period_duration_minutes = models.IntegerField(validators=[MinValueValidator(30), MaxValueValidator(120)], default=45)
    total_periods_per_day = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], default=8)
    break_time = models.TimeField(default=time(12, 0))  # 12:00 PM - Main break time
    friday_closing_time = models.TimeField(default=time(14, 0))  # 2:00 PM
    working_days = models.JSONField(default=list, blank=True)  # e.g., ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    academic_year = models.CharField(max_length=20, blank=True, default='2024-2025')
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Enhanced break time configuration
    break_periods = models.JSONField(default=list, blank=True)  # e.g., [{"period": 4, "duration": 15, "name": "Short Break"}, {"period": 6, "duration": 30, "name": "Lunch Break"}]
    assembly_time = models.TimeField(default=time(8, 0))  # Assembly time before first period
    assembly_duration_minutes = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(60)], default=15)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.school_name} ({self.school_code})"

    class Meta:
        verbose_name = "School Profile"
        verbose_name_plural = "School Profiles"

    def save(self, *args, **kwargs):
        # Set default working days if not provided
        if not self.working_days:
            self.working_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        
        # Set default break periods if not provided
        if not self.break_periods:
            self.break_periods = [
                {"period": 4, "duration": 15, "name": "Short Break"},
                {"period": 6, "duration": 30, "name": "Lunch Break"}
            ]
        
        super().save(*args, **kwargs)

    def get_period_times(self, period_number):
        """
        Calculate start and end times for a given period number
        Returns: (start_time, end_time)
        """
        
        # Start from assembly time
        current_time = self.assembly_time
        
        # Add assembly duration
        if self.assembly_duration_minutes > 0:
            current_time = (datetime.combine(datetime.today(), current_time) + 
                          timedelta(minutes=self.assembly_duration_minutes)).time()
        
        # Calculate time for each period
        for period in range(1, period_number + 1):
            # Check if this period should be a break
            break_period = next((bp for bp in self.break_periods if bp['period'] == period), None)
            
            if break_period:
                # This is a break period
                break_duration = break_period['duration']
                current_time = (datetime.combine(datetime.today(), current_time) + 
                              timedelta(minutes=break_duration)).time()
            else:
                # This is a regular period
                if period > 1:
                    current_time = (datetime.combine(datetime.today(), current_time) + 
                                  timedelta(minutes=self.period_duration_minutes)).time()
        
        # Calculate end time
        end_time = (datetime.combine(datetime.today(), current_time) + 
                   timedelta(minutes=self.period_duration_minutes)).time()
        
        return current_time, end_time

    def get_break_periods_info(self):
        """
        Get information about all break periods
        Returns: List of break period information
        """
        break_info = []
        for bp in self.break_periods:
            start_time, end_time = self.get_period_times(bp['period'])
            break_info.append({
                'period': bp['period'],
                'name': bp['name'],
                'duration': bp['duration'],
                'start_time': start_time,
                'end_time': end_time
            })
        return break_info


class Subject(models.Model):
    school = models.ForeignKey(SchoolProfile, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.school.school_name})"

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        unique_together = ['school', 'code']
        ordering = ['name']


class Teacher(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    school = models.ForeignKey(SchoolProfile, on_delete=models.CASCADE, related_name='teachers')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile', null=True, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    subject_specialist = models.CharField(max_length=255)
    previous_subjects = models.JSONField(default=list, blank=True)  # List of previous subjects taught
    designation = models.CharField(max_length=100)
    qualification = models.CharField(max_length=255)
    is_class_teacher = models.BooleanField(default=False)
    class_teacher_class = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(20)])
    class_teacher_section = models.CharField(max_length=10, blank=True, null=True)
    
    # Optional fields for future features
    phone_number = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    date_joined = models.DateField(null=True, blank=True)
    experience_years = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(50)], null=True, blank=True)
    profile_picture = models.ImageField(upload_to='teacher_profiles/', blank=True, null=True)
    
    # Status field
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.school.school_name}"

    class Meta:
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"
        ordering = ['name']

    def clean(self):
        from django.core.exceptions import ValidationError
        # Validate that class teacher fields are provided when is_class_teacher is True
        if self.is_class_teacher:
            if not self.class_teacher_class:
                raise ValidationError("Class teacher class must be specified when teacher is a class teacher.")
            if not self.class_teacher_section:
                raise ValidationError("Class teacher section must be specified when teacher is a class teacher.")
        
        # Validate that class teacher fields are not provided when is_class_teacher is False
        if not self.is_class_teacher:
            if self.class_teacher_class or self.class_teacher_section:
                raise ValidationError("Class teacher fields should not be specified when teacher is not a class teacher.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class TeacherSubjectAssignment(models.Model):
    """Model to track which teachers can teach which subjects"""
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='subject_assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='teacher_assignments')
    is_primary = models.BooleanField(default=True)  # Primary teacher for this subject
    max_periods_per_week = models.IntegerField(default=20, validators=[MinValueValidator(1), MaxValueValidator(40)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.teacher.name} - {self.subject.name}"

    class Meta:
        verbose_name = "Teacher Subject Assignment"
        verbose_name_plural = "Teacher Subject Assignments"
        unique_together = ['teacher', 'subject']
        ordering = ['teacher__name', 'subject__name']

    def clean(self):
        from django.core.exceptions import ValidationError
        # Validate that teacher and subject belong to the same school
        if self.teacher.school != self.subject.school:
            raise ValidationError("Teacher and subject must belong to the same school.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Class(models.Model):
    school = models.ForeignKey(SchoolProfile, on_delete=models.CASCADE, related_name='classes')
    class_name = models.CharField(max_length=50)  # e.g., "Class 10", "Grade 5"
    section = models.CharField(max_length=10)  # e.g., "A", "B", "C"
    total_strength = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    room_number = models.CharField(max_length=20)
    class_teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_classes')
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    subjects = models.ManyToManyField(Subject, related_name='classes', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.class_name} - {self.section} ({self.school.school_name})"

    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"
        unique_together = ['school', 'class_name', 'section']
        ordering = ['class_name', 'section']

    def clean(self):
        from django.core.exceptions import ValidationError
        # Validate that class teacher belongs to the same school
        if self.class_teacher and self.class_teacher.school != self.school:
            raise ValidationError("Class teacher must belong to the same school.")
        
        # Validate that class teacher is active
        if self.class_teacher and not self.class_teacher.is_active:
            raise ValidationError("Class teacher must be active.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class TimeTableSlot(models.Model):
    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
    ]

    school = models.ForeignKey(SchoolProfile, on_delete=models.CASCADE, related_name='timetable_slots')
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='timetable_slots')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='timetable_slots')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='timetable_slots')
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    period_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    academic_year = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Period timing fields
    period_start_time = models.TimeField(null=True, blank=True)  # Actual start time of this period
    period_end_time = models.TimeField(null=True, blank=True)    # Actual end time of this period
    is_break_period = models.BooleanField(default=False)         # Whether this is a break period
    break_name = models.CharField(max_length=50, blank=True)     # Name of break (e.g., "Lunch Break", "Short Break")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.class_obj.class_name}-{self.class_obj.section} | {self.subject.name} | {self.teacher.name} | {self.day} P{self.period_number}"

    class Meta:
        verbose_name = "Time Table Slot"
        verbose_name_plural = "Time Table Slots"
        unique_together = ['school', 'class_obj', 'day', 'period_number', 'academic_year']
        ordering = ['day', 'period_number', 'class_obj__class_name', 'class_obj__section']

    def clean(self):
        from django.core.exceptions import ValidationError
        # Validate that all entities belong to the same school
        if (self.class_obj.school != self.school or 
            self.subject.school != self.school or 
            self.teacher.school != self.school):
            raise ValidationError("All entities must belong to the same school.")
        
        # Validate that subject is assigned to the class
        if self.subject not in self.class_obj.subjects.all():
            raise ValidationError("Subject must be assigned to the class.")
        
        # Validate that teacher can teach this subject
        if not TeacherSubjectAssignment.objects.filter(teacher=self.teacher, subject=self.subject).exists():
            raise ValidationError("Teacher must be assigned to teach this subject.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class SubstitutionLog(models.Model):
    school = models.ForeignKey(SchoolProfile, on_delete=models.CASCADE, related_name='substitution_logs')
    original_teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='original_substitutions')
    substitute_teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='substitute_assignments')
    timetable_slot = models.ForeignKey(TimeTableSlot, on_delete=models.CASCADE, related_name='substitution_logs')
    date = models.DateField()  # The date of substitution
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.date}: {self.original_teacher.name} → {self.substitute_teacher.name} ({self.timetable_slot})"

    class Meta:
        verbose_name = "Substitution Log"
        verbose_name_plural = "Substitution Logs"
        ordering = ['-date', 'timetable_slot']


class TeacherAbsence(models.Model):
    school = models.ForeignKey(SchoolProfile, on_delete=models.CASCADE, related_name='teacher_absences')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='absences')
    date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.teacher.name} absent on {self.date}" 

    class Meta:
        verbose_name = "Teacher Absence"
        verbose_name_plural = "Teacher Absences"
        unique_together = ['teacher', 'date']
        ordering = ['-date', 'teacher']
