from django.urls import path
from . import views



urlpatterns = [
    # Authentication endpoints
    path('api/register/', views.register_school, name='register_school'),
    path('api/login/', views.login_school, name='login_school'),
     
    # Teacher authentication endpoints
    path('api/teacher/login/', views.teacher_login, name='teacher_login'),
    path('api/teacher/password-reset/', views.teacher_password_reset, name='teacher_password_reset'),
    
    # School profile endpoints
    path('api/school-profile/', views.SchoolProfileView.as_view(), name='school_profile'),
    
    # Teacher endpoints
    path('api/teachers/', views.TeacherListView.as_view(), name='teacher_list'),
    path('api/teachers/<int:pk>/', views.TeacherDetailView.as_view(), name='teacher_detail'),
    path('api/teachers/<int:pk>/activate/', views.TeacherActivateView.as_view(), name='teacher_activate'),
    path('api/teachers/stats/', views.TeacherStatsView.as_view(), name='teacher_stats'),
    path('api/teachers/workload/', views.TeacherWeeklyWorkloadReportView.as_view(), name='teacher_weekly_workload'),
    path('api/teachers/absent/', views.TeacherAbsenceSubstituteView.as_view(), name='teacher_absence_substitute'),
    
    # Subject endpoints
    path('api/subjects/', views.SubjectListView.as_view(), name='subject_list'),
    path('api/subjects/<int:pk>/', views.SubjectDetailView.as_view(), name='subject_detail'),
    path('api/subjects/<int:pk>/activate/', views.SubjectActivateView.as_view(), name='subject_activate'),
    
    # Class endpoints
    path('api/classes/', views.ClassListView.as_view(), name='class_list'),
    path('api/classes/<int:pk>/', views.ClassDetailView.as_view(), name='class_detail'),
    path('api/classes/<int:pk>/activate/', views.ClassActivateView.as_view(), name='class_activate'),
    path('api/classes/stats/', views.ClassStatsView.as_view(), name='class_stats'),
    
    # Teacher Subject Assignment management
    path('api/teacher-assignments/', views.TeacherSubjectAssignmentListView.as_view(), name='teacher_assignment_list'),
    path('api/teacher-assignments/<int:pk>/', views.TeacherSubjectAssignmentDetailView.as_view(), name='teacher_assignment_detail'),
    
    # Timetable management
    path('api/timetable/slots/', views.TimeTableSlotListView.as_view(), name='timetable_slot_list'),
    path('api/timetable/slots/<int:pk>/', views.TimeTableSlotDetailView.as_view(), name='timetable_slot_detail'),
    path('api/timetable/generate/', views.GenerateTimetableView.as_view(), name='generate_timetable'),
    path('api/timetable/stats/', views.TimetableStatsView.as_view(), name='timetable_stats'),
] 