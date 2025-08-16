from django.shortcuts import render
from rest_framework import status, generics, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.core.management import call_command
from django.core.management.base import CommandError
import random
from collections import defaultdict, Counter
import secrets
import string
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, SchoolProfileSerializer, 
    TeacherSerializer, TeacherListSerializer, TeacherLoginSerializer, TeacherPasswordResetSerializer,
    SubjectSerializer, SubjectListSerializer, ClassSerializer, ClassListSerializer,
    TeacherSubjectAssignmentSerializer, TeacherSubjectAssignmentListSerializer,
    TimeTableSlotSerializer, TimeTableSlotListSerializer, TimetableGenerationSerializer
)
from .models import SchoolProfile, Teacher, Subject, Class, TeacherSubjectAssignment, TimeTableSlot, TeacherAbsence, SubstitutionLog
from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework import serializers
from drf_yasg.utils import swagger_auto_schema

# Create your views here.

@swagger_auto_schema(method='post', request_body=UserRegistrationSerializer)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_school(request):
    """Register a new school with email and password"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'School registered successfully',
            'user_id': user.id,
            'email': user.email,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='post', request_body=UserLoginSerializer)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_school(request):
    """Login with email and password, return access token"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        # Try to authenticate with email as username
        user = authenticate(username=email, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Login successful',
                'user_id': user.id,
                'email': user.email,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def teacher_login(request):
    """Teacher login with email and password"""
    serializer = TeacherLoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        # Try to authenticate with email as username
        user = authenticate(username=email, password=password)
        
        if user and hasattr(user, 'teacher_profile'):
            teacher = user.teacher_profile
            if teacher.is_active:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': 'Teacher login successful',
                    'teacher_id': teacher.id,
                    'name': teacher.name,
                    'email': teacher.email,
                    'school_name': teacher.school.school_name,
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh)
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Teacher account is deactivated'
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({
                'error': 'Invalid credentials or teacher not found'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def teacher_password_reset(request):
    """Reset teacher password and send via email"""
    serializer = TeacherPasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        try:
            teacher = Teacher.objects.get(email=email, is_active=True)
            user = teacher.user
            
            # Generate new secure password
            new_password = generate_secure_password()
            user.password = make_password(new_password)
            user.save()
            
            # Send email with new password
            try:
                send_mail(
                    subject='Password Reset - Timetable Management System',
                    message=f'''
                    Hello {teacher.name},
                    
                    Your password has been reset. Your new password is:
                    
                    {new_password}
                    
                    Please change this password after your next login for security.
                    
                    Best regards,
                    {teacher.school.school_name} Administration
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                return Response({
                    'message': 'Password reset email sent successfully'
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({
                    'error': 'Failed to send email. Please contact administrator.',
                    'new_password': new_password  # Show password in response as fallback
                }, status=status.HTTP_200_OK)
                
        except Teacher.DoesNotExist:
            return Response({
                'error': 'Teacher not found or account is deactivated'
            }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def generate_secure_password():
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(12))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in "!@#$%^&*" for c in password)):
            return password


class SchoolProfileView(generics.RetrieveUpdateAPIView):
    """View and update school profile"""
    serializer_class = SchoolProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Only get; do NOT auto-create since schools already have their code
        return SchoolProfile.objects.get(user=self.request.user)

    def get(self, request, *args, **kwargs):
        """Get school profile"""
        try:
            profile = self.get_object()
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except SchoolProfile.DoesNotExist:
            return Response({'error': 'School profile not found. Please create it by updating with school_name and school_code.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Failed to retrieve school profile: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, *args, **kwargs):
        """Create or update school profile (full update)"""
        try:
            try:
                profile = self.get_object()
                serializer = self.get_serializer(profile, data=request.data, partial=False)
                action = 'updated'
            except SchoolProfile.DoesNotExist:
                serializer = self.get_serializer(data=request.data)
                action = 'created'

            if serializer.is_valid():
                if action == 'created':
                    # Create with current user
                    profile = SchoolProfile.objects.create(user=request.user, **serializer.validated_data)
                    data = self.get_serializer(profile).data
                else:
                    profile = serializer.save()
                    data = serializer.data
                return Response({'message': f'School profile {action} successfully', 'data': data})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Failed to update school profile: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, *args, **kwargs):
        """Partially create or update school profile"""
        try:
            try:
                profile = self.get_object()
                serializer = self.get_serializer(profile, data=request.data, partial=True)
                action = 'updated'
                if serializer.is_valid():
                    profile = serializer.save()
                    return Response({'message': f'School profile {action} successfully', 'data': serializer.data})
            except SchoolProfile.DoesNotExist:
                # Create with provided partial data, letting model defaults fill the rest
                serializer = self.get_serializer(data=request.data, partial=True)
                if serializer.is_valid():
                    profile = SchoolProfile.objects.create(user=request.user, **serializer.validated_data)
                    return Response({'message': 'School profile created successfully', 'data': self.get_serializer(profile).data})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Failed to update school profile: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeacherListView(generics.ListCreateAPIView):
    """List all teachers and create new teacher"""
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_class_teacher', 'designation', 'gender']
    search_fields = ['name', 'subject_specialist', 'email']
    ordering_fields = ['name', 'created_at', 'experience_years']
    ordering = ['name']

    def get_queryset(self):
        """Filter teachers by the authenticated school"""
        try:
            return Teacher.objects.filter(school=self.request.user.school_profile)
        except SchoolProfile.DoesNotExist:
            # Return empty queryset if no school profile exists
            return Teacher.objects.none()

    def get_serializer_class(self):
        """Use different serializers for list and create"""
        if self.request.method == 'GET':
            return TeacherListSerializer
        return TeacherSerializer

    def list(self, request, *args, **kwargs):
        """Custom list response with count"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """Create a new teacher with automatic user account creation"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            teacher = serializer.save()
            
            # Get the generated password from the serializer
            generated_password = getattr(serializer, 'generated_password', None)
            
            response_data = {
                'message': 'Teacher created successfully',
                'data': TeacherSerializer(teacher).data,
                'login_credentials': {
                    'email': teacher.email,
                    'password': generated_password,
                    'note': 'Please save this password securely. It will not be shown again.'
                }
            }
            
            # Try to send email with credentials
            try:
                send_mail(
                    subject='Welcome to Timetable Management System',
                    message=f'''
                    Hello {teacher.name},
                    
                    Welcome to {teacher.school.school_name}! Your account has been created successfully.
                    
                    Your login credentials:
                    Email: {teacher.email}
                    Password: {generated_password}
                    
                    Please change your password after your first login for security.
                    
                    Best regards,
                    {teacher.school.school_name} Administration
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[teacher.email],
                    fail_silently=True,
                )
                response_data['email_sent'] = True
            except Exception as e:
                response_data['email_sent'] = False
                response_data['email_error'] = 'Failed to send welcome email'
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific teacher"""
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter teachers by the authenticated school"""
        return Teacher.objects.filter(school=self.request.user.school_profile)

    def retrieve(self, request, *args, **kwargs):
        """Get teacher details"""
        teacher = self.get_object()
        serializer = self.get_serializer(teacher)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update teacher"""
        teacher = self.get_object()
        serializer = self.get_serializer(teacher, data=request.data, partial=kwargs.get('partial', False))
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Teacher updated successfully',
                'data': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Soft delete teacher by setting is_active to False"""
        teacher = self.get_object()
        teacher.is_active = False
        teacher.save()
        return Response({
            'message': 'Teacher deactivated successfully'
        }, status=status.HTTP_200_OK)


class TeacherActivateView(generics.UpdateAPIView):
    """Activate a deactivated teacher"""
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter teachers by the authenticated school"""
        return Teacher.objects.filter(school=self.request.user.school_profile)

    def update(self, request, *args, **kwargs):
        """Activate teacher by setting is_active to True"""
        teacher = self.get_object()
        teacher.is_active = True
        teacher.save()
        serializer = self.get_serializer(teacher)
        return Response({
            'message': 'Teacher activated successfully',
            'data': serializer.data
        })


class TeacherStatsView(generics.GenericAPIView):
    """Get teacher statistics for the school"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get teacher statistics"""
        school = request.user.school_profile
        teachers = Teacher.objects.filter(school=school)
        
        stats = {
            'total_teachers': teachers.count(),
            'active_teachers': teachers.filter(is_active=True).count(),
            'inactive_teachers': teachers.filter(is_active=False).count(),
            'class_teachers': teachers.filter(is_class_teacher=True, is_active=True).count(),
            'subject_teachers': teachers.filter(is_class_teacher=False, is_active=True).count(),
            'by_designation': {},
            'by_gender': {},
        }
        
        # Count by designation
        for teacher in teachers.filter(is_active=True):
            designation = teacher.designation
            stats['by_designation'][designation] = stats['by_designation'].get(designation, 0) + 1
        
        # Count by gender
        for teacher in teachers.filter(is_active=True):
            gender = teacher.get_gender_display() if teacher.gender else 'Not Specified'
            stats['by_gender'][gender] = stats['by_gender'].get(gender, 0) + 1
        
        return Response(stats)


# Subject Management Views
class SubjectListView(generics.ListCreateAPIView):
    """List all subjects and create new subject"""
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """Filter subjects by the authenticated school"""
        try:
            return Subject.objects.filter(school=self.request.user.school_profile)
        except SchoolProfile.DoesNotExist:
            # Return empty queryset if no school profile exists
            return Subject.objects.none()

    def get_serializer_class(self):
        """Use different serializers for list and create"""
        if self.request.method == 'GET':
            return SubjectListSerializer
        return SubjectSerializer

    def list(self, request, *args, **kwargs):
        """Custom list response with count"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """Create a new subject"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            subject = serializer.save()
            return Response({
                'message': 'Subject created successfully',
                'data': SubjectSerializer(subject).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific subject"""
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter subjects by the authenticated school"""
        return Subject.objects.filter(school=self.request.user.school_profile)

    def retrieve(self, request, *args, **kwargs):
        """Get subject details"""
        subject = self.get_object()
        serializer = self.get_serializer(subject)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update subject"""
        subject = self.get_object()
        serializer = self.get_serializer(subject, data=request.data, partial=kwargs.get('partial', False))
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Subject updated successfully',
                'data': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Soft delete subject by setting is_active to False"""
        subject = self.get_object()
        subject.is_active = False
        subject.save()
        return Response({
            'message': 'Subject deactivated successfully'
        }, status=status.HTTP_200_OK)


class SubjectActivateView(generics.UpdateAPIView):
    """Activate a deactivated subject"""
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter subjects by the authenticated school"""
        return Subject.objects.filter(school=self.request.user.school_profile)

    def update(self, request, *args, **kwargs):
        """Activate subject by setting is_active to True"""
        subject = self.get_object()
        subject.is_active = True
        subject.save()
        serializer = self.get_serializer(subject)
        return Response({
            'message': 'Subject activated successfully',
            'data': serializer.data
        })


# Class Management Views
class ClassListView(generics.ListCreateAPIView):
    """List all classes and create new class"""
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'class_name', 'section']
    search_fields = ['class_name', 'section', 'room_number']
    ordering_fields = ['class_name', 'section', 'total_strength', 'created_at']
    ordering = ['class_name', 'section']

    def get_queryset(self):
        """Filter classes by the authenticated school"""
        try:
            return Class.objects.filter(school=self.request.user.school_profile)
        except SchoolProfile.DoesNotExist:
            # Return empty queryset if no school profile exists
            return Class.objects.none()

    def get_serializer_class(self):
        """Use different serializers for list and create"""
        if self.request.method == 'GET':
            return ClassListSerializer
        return ClassSerializer

    def list(self, request, *args, **kwargs):
        """Custom list response with count"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """Create a new class"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            class_obj = serializer.save()
            return Response({
                'message': 'Class created successfully',
                'data': ClassSerializer(class_obj).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClassDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific class"""
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter classes by the authenticated school"""
        return Class.objects.filter(school=self.request.user.school_profile)

    def retrieve(self, request, *args, **kwargs):
        """Get class details"""
        class_obj = self.get_object()
        serializer = self.get_serializer(class_obj)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update class"""
        class_obj = self.get_object()
        serializer = self.get_serializer(class_obj, data=request.data, partial=kwargs.get('partial', False))
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Class updated successfully',
                'data': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Soft delete class by setting is_active to False"""
        class_obj = self.get_object()
        class_obj.is_active = False
        class_obj.save()
        return Response({
            'message': 'Class deactivated successfully'
        }, status=status.HTTP_200_OK)


class ClassActivateView(generics.UpdateAPIView):
    """Activate a deactivated class"""
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter classes by the authenticated school"""
        return Class.objects.filter(school=self.request.user.school_profile)

    def update(self, request, *args, **kwargs):
        """Activate class by setting is_active to True"""
        class_obj = self.get_object()
        class_obj.is_active = True
        class_obj.save()
        serializer = self.get_serializer(class_obj)
        return Response({
            'message': 'Class activated successfully',
            'data': serializer.data
        })


class ClassStatsView(generics.GenericAPIView):
    """Get class statistics for the school"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get class statistics"""
        school = request.user.school_profile
        classes = Class.objects.filter(school=school)
        
        stats = {
            'total_classes': classes.count(),
            'active_classes': classes.filter(is_active=True).count(),
            'inactive_classes': classes.filter(is_active=False).count(),
            'total_students': classes.filter(is_active=True).aggregate(
                total=models.Sum('total_strength')
            )['total'] or 0,
            'by_class_name': {},
            'by_section': {},
            'classes_with_teachers': classes.filter(is_active=True, class_teacher__isnull=False).count(),
            'classes_without_teachers': classes.filter(is_active=True, class_teacher__isnull=True).count(),
        }
        
        # Count by class name
        for class_obj in classes.filter(is_active=True):
            class_name = class_obj.class_name
            stats['by_class_name'][class_name] = stats['by_class_name'].get(class_name, 0) + 1
        
        # Count by section
        for class_obj in classes.filter(is_active=True):
            section = class_obj.section
            stats['by_section'][section] = stats['by_section'].get(section, 0) + 1
        
        return Response(stats)


# Teacher Subject Assignment Views
class TeacherSubjectAssignmentListView(generics.ListCreateAPIView):
    """List all teacher subject assignments and create new ones"""
    serializer_class = TeacherSubjectAssignmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_primary', 'teacher', 'subject']
    search_fields = ['teacher__name', 'subject__name']
    ordering_fields = ['teacher__name', 'subject__name', 'created_at']
    ordering = ['teacher__name', 'subject__name']

    def get_queryset(self):
        """Filter assignments by the authenticated school"""
        return TeacherSubjectAssignment.objects.filter(
            teacher__school=self.request.user.school_profile
        ).select_related('teacher', 'subject')

    def get_serializer_class(self):
        """Use different serializers for list and create"""
        if self.request.method == 'GET':
            return TeacherSubjectAssignmentListSerializer
        return TeacherSubjectAssignmentSerializer

    def list(self, request, *args, **kwargs):
        """Custom list response with count"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """Create a new teacher subject assignment"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            assignment = serializer.save()
            return Response({
                'message': 'Teacher subject assignment created successfully',
                'data': TeacherSubjectAssignmentSerializer(assignment).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherSubjectAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific teacher subject assignment"""
    serializer_class = TeacherSubjectAssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter assignments by the authenticated school"""
        return TeacherSubjectAssignment.objects.filter(
            teacher__school=self.request.user.school_profile
        ).select_related('teacher', 'subject')

    def retrieve(self, request, *args, **kwargs):
        """Get assignment details"""
        assignment = self.get_object()
        serializer = self.get_serializer(assignment)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update assignment"""
        assignment = self.get_object()
        serializer = self.get_serializer(assignment, data=request.data, partial=kwargs.get('partial', False))
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Teacher subject assignment updated successfully',
                'data': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Delete teacher subject assignment"""
        assignment = self.get_object()
        assignment.delete()
        return Response({
            'message': 'Teacher subject assignment deleted successfully'
        }, status=status.HTTP_200_OK)


# Timetable Views
class TimeTableSlotListView(generics.ListCreateAPIView):
    """List all timetable slots and create new ones"""
    serializer_class = TimeTableSlotSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'day', 'class_obj', 'subject', 'teacher']
    search_fields = ['class_obj__class_name', 'class_obj__section', 'subject__name', 'teacher__name']
    ordering_fields = ['day', 'period_number', 'class_obj__class_name', 'created_at']
    ordering = ['day', 'period_number', 'class_obj__class_name', 'class_obj__section']

    def get_queryset(self):
        """Filter slots by the authenticated school"""
        return TimeTableSlot.objects.filter(
            school=self.request.user.school_profile
        ).select_related('class_obj', 'subject', 'teacher')

    def get_serializer_class(self):
        """Use different serializers for list and create"""
        if self.request.method == 'GET':
            return TimeTableSlotListSerializer
        return TimeTableSlotSerializer

    def list(self, request, *args, **kwargs):
        """Custom list response with count"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """Create a new timetable slot"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            slot = serializer.save()
            return Response({
                'message': 'Timetable slot created successfully',
                'data': TimeTableSlotSerializer(slot).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TimeTableSlotDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific timetable slot"""
    serializer_class = TimeTableSlotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter slots by the authenticated school"""
        return TimeTableSlot.objects.filter(
            school=self.request.user.school_profile
        ).select_related('class_obj', 'subject', 'teacher')

    def retrieve(self, request, *args, **kwargs):
        """Get slot details"""
        slot = self.get_object()
        serializer = self.get_serializer(slot)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update slot"""
        slot = self.get_object()
        serializer = self.get_serializer(slot, data=request.data, partial=kwargs.get('partial', False))
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Timetable slot updated successfully',
                'data': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Delete timetable slot"""
        slot = self.get_object()
        slot.delete()
        return Response({
            'message': 'Timetable slot deleted successfully'
        }, status=status.HTTP_200_OK)


class GenerateTimetableView(generics.GenericAPIView):
    """Generate automated timetable"""
    serializer_class = TimetableGenerationSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Generate timetable using the management command"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            academic_year = serializer.validated_data.get('academic_year', '')
            clear_existing = serializer.validated_data.get('clear_existing', True)
            max_attempts = serializer.validated_data.get('max_attempts', 100)
            
            school = request.user.school_profile
            
            try:
                # Call the management command
                from io import StringIO
                from django.core.management import call_command
                
                out = StringIO()
                call_command(
                    'generate_timetable',
                    school_id=school.id,
                    academic_year=academic_year,
                    clear_existing=clear_existing,
                    max_attempts=max_attempts,
                    stdout=out
                )
                
                output = out.getvalue()
                
                # Count created slots
                slots_count = TimeTableSlot.objects.filter(
                    school=school, 
                    academic_year=academic_year
                ).count()
                
                return Response({
                    'message': 'Timetable generated successfully',
                    'slots_created': slots_count,
                    'output': output,
                    'academic_year': academic_year
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({
                    'error': f'Failed to generate timetable: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TimetableStatsView(generics.GenericAPIView):
    """Get timetable statistics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get timetable statistics"""
        school = request.user.school_profile
        academic_year = request.query_params.get('academic_year', '')
        
        slots = TimeTableSlot.objects.filter(school=school)
        if academic_year:
            slots = slots.filter(academic_year=academic_year)
        
        stats = {
            'total_slots': slots.count(),
            'by_day': {},
            'by_class': {},
            'by_subject': {},
            'by_teacher': {},
            'conflicts': self.check_conflicts(school, academic_year)
        }
        
        # Count by day
        for slot in slots:
            day = slot.day
            stats['by_day'][day] = stats['by_day'].get(day, 0) + 1
        
        # Count by class
        for slot in slots:
            class_name = f"{slot.class_obj.class_name}-{slot.class_obj.section}"
            stats['by_class'][class_name] = stats['by_class'].get(class_name, 0) + 1
        
        # Count by subject
        for slot in slots:
            subject = slot.subject.name
            stats['by_subject'][subject] = stats['by_subject'].get(subject, 0) + 1
        
        # Count by teacher
        for slot in slots:
            teacher = slot.teacher.name
            stats['by_teacher'][teacher] = stats['by_teacher'].get(teacher, 0) + 1
        
        return Response(stats)

    def check_conflicts(self, school, academic_year):
        """Check for timetable conflicts"""
        slots = TimeTableSlot.objects.filter(school=school)
        if academic_year:
            slots = slots.filter(academic_year=academic_year)
        
        conflicts = []
        
        # Check for teacher double-booking
        teacher_schedule = defaultdict(set)
        for slot in slots:
            key = (slot.teacher.id, slot.day, slot.period_number)
            if key in teacher_schedule[slot.teacher.id]:
                conflicts.append({
                    'type': 'teacher_double_booking',
                    'teacher': slot.teacher.name,
                    'day': slot.day,
                    'period': slot.period_number
                })
            else:
                teacher_schedule[slot.teacher.id].add(key)
        
        # Check for class double-booking
        class_schedule = defaultdict(set)
        for slot in slots:
            key = (slot.class_obj.id, slot.day, slot.period_number)
            if key in class_schedule[slot.class_obj.id]:
                conflicts.append({
                    'type': 'class_double_booking',
                    'class': f"{slot.class_obj.class_name}-{slot.class_obj.section}",
                    'day': slot.day,
                    'period': slot.period_number
                })
            else:
                class_schedule[slot.class_obj.id].add(key)
        
        return conflicts


class TeacherWeeklyWorkloadReportView(APIView):
    """API to get weekly workload report per teacher"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        school = request.user.school_profile
        week_str = request.query_params.get('week')  # Format: YYYY-WW
        today = timezone.now().date()
        if week_str:
            try:
                year, week = map(int, week_str.split('-'))
                # Monday of the given week
                start_date = datetime.strptime(f'{year}-W{week}-1', "%Y-W%W-%w").date()
            except Exception:
                return Response({'error': 'Invalid week format. Use YYYY-WW.'}, status=400)
        else:
            # Default: current week (Monday to Sunday)
            start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)

        teachers = Teacher.objects.filter(school=school, is_active=True)
        report = []
        for teacher in teachers:
            slots = TimeTableSlot.objects.filter(
                school=school,
                teacher=teacher,
                is_active=True,
                # Assume timetable slots have a day field (Monday-Friday)
            )
            # Filter slots by week (if TimeTableSlot has a date, otherwise by academic week logic)
            # Here, we assume timetable is for the current academic week, so we just count by day
            day_counts = {day: 0 for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']}
            subject_counts = {}
            total = 0
            for slot in slots:
                day_counts[slot.day] = day_counts.get(slot.day, 0) + 1
                subject_counts[slot.subject.name] = subject_counts.get(slot.subject.name, 0) + 1
                total += 1
            report.append({
                'teacher_id': teacher.id,
                'teacher_name': teacher.name,
                'email': teacher.email,
                'total_periods': total,
                'by_day': day_counts,
                'by_subject': subject_counts,
            })
        return Response({'week_start': start_date, 'week_end': end_date, 'report': report})


class TeacherAbsenceRequestSerializer(serializers.Serializer):
    teacher_id = serializers.IntegerField()
    date = serializers.DateField()
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)

class TeacherAbsenceSubstituteView(APIView):
    """API to mark a teacher absent and auto-substitute their periods"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TeacherAbsenceRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        teacher_id = serializer.validated_data['teacher_id']
        date = serializer.validated_data['date']
        reason = serializer.validated_data.get('reason', '')
        school = request.user.school_profile
        try:
            teacher = Teacher.objects.get(id=teacher_id, school=school)
        except Teacher.DoesNotExist:
            return Response({'error': 'Teacher not found in your school.'}, status=404)
        # Check if already marked absent
        absence, created = TeacherAbsence.objects.get_or_create(
            school=school, teacher=teacher, date=date,
            defaults={'reason': reason}
        )
        if not created:
            return Response({'error': 'Teacher already marked absent for this date.'}, status=400)
        # Find all slots for this teacher on that day
        slots = TimeTableSlot.objects.filter(
            school=school, teacher=teacher, day=date.strftime('%A'), is_active=True
        )
        substitutions = []
        for slot in slots:
            # Find substitute teachers for the subject
            possible_subs = TeacherSubjectAssignment.objects.filter(
                subject=slot.subject, teacher__school=school, teacher__is_active=True
            ).exclude(teacher=teacher)
            # Exclude teachers already booked for that period
            busy_teacher_ids = TimeTableSlot.objects.filter(
                school=school, day=slot.day, period_number=slot.period_number, is_active=True
            ).values_list('teacher_id', flat=True)
            available_subs = [tsa.teacher for tsa in possible_subs if tsa.teacher.id not in busy_teacher_ids]
            # Exclude teachers who have exceeded 25 periods that week
            week_start = date - timedelta(days=date.weekday())
            week_end = week_start + timedelta(days=6)
            def teacher_weekly_count(t):
                return TimeTableSlot.objects.filter(
                    school=school, teacher=t, is_active=True
                ).count()
            available_subs = [t for t in available_subs if teacher_weekly_count(t) < 25]
            if available_subs:
                substitute = available_subs[0]  # Pick the first available
                old_teacher = slot.teacher
                slot.teacher = substitute
                slot.save()
                SubstitutionLog.objects.create(
                    school=school,
                    original_teacher=old_teacher,
                    substitute_teacher=substitute,
                    timetable_slot=slot,
                    date=date,
                    reason=reason
                )
                substitutions.append({
                    'class': f'{slot.class_obj.class_name}-{slot.class_obj.section}',
                    'period': slot.period_number,
                    'subject': slot.subject.name,
                    'old_teacher': old_teacher.name,
                    'substitute_teacher': substitute.name
                })
            else:
                substitutions.append({
                    'class': f'{slot.class_obj.class_name}-{slot.class_obj.section}',
                    'period': slot.period_number,
                    'subject': slot.subject.name,
                    'old_teacher': teacher.name,
                    'substitute_teacher': None,
                    'note': 'No available substitute found.'
                })
        return Response({
            'message': f'Teacher {teacher.name} marked absent for {date}.',
            'substitutions': substitutions
        })


class ClearTimetableView(generics.GenericAPIView):
    """Clear all timetable slots for a school"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Clear all timetable slots"""
        school = request.user.school_profile
        academic_year = request.data.get('academic_year', '')
        
        try:
            with transaction.atomic():
                # Delete all timetable slots for the school
                slots_to_delete = TimeTableSlot.objects.filter(school=school)
                if academic_year:
                    slots_to_delete = slots_to_delete.filter(academic_year=academic_year)
                
                deleted_count = slots_to_delete.count()
                slots_to_delete.delete()
                
                return Response({
                    'message': f'Successfully cleared {deleted_count} timetable slots',
                    'deleted_count': deleted_count,
                    'academic_year': academic_year
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({
                'error': f'Failed to clear timetable: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClassSubjectManagementView(generics.GenericAPIView):
    """Manage subjects for a specific class"""
    permission_classes = [IsAuthenticated]

    def get(self, request, class_id):
        """Get current subjects for a class"""
        try:
            class_obj = Class.objects.get(
                id=class_id, 
                school=request.user.school_profile
            )
            subjects = class_obj.subjects.filter(is_active=True)
            serializer = SubjectListSerializer(subjects, many=True)
            
            return Response({
                'class_id': class_id,
                'class_name': f"{class_obj.class_name}-{class_obj.section}",
                'subjects': serializer.data,
                'available_subjects': SubjectListSerializer(
                    Subject.objects.filter(school=request.user.school_profile, is_active=True),
                    many=True
                ).data
            })
        except Class.DoesNotExist:
            return Response({
                'error': 'Class not found'
            }, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, class_id):
        """Add subjects to a class"""
        try:
            class_obj = Class.objects.get(
                id=class_id, 
                school=request.user.school_profile
            )
            subject_ids = request.data.get('subject_ids', [])
            
            if not subject_ids:
                return Response({
                    'error': 'No subject IDs provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate that all subjects belong to the same school
            subjects = Subject.objects.filter(
                id__in=subject_ids,
                school=request.user.school_profile,
                is_active=True
            )
            
            if len(subjects) != len(subject_ids):
                return Response({
                    'error': 'Some subjects not found or inactive'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Add subjects to class
            class_obj.subjects.add(*subjects)
            
            return Response({
                'message': f'Successfully added {len(subjects)} subjects to {class_obj.class_name}-{class_obj.section}',
                'subjects': SubjectListSerializer(subjects, many=True).data
            }, status=status.HTTP_200_OK)
            
        except Class.DoesNotExist:
            return Response({
                'error': 'Class not found'
            }, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, class_id):
        """Remove subjects from a class"""
        try:
            class_obj = Class.objects.get(
                id=class_id, 
                school=request.user.school_profile
            )
            subject_ids = request.data.get('subject_ids', [])
            
            if not subject_ids:
                return Response({
                    'error': 'No subject IDs provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Remove subjects from class
            subjects = Subject.objects.filter(id__in=subject_ids)
            class_obj.subjects.remove(*subjects)
            
            return Response({
                'message': f'Successfully removed {len(subjects)} subjects from {class_obj.class_name}-{class_obj.section}',
                'removed_subjects': SubjectListSerializer(subjects, many=True).data
            }, status=status.HTTP_200_OK)
            
        except Class.DoesNotExist:
            return Response({
                'error': 'Class not found'
            }, status=status.HTTP_404_NOT_FOUND)


class TeacherWorkloadAnalysisView(generics.GenericAPIView):
    """Analyze teacher workload and suggest optimal distribution"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get teacher workload analysis"""
        school = request.user.school_profile
        teachers = Teacher.objects.filter(school=school, is_active=True)
        
        analysis = []
        total_periods = 0
        
        for teacher in teachers:
            # Get current workload
            current_slots = TimeTableSlot.objects.filter(
                school=school,
                teacher=teacher
            ).count()
            
            # Get teacher's subject assignments
            assignments = TeacherSubjectAssignment.objects.filter(
                teacher=teacher,
                subject__school=school
            ).select_related('subject')
            
            subjects_taught = [ass.subject.name for ass in assignments]
            max_periods = sum(ass.max_periods_per_week for ass in assignments)
            
            analysis.append({
                'teacher_id': teacher.id,
                'teacher_name': teacher.name,
                'subjects': subjects_taught,
                'current_periods': current_slots,
                'max_periods': max_periods,
                'utilization_percentage': round((current_slots / max_periods * 100) if max_periods > 0 else 0, 2),
                'workload_status': 'Under-utilized' if current_slots < max_periods * 0.8 else 'Optimal' if current_slots <= max_periods else 'Over-utilized'
            })
            
            total_periods += current_slots
        
        # Calculate averages
        if analysis:
            avg_periods = total_periods / len(analysis)
            for item in analysis:
                item['deviation_from_avg'] = round(item['current_periods'] - avg_periods, 2)
        
        return Response({
            'analysis': analysis,
            'summary': {
                'total_teachers': len(analysis),
                'total_periods': total_periods,
                'average_periods': round(avg_periods, 2) if analysis else 0,
                'under_utilized': len([a for a in analysis if a['workload_status'] == 'Under-utilized']),
                'optimal': len([a for a in analysis if a['workload_status'] == 'Optimal']),
                'over_utilized': len([a for a in analysis if a['workload_status'] == 'Over-utilized'])
            }
        })


class SchoolPeriodTimingView(generics.GenericAPIView):
    """Manage school period timing and break periods configuration"""
    permission_classes = [IsAuthenticated]
    serializer_class = SchoolProfileSerializer

    def get(self, request):
        """Get current period timing configuration"""
        try:
            school = request.user.school_profile
            serializer = self.get_serializer(school)
            
            # Add calculated period timing information
            data = serializer.data
            data['period_timing_info'] = {
                'break_periods_info': school.get_break_periods_info(),
                'sample_period_times': {}
            }
            
            # Add sample period times for first few periods
            for period in range(1, min(8, school.total_periods_per_day + 1)):
                start_time, end_time = school.get_period_times(period)
                data['period_timing_info']['sample_period_times'][f'period_{period}'] = {
                    'start_time': start_time,
                    'end_time': end_time
                }
            
            return Response({
                'message': 'Period timing configuration retrieved successfully',
                'data': data
            })
        except SchoolProfile.DoesNotExist:
            return Response({
                'error': 'School profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Failed to retrieve period timing: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        """Update period timing configuration"""
        try:
            school = request.user.school_profile
            serializer = self.get_serializer(school, data=request.data, partial=True)
            
            if serializer.is_valid():
                # Validate break periods configuration
                break_periods = request.data.get('break_periods', [])
                if break_periods:
                    # Validate break period structure
                    for bp in break_periods:
                        if not all(key in bp for key in ['period', 'duration', 'name']):
                            return Response({
                                'error': 'Break periods must include period, duration, and name'
                            }, status=status.HTTP_400_BAD_REQUEST)
                        
                        if bp['period'] < 1 or bp['period'] > school.total_periods_per_day:
                            return Response({
                                'error': f"Break period {bp['period']} must be between 1 and {school.total_periods_per_day}"
                            }, status=status.HTTP_400_BAD_REQUEST)
                        
                        if bp['duration'] < 5 or bp['duration'] > 60:
                            return Response({
                                'error': f"Break duration must be between 5 and 60 minutes"
                            }, status=status.HTTP_400_BAD_REQUEST)
                
                school = serializer.save()
                return Response({
                    'message': 'Period timing configuration updated successfully',
                    'data': self.get_serializer(school).data
                })
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except SchoolProfile.DoesNotExist:
            return Response({
                'error': 'School profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Failed to update period timing: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
