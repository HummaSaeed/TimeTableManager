# Timetable Management System - System Architecture

## 🏗️ **System Overview**

The Timetable Management System is a Django-based web application designed for school administrators to manage teachers, classes, subjects, and generate automated timetables. The system follows a RESTful API architecture with JWT authentication.

## 📊 **Architecture Diagram**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Layer     │    │   Database      │
│   (React/Vue)   │◄──►│   (Django DRF)  │◄──►│   (SQLite/      │
│                 │    │                 │    │    PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Authentication│
                       │   (JWT)         │
                       └─────────────────┘
```

## 🧩 **Core Components**

### **1. Django Framework**
- **Version:** Django 5.2.3
- **Purpose:** Web framework providing ORM, admin interface, and URL routing
- **Key Features:**
  - Model-View-Template (MVT) architecture
  - Built-in admin interface
  - Database migrations
  - Security features

### **2. Django REST Framework (DRF)**
- **Version:** 3.16.0
- **Purpose:** API framework for building RESTful APIs
- **Key Features:**
  - Serializers for data transformation
  - ViewSets for CRUD operations
  - Authentication and permissions
  - API documentation (Swagger/ReDoc)

### **3. Authentication System**
- **Framework:** JWT (JSON Web Tokens)
- **Library:** `djangorestframework-simplejwt`
- **Features:**
  - Access and refresh tokens
  - Token expiration
  - Secure authentication

### **4. Database Layer**
- **Development:** SQLite3
- **Production:** PostgreSQL (recommended)
- **ORM:** Django ORM
- **Migrations:** Automatic schema management

## 🗄️ **Database Schema**

### **Core Models**

#### **SchoolProfile**
```python
class SchoolProfile(models.Model):
    user = models.OneToOneField(User)
    school_name = models.CharField(max_length=255)
    school_code = models.CharField(max_length=50, unique=True)
    school_start_time = models.TimeField()
    school_end_time = models.TimeField()
    # ... other fields
```

#### **Teacher**
```python
class Teacher(models.Model):
    school = models.ForeignKey(SchoolProfile)
    user = models.OneToOneField(User)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    subject_specialist = models.CharField(max_length=255)
    # ... other fields
```

#### **Subject**
```python
class Subject(models.Model):
    school = models.ForeignKey(SchoolProfile)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    # ... other fields
```

#### **Class**
```python
class Class(models.Model):
    school = models.ForeignKey(SchoolProfile)
    class_name = models.CharField(max_length=50)
    section = models.CharField(max_length=10)
    subjects = models.ManyToManyField(Subject)
    # ... other fields
```

#### **TimeTableSlot**
```python
class TimeTableSlot(models.Model):
    school = models.ForeignKey(SchoolProfile)
    class_obj = models.ForeignKey(Class)
    subject = models.ForeignKey(Subject)
    teacher = models.ForeignKey(Teacher)
    day = models.CharField(max_length=10)
    period_number = models.IntegerField()
    # ... other fields
```

### **Relationships**

```
User (1) ─── (1) SchoolProfile (1) ─── (N) Teacher
                                    └── (N) Subject
                                    └── (N) Class
                                    └── (N) TimeTableSlot

Teacher (N) ─── (N) Subject (through TeacherSubjectAssignment)
Class (N) ─── (N) Subject (through ManyToManyField)
```

## 🔐 **Security Architecture**

### **Authentication Flow**

1. **Registration:**
   ```
   User Registration → Create User → Create SchoolProfile → Return JWT Tokens
   ```

2. **Login:**
   ```
   User Login → Validate Credentials → Return JWT Tokens
   ```

3. **API Access:**
   ```
   API Request → Validate JWT Token → Check Permissions → Return Response
   ```

### **Security Features**

- **JWT Authentication:** Stateless authentication
- **CORS Protection:** Cross-origin resource sharing
- **CSRF Protection:** Cross-site request forgery protection
- **Input Validation:** Serializer-based validation
- **SQL Injection Protection:** Django ORM protection

## 🌐 **API Architecture**

### **RESTful Design**

The API follows REST principles:

- **GET:** Retrieve resources
- **POST:** Create resources
- **PUT:** Update resources (full update)
- **PATCH:** Update resources (partial update)
- **DELETE:** Delete resources

### **API Endpoints Structure**

```
/api/
├── register/                    # School registration
├── login/                      # School login
├── school-profile/             # School profile management
├── teachers/                   # Teacher management
├── subjects/                   # Subject management
├── classes/                    # Class management
├── teacher-assignments/        # Teacher-subject assignments
├── timetable/
│   ├── slots/                 # Timetable slots
│   ├── generate/              # Generate timetable
│   └── stats/                 # Timetable statistics
└── swagger/                   # API documentation
```

### **Response Format**

```json
{
    "message": "Success message",
    "data": {
        // Resource data
    },
    "count": 10,
    "next": "next_page_url",
    "previous": "previous_page_url"
}
```

## 🔄 **Data Flow**

### **1. User Registration Flow**

```
1. User submits registration data
2. Validate input data
3. Create User object
4. Create SchoolProfile object
5. Generate JWT tokens
6. Return success response with tokens
```

### **2. Timetable Generation Flow**

```
1. Validate school data
2. Check teacher-subject assignments
3. Check class-subject assignments
4. Generate timetable slots
5. Resolve conflicts
6. Save timetable to database
7. Return generation results
```

### **3. Teacher Management Flow**

```
1. Create teacher account
2. Generate secure password
3. Send welcome email
4. Create teacher profile
5. Return teacher data with credentials
```

## 🚀 **Performance Architecture**

### **Database Optimization**

- **Indexes:** Strategic database indexes
- **Query Optimization:** Select_related and prefetch_related
- **Caching:** Django caching framework
- **Pagination:** API response pagination

### **API Performance**

- **Serialization:** Efficient data serialization
- **Filtering:** Database-level filtering
- **Search:** Full-text search capabilities
- **Rate Limiting:** API rate limiting

## 🔧 **Configuration Management**

### **Environment Variables**

```bash
# Django Settings
DEBUG=True/False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True

# Static Files
STATIC_ROOT=staticfiles
MEDIA_ROOT=media
```

### **Settings Structure**

```python
# core/settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'rest_framework',
    'corsheaders',
    'timetable',
    'drf_yasg',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # ... other middleware
]
```

## 🛠️ **Development Architecture**

### **Project Structure**

```
TimeTableManager/
├── core/                    # Django project settings
│   ├── settings.py         # Main settings
│   ├── urls.py            # Main URL configuration
│   └── wsgi.py            # WSGI configuration
├── timetable/              # Main application
│   ├── models.py          # Database models
│   ├── views.py           # API views
│   ├── serializers.py     # DRF serializers
│   ├── urls.py           # App URL configuration
│   └── management/       # Custom commands
├── staticfiles/           # Collected static files
├── media/                 # User uploaded files
└── requirements.txt       # Python dependencies
```

### **Code Organization**

- **Models:** Database schema and business logic
- **Views:** API endpoints and request handling
- **Serializers:** Data transformation and validation
- **URLs:** API routing and endpoint mapping
- **Admin:** Django admin interface configuration

## 🔄 **Deployment Architecture**

### **Development Environment**

- **Server:** Django development server
- **Database:** SQLite3
- **Static Files:** Django static files serving
- **Email:** Console backend

### **Production Environment**

- **Web Server:** Nginx/Gunicorn
- **Database:** PostgreSQL
- **Static Files:** CDN or web server
- **Email:** SMTP server
- **SSL:** HTTPS encryption

## 📊 **Monitoring and Logging**

### **Logging Configuration**

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'error.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
```

### **Error Handling**

- **API Errors:** Standardized error responses
- **Validation Errors:** Detailed field-level errors
- **Database Errors:** Graceful error handling
- **Authentication Errors:** Clear authentication messages

## 🔒 **Security Architecture**

### **Authentication Security**

- **JWT Tokens:** Secure token-based authentication
- **Token Expiration:** Automatic token expiration
- **Refresh Tokens:** Secure token refresh mechanism
- **Password Security:** Strong password requirements

### **Data Security**

- **Input Validation:** Comprehensive input validation
- **SQL Injection Protection:** ORM-based protection
- **XSS Protection:** Template-based protection
- **CSRF Protection:** Built-in CSRF protection

## 🚀 **Scalability Considerations**

### **Horizontal Scaling**

- **Load Balancing:** Multiple application servers
- **Database Scaling:** Read replicas and sharding
- **Caching:** Redis/Memcached for caching
- **CDN:** Content delivery network for static files

### **Vertical Scaling**

- **Database Optimization:** Query optimization and indexing
- **Application Optimization:** Code optimization and profiling
- **Resource Management:** Memory and CPU optimization

## 📈 **Future Architecture Enhancements**

### **Planned Improvements**

1. **Microservices Architecture:** Split into smaller services
2. **Event-Driven Architecture:** Asynchronous processing
3. **Real-time Features:** WebSocket integration
4. **Mobile API:** Dedicated mobile API endpoints
5. **Analytics Integration:** Advanced reporting and analytics

### **Technology Stack Evolution**

- **Database:** PostgreSQL with advanced features
- **Caching:** Redis for session and data caching
- **Message Queue:** Celery for background tasks
- **Monitoring:** Prometheus and Grafana
- **Containerization:** Docker and Kubernetes

---

## 📚 **Additional Resources**

- **Django Documentation:** https://docs.djangoproject.com/
- **DRF Documentation:** https://www.django-rest-framework.org/
- **JWT Documentation:** https://django-rest-framework-simplejwt.readthedocs.io/

---

*Last updated: August 8, 2025*
*Version: 1.0.0* 