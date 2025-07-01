# Timetable Management API Documentation

## Base URL
```
http://localhost:8000/
```

## Authentication
All API endpoints (except registration and login) require JWT authentication. Include the access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## 1. Authentication Endpoints

### 1.1 Register School
**POST** `/api/register/`

Register a new school with email and password.

**Request Body:**
```json
{
    "email": "school@example.com",
    "password": "securepassword123",
    "password_confirm": "securepassword123"
}
```

**Response (201 Created):**
```json
{
    "message": "School registered successfully",
    "user_id": 1,
    "email": "school@example.com",
    "tokens": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

### 1.2 Login School
**POST** `/api/login/`

Login with email and password to get access token.

**Request Body:**
```json
{
    "email": "school@example.com",
    "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
    "message": "Login successful",
    "user_id": 1,
    "email": "school@example.com",
    "tokens": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

---

## 2. School Profile Endpoints

### 2.1 Get School Profile
**GET** `/api/school-profile/`

Get the authenticated school's profile.

**Response (200 OK):**
```json
{
    "id": 1,
    "user_email": "school@example.com",
    "school_name": "Example School",
    "school_code": "EX001",
    "school_start_time": "08:00:00",
    "school_end_time": "15:00:00",
    "number_of_classes": 12,
    "sections_per_class": {
        "1": ["A", "B", "C"],
        "2": ["A", "B"],
        "3": ["A", "B", "C", "D"]
    },
    "period_duration_minutes": 45,
    "total_periods_per_day": 8,
    "break_time": "12:00:00",
    "friday_closing_time": "13:00:00",
    "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "academic_year": "2024-25",
    "timezone": "UTC",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

### 2.2 Update School Profile
**PUT** `/api/school-profile/`

Update the complete school profile.

**Request Body:**
```json
{
    "school_name": "Updated School Name",
    "school_code": "US001",
    "school_start_time": "08:30:00",
    "school_end_time": "15:30:00",
    "number_of_classes": 15,
    "sections_per_class": {
        "1": ["A", "B"],
        "2": ["A", "B", "C"]
    },
    "period_duration_minutes": 50,
    "total_periods_per_day": 7,
    "break_time": "12:30:00",
    "friday_closing_time": "13:30:00",
    "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "academic_year": "2024-25",
    "timezone": "Asia/Kolkata"
}
```

### 2.3 Partial Update School Profile
**PATCH** `/api/school-profile/`

Partially update the school profile.

**Request Body:**
```json
{
    "school_name": "New School Name",
    "period_duration_minutes": 40
}
```

---

## 3. Teacher Management Endpoints

### 3.1 List Teachers
**GET** `/api/teachers/`

Get all teachers for the authenticated school with filtering, searching, and pagination.

**Query Parameters:**
- `is_active` (boolean): Filter by active status
- `is_class_teacher` (boolean): Filter by class teacher status
- `designation` (string): Filter by designation
- `gender` (string): Filter by gender (M/F/O)
- `search` (string): Search in name, subject_specialist, email
- `ordering` (string): Order by name, created_at, experience_years
- `page` (integer): Page number for pagination

**Example Request:**
```
GET /api/teachers/?is_active=true&search=math&ordering=name
```

**Response (200 OK):**
```json
{
    "count": 2,
    "results": [
        {
            "id": 1,
            "name": "John Doe",
            "subject_specialist": "Mathematics",
            "designation": "Senior Teacher",
            "is_class_teacher": true,
            "class_teacher_class": 10,
            "class_teacher_section": "A",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "subject_specialist": "Physics",
            "designation": "Teacher",
            "is_class_teacher": false,
            "class_teacher_class": null,
            "class_teacher_section": null,
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

### 3.2 Create Teacher
**POST** `/api/teachers/`

Create a new teacher for the authenticated school.

**Request Body:**
```json
{
    "name": "John Doe",
    "subject_specialist": "Mathematics",
    "previous_subjects": ["Physics", "Chemistry"],
    "designation": "Senior Teacher",
    "qualification": "M.Sc. Mathematics",
    "is_class_teacher": true,
    "class_teacher_class": 10,
    "class_teacher_section": "A",
    "phone_number": "+1234567890",
    "email": "john.doe@school.com",
    "gender": "M",
    "date_joined": "2020-06-01",
    "experience_years": 5
}
```

**Response (201 Created):**
```json
{
    "message": "Teacher created successfully",
    "data": {
        "id": 1,
        "school": 1,
        "school_name": "Example School",
        "name": "John Doe",
        "subject_specialist": "Mathematics",
        "previous_subjects": ["Physics", "Chemistry"],
        "designation": "Senior Teacher",
        "qualification": "M.Sc. Mathematics",
        "is_class_teacher": true,
        "class_teacher_class": 10,
        "class_teacher_section": "A",
        "phone_number": "+1234567890",
        "email": "john.doe@school.com",
        "gender": "M",
        "gender_display": "Male",
        "date_joined": "2020-06-01",
        "experience_years": 5,
        "is_active": true,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
}
```

### 3.3 Get Teacher Details
**GET** `/api/teachers/{id}/`

Get detailed information about a specific teacher.

**Response (200 OK):**
```json
{
    "id": 1,
    "school": 1,
    "school_name": "Example School",
    "name": "John Doe",
    "subject_specialist": "Mathematics",
    "previous_subjects": ["Physics", "Chemistry"],
    "designation": "Senior Teacher",
    "qualification": "M.Sc. Mathematics",
    "is_class_teacher": true,
    "class_teacher_class": 10,
    "class_teacher_section": "A",
    "phone_number": "+1234567890",
    "email": "john.doe@school.com",
    "gender": "M",
    "gender_display": "Male",
    "date_joined": "2020-06-01",
    "experience_years": 5,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

### 3.4 Update Teacher
**PUT** `/api/teachers/{id}/`

Update a teacher's complete information.

**Request Body:**
```json
{
    "name": "John Doe Updated",
    "subject_specialist": "Advanced Mathematics",
    "previous_subjects": ["Physics", "Chemistry", "Statistics"],
    "designation": "Head of Mathematics",
    "qualification": "Ph.D. Mathematics",
    "is_class_teacher": false,
    "phone_number": "+1234567891",
    "email": "john.doe.updated@school.com",
    "gender": "M",
    "date_joined": "2020-06-01",
    "experience_years": 6
}
```

### 3.5 Partial Update Teacher
**PATCH** `/api/teachers/{id}/`

Partially update a teacher's information.

**Request Body:**
```json
{
    "designation": "Head of Mathematics",
    "experience_years": 6
}
```

### 3.6 Deactivate Teacher
**DELETE** `/api/teachers/{id}/`

Soft delete a teacher by setting is_active to false.

**Response (200 OK):**
```json
{
    "message": "Teacher deactivated successfully"
}
```

### 3.7 Activate Teacher
**PATCH** `/api/teachers/{id}/activate/`

Reactivate a deactivated teacher.

**Response (200 OK):**
```json
{
    "message": "Teacher activated successfully",
    "data": {
        "id": 1,
        "school": 1,
        "school_name": "Example School",
        "name": "John Doe",
        "subject_specialist": "Mathematics",
        "designation": "Senior Teacher",
        "is_class_teacher": true,
        "class_teacher_class": 10,
        "class_teacher_section": "A",
        "is_active": true,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
}
```

### 3.8 Teacher Statistics
**GET** `/api/teachers/stats/`

Get teacher statistics for the authenticated school.

**Response (200 OK):**
```json
{
    "total_teachers": 10,
    "active_teachers": 8,
    "inactive_teachers": 2,
    "class_teachers": 5,
    "subject_teachers": 3,
    "by_designation": {
        "Senior Teacher": 3,
        "Teacher": 4,
        "Head of Department": 1
    },
    "by_gender": {
        "Male": 4,
        "Female": 4,
        "Not Specified": 0
    }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
    "field_name": ["Error message"]
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
    "detail": "Not found."
}
```

---

## Validation Rules

### Teacher Model Validation
- `is_class_teacher`: If true, both `class_teacher_class` and `class_teacher_section` are required
- `class_teacher_class`: Must be between 1 and 20
- `experience_years`: Must be between 0 and 50
- `gender`: Must be one of 'M', 'F', or 'O'
- `school_code`: Must be unique across all schools

### School Profile Validation
- `number_of_classes`: Must be between 1 and 20
- `period_duration_minutes`: Must be between 30 and 120
- `total_periods_per_day`: Must be between 1 and 10 