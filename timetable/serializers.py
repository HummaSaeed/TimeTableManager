from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
import secrets
import string
from .models import SchoolProfile, Teacher, Subject, Class, TeacherSubjectAssignment, TimeTableSlot


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class SchoolProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = SchoolProfile
        fields = [
            'id', 'user_email', 'school_name', 'school_code', 'school_start_time',
            'school_end_time', 'number_of_classes', 'sections_per_class',
            'period_duration_minutes', 'total_periods_per_day', 'break_time',
            'friday_closing_time', 'working_days', 'academic_year', 'timezone',
            'break_periods', 'assembly_time', 'assembly_duration_minutes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_school_code(self, value):
        # Check if school_code is unique (excluding current instance if updating)
        user = self.context['request'].user
        qs = SchoolProfile.objects.filter(school_code=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("School code must be unique.")
        return value


class SubjectSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.school_name', read_only=True)

    class Meta:
        model = Subject
        fields = [
            'id', 'school', 'school_name', 'name', 'code', 'description', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'school', 'created_at', 'updated_at']

    def validate_code(self, value):
        # Check if subject code is unique within the school
        user = self.context['request'].user
        school = user.school_profile
        existing_subject = Subject.objects.filter(school=school, code=value)
        if self.instance:
            existing_subject = existing_subject.exclude(pk=self.instance.pk)
        if existing_subject.exists():
            raise serializers.ValidationError("Subject code must be unique within the school.")
        return value

    def create(self, validated_data):
        # Automatically set the school to the authenticated user's school
        validated_data['school'] = self.context['request'].user.school_profile
        return super().create(validated_data)


class SubjectListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing subjects"""
    school_name = serializers.CharField(source='school.school_name', read_only=True)

    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'is_active', 'created_at', 'school_name']
        read_only_fields = ['id', 'created_at']


class TeacherSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.school_name', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    generated_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Teacher
        fields = [
            'id', 'school', 'school_name', 'user', 'name', 'email', 'subject_specialist', 
            'previous_subjects', 'designation', 'qualification', 'is_class_teacher', 
            'class_teacher_class', 'class_teacher_section', 'phone_number', 'gender', 
            'gender_display', 'date_joined', 'experience_years', 'profile_picture', 
            'is_active', 'created_at', 'updated_at', 'generated_password'
        ]
        read_only_fields = ['id', 'school', 'user', 'created_at', 'updated_at']

    def validate(self, attrs):
        # Validate class teacher fields
        is_class_teacher = attrs.get('is_class_teacher', getattr(self.instance, 'is_class_teacher', False))
        class_teacher_class = attrs.get('class_teacher_class', getattr(self.instance, 'class_teacher_class', None))
        class_teacher_section = attrs.get('class_teacher_section', getattr(self.instance, 'class_teacher_section', None))

        if is_class_teacher:
            if not class_teacher_class:
                raise serializers.ValidationError("Class teacher class must be specified when teacher is a class teacher.")
            if not class_teacher_section:
                raise serializers.ValidationError("Class teacher section must be specified when teacher is a class teacher.")
        else:
            # If not class teacher, ignore class_teacher_* fields
            attrs.pop('class_teacher_class', None)
            attrs.pop('class_teacher_section', None)

        # Validate email uniqueness
        email = attrs.get('email')
        if email:
            existing_teacher = Teacher.objects.filter(email=email)
            if self.instance:
                existing_teacher = existing_teacher.exclude(pk=self.instance.pk)
            if existing_teacher.exists():
                raise serializers.ValidationError("A teacher with this email already exists.")

        return attrs

    def create(self, validated_data):
        # Generate secure random password
        password = self.generate_secure_password()
        validated_data['generated_password'] = password
        
        # Create user account
        email = validated_data['email']
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=validated_data['name'].split()[0] if validated_data['name'] else '',
            last_name=' '.join(validated_data['name'].split()[1:]) if len(validated_data['name'].split()) > 1 else ''
        )
        
        # Automatically set the school to the authenticated user's school
        validated_data['school'] = self.context['request'].user.school_profile
        validated_data['user'] = user
        
        # Remove generated_password from validated_data before creating teacher
        validated_data.pop('generated_password', None)
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # If toggled off class teacher, clear class fields on instance
        is_class_teacher = validated_data.get('is_class_teacher', instance.is_class_teacher)
        if not is_class_teacher:
            validated_data['class_teacher_class'] = None
            validated_data['class_teacher_section'] = None
        return super().update(instance, validated_data)

    def generate_secure_password(self):
        """Generate a secure random password"""
        # Generate a 12-character password with letters, digits, and symbols
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        while True:
            password = ''.join(secrets.choice(alphabet) for i in range(12))
            # Ensure password has at least one of each character type
            if (any(c.islower() for c in password)
                    and any(c.isupper() for c in password)
                    and any(c.isdigit() for c in password)
                    and any(c in "!@#$%^&*" for c in password)):
                return password


class TeacherListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing teachers"""
    school_name = serializers.CharField(source='school.school_name', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)

    class Meta:
        model = Teacher
        fields = [
            'id', 'school_name', 'name', 'email', 'subject_specialist', 'designation', 'is_class_teacher',
            'class_teacher_class', 'class_teacher_section', 'is_active', 'created_at', 'gender_display'
        ]
        read_only_fields = ['id', 'created_at']


class TeacherLoginSerializer(serializers.Serializer):
    """Serializer for teacher login"""
    email = serializers.EmailField()
    password = serializers.CharField()


class TeacherPasswordResetSerializer(serializers.Serializer):
    """Serializer for teacher password reset"""
    email = serializers.EmailField()


class TeacherSubjectAssignmentSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    school_name = serializers.CharField(source='teacher.school.school_name', read_only=True)

    class Meta:
        model = TeacherSubjectAssignment
        fields = [
            'id', 'teacher', 'teacher_name', 'subject', 'subject_name', 'school_name',
            'is_primary', 'max_periods_per_week', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        # Validate that teacher and subject belong to the same school
        teacher = attrs.get('teacher')
        subject = attrs.get('subject')
        
        if teacher and subject and teacher.school != subject.school:
            raise serializers.ValidationError("Teacher and subject must belong to the same school.")
        
        return attrs


class TeacherSubjectAssignmentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing teacher subject assignments"""
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = TeacherSubjectAssignment
        fields = [
            'id', 'teacher_name', 'subject_name', 'is_primary', 
            'max_periods_per_week', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ClassSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.school_name', read_only=True)
    class_teacher_name = serializers.CharField(source='class_teacher.name', read_only=True)
    subjects_list = SubjectListSerializer(source='subjects', many=True, read_only=True)

    class Meta:
        model = Class
        fields = [
            'id', 'school', 'school_name', 'class_name', 'section', 'total_strength',
            'room_number', 'class_teacher', 'class_teacher_name', 'start_time', 'end_time',
            'subjects', 'subjects_list', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'school', 'created_at', 'updated_at']

    def validate(self, attrs):
        # Validate that class_name and section combination is unique within the school
        user = self.context['request'].user
        school = user.school_profile
        class_name = attrs.get('class_name')
        section = attrs.get('section')
        
        if class_name and section:
            existing_class = Class.objects.filter(
                school=school, 
                class_name=class_name, 
                section=section
            )
            if self.instance:
                existing_class = existing_class.exclude(pk=self.instance.pk)
            if existing_class.exists():
                raise serializers.ValidationError("A class with this name and section already exists in your school.")

        # Validate that class teacher belongs to the same school
        class_teacher = attrs.get('class_teacher')
        if class_teacher and class_teacher.school != school:
            raise serializers.ValidationError("Class teacher must belong to your school.")

        # Validate that class teacher is active
        if class_teacher and not class_teacher.is_active:
            raise serializers.ValidationError("Class teacher must be active.")

        return attrs

    def create(self, validated_data):
        # Automatically set the school to the authenticated user's school
        validated_data['school'] = self.context['request'].user.school_profile
        return super().create(validated_data)


class ClassListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing classes"""
    school_name = serializers.CharField(source='school.school_name', read_only=True)
    class_teacher_name = serializers.CharField(source='class_teacher.name', read_only=True)
    subjects_count = serializers.SerializerMethodField()

    class Meta:
        model = Class
        fields = [
            'id', 'school_name', 'class_name', 'section', 'total_strength', 'room_number',
            'class_teacher_name', 'subjects_count', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_subjects_count(self, obj):
        return obj.subjects.count()


class TimeTableSlotSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.school_name', read_only=True)
    class_name = serializers.CharField(source='class_obj.class_name', read_only=True)
    class_section = serializers.CharField(source='class_obj.section', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)

    class Meta:
        model = TimeTableSlot
        fields = [
            'id', 'school', 'school_name', 'class_obj', 'class_name', 'class_section',
            'subject', 'subject_name', 'teacher', 'teacher_name', 'day', 'period_number',
            'academic_year', 'is_active', 'period_start_time', 'period_end_time',
            'is_break_period', 'break_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'school', 'created_at', 'updated_at']

    def validate(self, attrs):
        # Validate that all entities belong to the same school
        user = self.context['request'].user
        school = user.school_profile
        
        class_obj = attrs.get('class_obj')
        subject = attrs.get('subject')
        teacher = attrs.get('teacher')
        
        if class_obj and class_obj.school != school:
            raise serializers.ValidationError("Class must belong to your school.")
        
        if subject and subject.school != school:
            raise serializers.ValidationError("Subject must belong to your school.")
        
        if teacher and teacher.school != school:
            raise serializers.ValidationError("Teacher must belong to your school.")
        
        # Validate that subject is assigned to the class
        if class_obj and subject and subject not in class_obj.subjects.all():
            raise serializers.ValidationError("Subject must be assigned to the class.")
        
        # Validate that teacher can teach this subject
        if teacher and subject and not TeacherSubjectAssignment.objects.filter(teacher=teacher, subject=subject).exists():
            raise serializers.ValidationError("Teacher must be assigned to teach this subject.")
        
        return attrs

    def create(self, validated_data):
        # Automatically set the school to the authenticated user's school
        validated_data['school'] = self.context['request'].user.school_profile
        return super().create(validated_data)


class TimeTableSlotListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing timetable slots"""
    class_name = serializers.CharField(source='class_obj.class_name', read_only=True)
    class_section = serializers.CharField(source='class_obj.section', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)

    class Meta:
        model = TimeTableSlot
        fields = [
            'id', 'class_name', 'class_section', 'subject_name', 'teacher_name',
            'day', 'period_number', 'is_active', 'period_start_time', 'period_end_time',
            'is_break_period', 'break_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TimetableGenerationSerializer(serializers.Serializer):
    """Serializer for timetable generation request"""
    academic_year = serializers.CharField(max_length=20, required=False, allow_blank=True)
    clear_existing = serializers.BooleanField(default=True)
    max_attempts = serializers.IntegerField(default=100, min_value=1, max_value=1000) 