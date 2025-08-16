# Timetable Management System - Troubleshooting Guide

## 🚨 **Common Issues and Solutions**

This guide provides solutions to the most common issues encountered while using the Timetable Management System.

## 🔐 **Authentication Issues**

### **1. "User has no school_profile" Error**

**Problem:** Users trying to access API endpoints get this error.

**Solution:**
```bash
# Run the fix command
python manage.py fix_school_profiles

# Or manually create school profile
python manage.py shell
```
```python
from django.contrib.auth.models import User
from timetable.models import SchoolProfile
from datetime import time

user = User.objects.get(username='your_username')
SchoolProfile.objects.create(
    user=user,
    school_name="Your School Name",
    school_code="SCH001",
    school_start_time=time(8, 0),
    school_end_time=time(15, 0),
    # ... other required fields
)
```

### **2. JWT Token Expired**

**Problem:** "Token has expired" error.

**Solution:**
```bash
# Refresh token using refresh endpoint
curl -X POST http://127.0.0.1:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "your_refresh_token"}'
```

### **3. Invalid Credentials**

**Problem:** Login fails with "Invalid credentials".

**Solutions:**
1. **Check email format:** Ensure email is correct
2. **Reset password:** Use password reset endpoint
3. **Check user status:** Ensure user account is active

```bash
# Password reset
curl -X POST http://127.0.0.1:8000/api/teacher/password-reset/ \
  -H "Content-Type: application/json" \
  -d '{"email": "teacher@school.com"}'
```

## 🗄️ **Database Issues**

### **1. Migration Errors**

**Problem:** "No migrations to apply" or migration conflicts.

**Solution:**
```bash
# Check migration status
python manage.py showmigrations

# Reset migrations (if needed)
python manage.py migrate timetable zero
python manage.py makemigrations
python manage.py migrate

# Or apply specific migration
python manage.py migrate timetable 0007
```

### **2. Database Connection Issues**

**Problem:** "Database is locked" or connection errors.

**Solutions:**
```bash
# Restart development server
python manage.py runserver

# Check database file permissions
ls -la db.sqlite3

# Recreate database (WARNING: Data loss)
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### **3. NOT NULL Constraint Errors**

**Problem:** "NOT NULL constraint failed" errors.

**Solution:**
```bash
# Run the fix command
python manage.py fix_school_profiles

# Check model defaults
python manage.py shell
```
```python
from timetable.models import SchoolProfile
# Check if all required fields have defaults
```

## 📁 **Static Files Issues**

### **1. "Missing staticfiles manifest entry" Error**

**Problem:** Static files not found in production.

**Solutions:**
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check static files directory
ls -la staticfiles/

# Clear and recollect
python manage.py collectstatic --clear --noinput
```

### **2. Static Files Not Loading**

**Problem:** CSS/JS files not loading in development.

**Solutions:**
```bash
# Check DEBUG setting
# Ensure DEBUG = True in development

# Check static files configuration
python manage.py check

# Create static_files directory
mkdir static_files
```

## 🔧 **API Issues**

### **1. 400 Bad Request Errors**

**Problem:** API requests returning 400 errors.

**Solutions:**
1. **Check request format:**
```json
{
    "email": "user@example.com",
    "password": "password123"
}
```

2. **Check required fields:**
```python
# Check serializer requirements
from timetable.serializers import UserRegistrationSerializer
serializer = UserRegistrationSerializer(data=request.data)
print(serializer.errors)
```

3. **Validate data types:**
```python
# Ensure proper data types
# Email should be valid email format
# Passwords should meet requirements
```

### **2. 401 Unauthorized Errors**

**Problem:** API requests returning 401 errors.

**Solutions:**
1. **Check Authorization header:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://127.0.0.1:8000/api/teachers/
```

2. **Verify token validity:**
```python
# Check token in Django shell
from rest_framework_simplejwt.tokens import AccessToken
token = AccessToken('your_token_here')
print(token.payload)
```

### **3. 500 Internal Server Error**

**Problem:** Server errors in API responses.

**Solutions:**
1. **Check error logs:**
```bash
# Check Django error log
tail -f error.log

# Check server logs
python manage.py runserver --verbosity=2
```

2. **Enable DEBUG mode:**
```python
# In settings.py
DEBUG = True
```

## 📅 **Timetable Generation Issues**

### **1. "No active classes found" Error**

**Problem:** Timetable generation fails due to missing data.

**Solutions:**
```bash
# Check if classes exist
python manage.py shell
```
```python
from timetable.models import Class, SchoolProfile
school = SchoolProfile.objects.first()
classes = Class.objects.filter(school=school, is_active=True)
print(f"Active classes: {classes.count()}")
```

### **2. "No teacher-subject assignments found" Error**

**Problem:** No teachers assigned to subjects.

**Solutions:**
```python
# Check teacher assignments
from timetable.models import TeacherSubjectAssignment
assignments = TeacherSubjectAssignment.objects.all()
print(f"Teacher assignments: {assignments.count()}")

# Create assignments if needed
from timetable.models import Teacher, Subject
teacher = Teacher.objects.first()
subject = Subject.objects.first()
TeacherSubjectAssignment.objects.create(
    teacher=teacher,
    subject=subject,
    is_primary=True,
    max_periods_per_week=20
)
```

### **3. Timetable Generation Fails**

**Problem:** Generation process fails after multiple attempts.

**Solutions:**
1. **Check data completeness:**
```python
# Verify all required data exists
from timetable.models import *
school = SchoolProfile.objects.first()
teachers = Teacher.objects.filter(school=school, is_active=True)
subjects = Subject.objects.filter(school=school, is_active=True)
classes = Class.objects.filter(school=school, is_active=True)

print(f"Teachers: {teachers.count()}")
print(f"Subjects: {subjects.count()}")
print(f"Classes: {classes.count()}")
```

2. **Increase max attempts:**
```bash
python manage.py generate_timetable --max-attempts 500
```

## 📧 **Email Issues**

### **1. Email Not Sending**

**Problem:** Welcome emails or password reset emails not sent.

**Solutions:**
1. **Check email configuration:**
```python
# In settings.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # For development
EMAIL_HOST = 'smtp.gmail.com'  # For production
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

2. **Test email functionality:**
```python
from django.core.mail import send_mail
send_mail(
    'Test Subject',
    'Test message',
    'from@example.com',
    ['to@example.com'],
    fail_silently=False,
)
```

## 🔍 **Debugging Techniques**

### **1. Django Debug Toolbar**

**Installation:**
```bash
pip install django-debug-toolbar
```

**Configuration:**
```python
# In settings.py
INSTALLED_APPS = [
    # ...
    'debug_toolbar',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # ... other middleware
]

INTERNAL_IPS = [
    '127.0.0.1',
]
```

### **2. Logging Configuration**

**Enhanced logging:**
```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
    },
}
```

### **3. Database Queries Debugging**

**Enable query logging:**
```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 🛠️ **System Maintenance**

### **1. Database Backup**

**Create backup:**
```bash
python manage.py dumpdata > backup.json
```

**Restore backup:**
```bash
python manage.py loaddata backup.json
```

### **2. Clear Cache**

**Clear static files cache:**
```bash
python manage.py collectstatic --clear --noinput
```

### **3. Reset Development Environment**

**Complete reset:**
```bash
# Remove database
rm db.sqlite3

# Remove migrations
rm -rf timetable/migrations/0*.py

# Recreate migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

## 📞 **Getting Help**

### **1. Check Error Logs**

**Location:** `error.log` in project root

**View logs:**
```bash
tail -f error.log
```

### **2. Enable Verbose Output**

**Django commands:**
```bash
python manage.py runserver --verbosity=2
python manage.py migrate --verbosity=2
```

### **3. Common Debug Commands**

```bash
# Check Django version
python -c "import django; print(django.get_version())"

# Check installed packages
pip list

# Check database
python manage.py dbshell

# Check settings
python manage.py check

# Show URLs
python manage.py show_urls
```

### **4. Useful API Endpoints**

- **Health Check:** `GET /api/health/`
- **API Documentation:** `GET /swagger/`
- **Admin Interface:** `GET /admin/`

## 🔧 **Performance Issues**

### **1. Slow API Responses**

**Solutions:**
1. **Add database indexes:**
```python
# In models.py
class Meta:
    indexes = [
        models.Index(fields=['school', 'is_active']),
    ]
```

2. **Optimize queries:**
```python
# Use select_related for foreign keys
Teacher.objects.select_related('school').filter(is_active=True)

# Use prefetch_related for many-to-many
Class.objects.prefetch_related('subjects').all()
```

### **2. Memory Issues**

**Solutions:**
1. **Limit query results:**
```python
# Use pagination
from rest_framework.pagination import PageNumberPagination
```

2. **Optimize serializers:**
```python
# Use read-only fields where possible
class TeacherListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['id', 'name', 'email']  # Only needed fields
```

## 🚀 **Production Issues**

### **1. Static Files Not Serving**

**Solutions:**
1. **Configure web server (nginx):**
```nginx
location /static/ {
    alias /path/to/your/staticfiles/;
}
```

2. **Use CDN for static files**

### **2. Database Connection Issues**

**Solutions:**
1. **Use PostgreSQL in production**
2. **Configure connection pooling**
3. **Set proper database timeouts**

### **3. Security Issues**

**Solutions:**
1. **Set DEBUG = False**
2. **Use environment variables for secrets**
3. **Configure HTTPS**
4. **Set up proper CORS settings**

---

## 📚 **Additional Resources**

- **Django Documentation:** https://docs.djangoproject.com/
- **Django REST Framework:** https://www.django-rest-framework.org/
- **Project API Documentation:** `/swagger/` or `/redoc/`

---

*Last updated: August 8, 2025*
*Version: 1.0.0* 