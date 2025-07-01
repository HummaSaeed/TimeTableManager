from django.contrib import admin
from .models import SchoolProfile, Teacher, Subject, Class, TeacherSubjectAssignment, TimeTableSlot, SubstitutionLog, TeacherAbsence

# Register your models here.

@admin.register(SchoolProfile)
class SchoolProfileAdmin(admin.ModelAdmin):
    list_display = ['school_name', 'school_code', 'user', 'academic_year', 'created_at']
    list_filter = ['academic_year', 'timezone', 'created_at']
    search_fields = ['school_name', 'school_code', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['school_name']
    
    fieldsets = (
        ('School Information', {
            'fields': ('user', 'school_name', 'school_code', 'academic_year')
        }),
        ('Timing Configuration', {
            'fields': ('school_start_time', 'school_end_time', 'friday_closing_time', 'break_time')
        }),
        ('Class Configuration', {
            'fields': ('number_of_classes', 'sections_per_class', 'period_duration_minutes', 'total_periods_per_day')
        }),
        ('Additional Settings', {
            'fields': ('working_days', 'timezone')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'school', 'is_active', 'created_at']
    list_filter = ['is_active', 'school', 'created_at']
    search_fields = ['name', 'code', 'school__school_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    
    fieldsets = (
        ('Subject Information', {
            'fields': ('school', 'name', 'code', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Show subjects from all schools in admin"""
        return super().get_queryset(request).select_related('school')


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject_specialist', 'school', 'is_class_teacher', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_class_teacher', 'designation', 'gender', 'school', 'created_at']
    search_fields = ['name', 'email', 'subject_specialist', 'school__school_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('school', 'user', 'name', 'email', 'phone_number', 'gender')
        }),
        ('Professional Details', {
            'fields': ('subject_specialist', 'previous_subjects', 'designation', 'qualification', 'experience_years', 'date_joined')
        }),
        ('Class Teacher Assignment', {
            'fields': ('is_class_teacher', 'class_teacher_class', 'class_teacher_section')
        }),
        ('Status & Media', {
            'fields': ('is_active', 'profile_picture')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Show teachers from all schools in admin"""
        return super().get_queryset(request).select_related('school', 'user')


@admin.register(TeacherSubjectAssignment)
class TeacherSubjectAssignmentAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'subject', 'is_primary', 'max_periods_per_week', 'created_at']
    list_filter = ['is_primary', 'teacher__school', 'created_at']
    search_fields = ['teacher__name', 'subject__name', 'teacher__school__school_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['teacher__name', 'subject__name']
    autocomplete_fields = ['teacher', 'subject']


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['class_name', 'section', 'school', 'total_strength', 'class_teacher', 'is_active', 'created_at']
    list_filter = ['is_active', 'class_name', 'section', 'school', 'created_at']
    search_fields = ['class_name', 'section', 'room_number', 'school__school_name', 'class_teacher__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['class_name', 'section']
    filter_horizontal = ['subjects']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('school', 'class_name', 'section', 'total_strength', 'room_number')
        }),
        ('Schedule', {
            'fields': ('start_time', 'end_time')
        }),
        ('Teacher Assignment', {
            'fields': ('class_teacher',)
        }),
        ('Subjects', {
            'fields': ('subjects',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Show classes from all schools in admin"""
        return super().get_queryset(request).select_related('school', 'class_teacher')


@admin.register(TimeTableSlot)
class TimeTableSlotAdmin(admin.ModelAdmin):
    list_display = ['class_obj', 'subject', 'teacher', 'day', 'period_number', 'academic_year', 'is_active']
    list_filter = ['is_active', 'day', 'academic_year', 'school', 'created_at']
    search_fields = [
        'class_obj__class_name', 'class_obj__section', 
        'subject__name', 'teacher__name', 'school__school_name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['day', 'period_number', 'class_obj__class_name', 'class_obj__section']
    list_select_related = ['class_obj', 'subject', 'teacher', 'school']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'class_obj', 'subject', 'teacher', 'school'
        )


@admin.register(SubstitutionLog)
class SubstitutionLogAdmin(admin.ModelAdmin):
    list_display = ['date', 'school', 'original_teacher', 'substitute_teacher', 'timetable_slot', 'reason', 'created_at']
    list_filter = ['date', 'school', 'original_teacher', 'substitute_teacher']
    search_fields = [
        'original_teacher__name', 'substitute_teacher__name', 'school__school_name',
        'timetable_slot__class_obj__class_name', 'timetable_slot__subject__name', 'reason'
    ]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-date', 'school', 'original_teacher']
    autocomplete_fields = ['school', 'original_teacher', 'substitute_teacher', 'timetable_slot']


@admin.register(TeacherAbsence)
class TeacherAbsenceAdmin(admin.ModelAdmin):
    list_display = ['date', 'school', 'teacher', 'reason', 'created_at']
    list_filter = ['date', 'school', 'teacher']
    search_fields = ['teacher__name', 'school__school_name', 'reason']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-date', 'teacher']
    autocomplete_fields = ['school', 'teacher']
