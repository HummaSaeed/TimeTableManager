# Timetable Management System - Development Setup Guide

## 🛠️ **Prerequisites**

### **Required Software**
- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **Virtual Environment** - Python's built-in `venv`
- **Code Editor** - VS Code, PyCharm, or any preferred editor

### **System Requirements**
- **Operating System:** Windows, macOS, or Linux
- **Memory:** 4GB RAM minimum, 8GB recommended
- **Storage:** 2GB free space
- **Network:** Internet connection for package installation

## 🚀 **Installation Steps**

### **1. Clone the Repository**

```bash
git clone <repository-url>
cd TimeTableManager
```

### **2. Create Virtual Environment**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### **3. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **4. Environment Configuration**

Create a `.env` file in the project root:

```bash
# Django Settings
DEBUG=True
SECRET_KEY=your-development-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Email Settings (for development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=1025

# Static Files
STATIC_ROOT=staticfiles
MEDIA_ROOT=media

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### **5. Database Setup**

```bash
# Create database migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### **6. Static Files Setup**

```bash
# Create static files directory
mkdir static_files

# Collect static files
python manage.py collectstatic --noinput
```

### **7. Run Development Server**

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## 📁 **Project Structure**

```
TimeTableManager/
├── core/                    # Django project settings
│   ├── __init__.py
│   ├── settings.py         # Main settings file
│   ├── urls.py            # Main URL configuration
│   ├── asgi.py            # ASGI configuration
│   └── wsgi.py            # WSGI configuration
├── timetable/              # Main application
│   ├── __init__.py
│   ├── models.py          # Database models
│   ├── views.py           # API views
│   ├── serializers.py     # DRF serializers
│   ├── urls.py           # App URL configuration
│   ├── admin.py          # Django admin configuration
│   └── management/       # Custom management commands
│       └── commands/
│           ├── generate_timetable.py
│           └── fix_school_profiles.py
├── staticfiles/           # Collected static files
├── media/                 # User uploaded files
├── static_files/          # Custom static files
├── requirements.txt       # Python dependencies
├── manage.py             # Django management script
└── db.sqlite3           # SQLite database (development)
```

## 🔧 **Development Configuration**

### **Settings Configuration**

The main settings file is located at `core/settings.py`. Key development settings:

```python
# Development settings
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database (SQLite for development)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static_files')
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### **Environment Variables**

For production-like development, use environment variables:

```bash
# .env file
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

## 🗄️ **Database Management**

### **Migrations**

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Reset migrations (if needed)
python manage.py migrate timetable zero
python manage.py makemigrations
python manage.py migrate
```

### **Database Operations**

```bash
# Create superuser
python manage.py createsuperuser

# Shell access
python manage.py shell

# Database backup
python manage.py dumpdata > backup.json

# Database restore
python manage.py loaddata backup.json
```

## 🧪 **Testing**

### **Running Tests**

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test timetable

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### **Test Structure**

```
timetable/
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_serializers.py
│   └── test_commands.py
```

## 🔍 **Debugging**

### **Django Debug Toolbar**

Add to `requirements.txt`:
```
django-debug-toolbar
```

Configure in `settings.py`:
```python
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

### **Logging Configuration**

```python
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
        'level': 'INFO',
    },
}
```

## 📦 **Package Management**

### **Adding New Dependencies**

```bash
# Install new package
pip install package-name

# Update requirements.txt
pip freeze > requirements.txt

# Install from requirements
pip install -r requirements.txt
```

### **Development Dependencies**

```bash
# Install development packages
pip install django-debug-toolbar
pip install coverage
pip install black
pip install flake8
```

## 🚀 **Development Workflow**

### **1. Feature Development**

```bash
# Create new branch
git checkout -b feature/new-feature

# Make changes
# Test changes
python manage.py test

# Commit changes
git add .
git commit -m "Add new feature"

# Push changes
git push origin feature/new-feature
```

### **2. Code Quality**

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking (if using mypy)
mypy .
```

### **3. Database Changes**

```bash
# Make model changes
# Edit models.py

# Create migration
python manage.py makemigrations

# Review migration
python manage.py sqlmigrate timetable 0001

# Apply migration
python manage.py migrate

# Test changes
python manage.py test
```

## 🔧 **Custom Management Commands**

### **Available Commands**

```bash
# Generate timetable
python manage.py generate_timetable --school-id 1 --academic-year "2024-2025"

# Fix school profiles
python manage.py fix_school_profiles

# Create custom command
python manage.py startapp myapp
```

### **Creating New Commands**

1. Create command file in `timetable/management/commands/`
2. Inherit from `BaseCommand`
3. Implement `handle()` method

Example:
```python
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Description of command'

    def add_arguments(self, parser):
        parser.add_argument('--option', type=str)

    def handle(self, *args, **options):
        # Command logic here
        pass
```

## 🌐 **API Development**

### **API Documentation**

- **Swagger UI:** `http://127.0.0.1:8000/swagger/`
- **ReDoc:** `http://127.0.0.1:8000/redoc/`

### **Testing API Endpoints**

```bash
# Using curl
curl -X GET http://127.0.0.1:8000/api/teachers/ \
  -H "Authorization: Bearer <token>"

# Using httpie
http GET http://127.0.0.1:8000/api/teachers/ \
  Authorization:"Bearer <token>"
```

## 🔒 **Security Considerations**

### **Development Security**

```python
# settings.py
DEBUG = True  # Only in development
SECRET_KEY = 'development-key'  # Use environment variable in production

# CORS settings for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

### **Environment Variables**

```bash
# .env file
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

## 📊 **Performance Monitoring**

### **Development Tools**

```bash
# Install performance tools
pip install django-extensions
pip install django-silk

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ...
    'django_extensions',
    'silk',
]
```

### **Profiling**

```python
# In views.py
from silk.profiling.profiler import silk_profile

@silk_profile(name='View Profile')
def my_view(request):
    # View logic
    pass
```

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Import Errors**
   ```bash
   # Check Python path
   python -c "import sys; print(sys.path)"
   
   # Reinstall packages
   pip install -r requirements.txt
   ```

2. **Database Issues**
   ```bash
   # Reset database
   rm db.sqlite3
   python manage.py migrate
   ```

3. **Static Files Issues**
   ```bash
   # Recollect static files
   python manage.py collectstatic --clear --noinput
   ```

4. **Migration Issues**
   ```bash
   # Reset migrations
   python manage.py migrate timetable zero
   python manage.py makemigrations
   python manage.py migrate
   ```

### **Debug Commands**

```bash
# Check Django version
python -c "import django; print(django.get_version())"

# Check installed packages
pip list

# Check database
python manage.py dbshell

# Check settings
python manage.py check
```

## 📚 **Additional Resources**

### **Documentation**
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Project API Documentation](./API_DOCUMENTATION.md)

### **Development Tools**
- **VS Code Extensions:** Python, Django, REST Client
- **PyCharm:** Django support built-in
- **Postman:** API testing
- **Insomnia:** API development

### **Useful Commands**

```bash
# Development server
python manage.py runserver

# Shell
python manage.py shell

# Admin interface
# Visit http://127.0.0.1:8000/admin/

# API documentation
# Visit http://127.0.0.1:8000/swagger/
```

---

*Last updated: August 8, 2025*
*Version: 1.0.0* 