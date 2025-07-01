# Class Management API Documentation

## Base URL
```
http://localhost:8000/
```

## Authentication
All API endpoints require JWT authentication. Include the access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## 1. Subject Management Endpoints

### 1.1 List Subjects
**GET** `/api/subjects/`

Get all subjects for the authenticated school with filtering, searching, and pagination.

**Query Parameters:**
- `is_active` (boolean): Filter by active status
- `search` (string): Search in name, code
- `ordering` (string): Order by name, code, created_at
- `page` (integer): Page number for pagination

**Example Request:**
```
GET /api/subjects/?is_active=true&search=math&ordering=name
```

**Response (200 OK):**
```json
{
    "count": 3,
    "results": [
        {
            "id": 1,
            "name": "Mathematics",
            "code": "MATH101",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": 2,
            "name": "Physics",
            "code": "PHY101",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": 3,
            "name": "Chemistry",
            "code": "CHEM101",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

### 1.2 Create Subject
**POST** `/api/subjects/`

Create a new subject for the authenticated school.

**Request Body:**
```json
{
    "name": "Advanced Mathematics",
    "code": "MATH201",
    "description": "Advanced level mathematics including calculus and algebra"
}
```

**Response (201 Created):**
```json
{
    "message": "Subject created successfully",
    "data": {
        "id": 4,
        "school": 1,
        "school_name": "Example School",
        "name": "Advanced Mathematics",
        "code": "MATH201",
        "description": "Advanced level mathematics including calculus and algebra",
        "is_active": true,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
}
```

### 1.3 Get Subject Details
**GET** `/api/subjects/{id}/`

Get detailed information about a specific subject.

**Response (200 OK):**
```json
{
    "id": 1,
    "school": 1,
    "school_name": "Example School",
    "name": "Mathematics",
    "code": "MATH101",
    "description": "Basic mathematics including algebra and geometry",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

### 1.4 Update Subject
**PUT** `/api/subjects/{id}/`

Update a subject's complete information.

**Request Body:**
```json
{
    "name": "Mathematics Updated",
    "code": "MATH101",
    "description": "Updated description for mathematics"
}
```

### 1.5 Partial Update Subject
**PATCH** `/api/subjects/{id}/`

Partially update a subject's information.

**Request Body:**
```json
{
    "description": "New description for mathematics"
}
```

### 1.6 Deactivate Subject
**DELETE** `/api/subjects/{id}/`

Soft delete a subject by setting is_active to false.

**Response (200 OK):**
```json
{
    "message": "Subject deactivated successfully"
}
```

### 1.7 Activate Subject
**PATCH** `/api/subjects/{id}/activate/`

Reactivate a deactivated subject.

**Response (200 OK):**
```json
{
    "message": "Subject activated successfully",
    "data": {
        "id": 1,
        "school": 1,
        "school_name": "Example School",
        "name": "Mathematics",
        "code": "MATH101",
        "description": "Basic mathematics including algebra and geometry",
        "is_active": true,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
}
```

---

## 2. Class Management Endpoints

### 2.1 List Classes
**GET** `/api/classes/`

Get all classes for the authenticated school with filtering, searching, and pagination.

**Query Parameters:**
- `is_active` (boolean): Filter by active status
- `class_name` (string): Filter by class name
- `section` (string): Filter by section
- `search` (string): Search in class_name, section, room_number
- `ordering` (string): Order by class_name, section, total_strength, created_at
- `page` (integer): Page number for pagination

**Example Request:**
```
GET /api/classes/?is_active=true&class_name=Class 10&ordering=section
```

**Response (200 OK):**
```json
{
    "count": 2,
    "results": [
        {
            "id": 1,
            "class_name": "Class 10",
            "section": "A",
            "total_strength": 35,
            "room_number": "101",
            "class_teacher_name": "John Doe",
            "subjects_count": 5,
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": 2,
            "class_name": "Class 10",
            "section": "B",
            "total_strength": 32,
            "room_number": "102",
            "class_teacher_name": "Jane Smith",
            "subjects_count": 5,
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

### 2.2 Create Class
**POST** `/api/classes/`

Create a new class for the authenticated school.

**Request Body:**
```json
{
    "class_name": "Class 11",
    "section": "A",
    "total_strength": 30,
    "room_number": "201",
    "class_teacher": 1,
    "start_time": "08:00:00",
    "end_time": "14:00:00",
    "subjects": [1, 2, 3, 4, 5]
}
```

**Response (201 Created):**
```json
{
    "message": "Class created successfully",
    "data": {
        "id": 3,
        "school": 1,
        "school_name": "Example School",
        "class_name": "Class 11",
        "section": "A",
        "total_strength": 30,
        "room_number": "201",
        "class_teacher": 1,
        "class_teacher_name": "John Doe",
        "start_time": "08:00:00",
        "end_time": "14:00:00",
        "subjects": [1, 2, 3, 4, 5],
        "subjects_list": [
            {
                "id": 1,
                "name": "Mathematics",
                "code": "MATH101",
                "is_active": true,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "name": "Physics",
                "code": "PHY101",
                "is_active": true,
                "created_at": "2024-01-01T00:00:00Z"
            }
        ],
        "is_active": true,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
}
```

### 2.3 Get Class Details
**GET** `/api/classes/{id}/`

Get detailed information about a specific class.

**Response (200 OK):**
```json
{
    "id": 1,
    "school": 1,
    "school_name": "Example School",
    "class_name": "Class 10",
    "section": "A",
    "total_strength": 35,
    "room_number": "101",
    "class_teacher": 1,
    "class_teacher_name": "John Doe",
    "start_time": "08:00:00",
    "end_time": "14:00:00",
    "subjects": [1, 2, 3, 4, 5],
    "subjects_list": [
        {
            "id": 1,
            "name": "Mathematics",
            "code": "MATH101",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": 2,
            "name": "Physics",
            "code": "PHY101",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z"
        }
    ],
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

### 2.4 Update Class
**PUT** `/api/classes/{id}/`

Update a class's complete information.

**Request Body:**
```json
{
    "class_name": "Class 10",
    "section": "A",
    "total_strength": 38,
    "room_number": "103",
    "class_teacher": 2,
    "start_time": "08:30:00",
    "end_time": "14:30:00",
    "subjects": [1, 2, 3, 4, 5, 6]
}
```

### 2.5 Partial Update Class
**PATCH** `/api/classes/{id}/`

Partially update a class's information.

**Request Body:**
```json
{
    "total_strength": 40,
    "room_number": "104"
}
```

### 2.6 Deactivate Class
**DELETE** `/api/classes/{id}/`

Soft delete a class by setting is_active to false.

**Response (200 OK):**
```json
{
    "message": "Class deactivated successfully"
}
```

### 2.7 Activate Class
**PATCH** `/api/classes/{id}/activate/`

Reactivate a deactivated class.

**Response (200 OK):**
```json
{
    "message": "Class activated successfully",
    "data": {
        "id": 1,
        "school": 1,
        "school_name": "Example School",
        "class_name": "Class 10",
        "section": "A",
        "total_strength": 35,
        "room_number": "101",
        "class_teacher": 1,
        "class_teacher_name": "John Doe",
        "is_active": true,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
}
```

### 2.8 Class Statistics
**GET** `/api/classes/stats/`

Get class statistics for the authenticated school.

**Response (200 OK):**
```json
{
    "total_classes": 8,
    "active_classes": 7,
    "inactive_classes": 1,
    "total_students": 245,
    "by_class_name": {
        "Class 10": 2,
        "Class 11": 2,
        "Class 12": 2,
        "Class 9": 1
    },
    "by_section": {
        "A": 4,
        "B": 3
    },
    "classes_with_teachers": 6,
    "classes_without_teachers": 1
}
```

---

## 3. Validation Rules

### Subject Model Validation
- `name`: Required, max length 100 characters
- `code`: Required, max length 20 characters, must be unique within the school
- `description`: Optional text field
- `is_active`: Boolean field, defaults to True

### Class Model Validation
- `class_name`: Required, max length 50 characters
- `section`: Required, max length 10 characters
- `total_strength`: Required integer between 1 and 100
- `room_number`: Required, max length 20 characters
- `class_teacher`: Optional foreign key to Teacher (must belong to same school and be active)
- `start_time`: Optional time field
- `end_time`: Optional time field
- `subjects`: Optional many-to-many relationship with Subject
- `is_active`: Boolean field, defaults to True

### Unique Constraints
- Subject: `school` + `code` combination must be unique
- Class: `school` + `class_name` + `section` combination must be unique

### Cross-Validation Rules
- Class teacher must belong to the same school as the class
- Class teacher must be active
- Subjects must belong to the same school as the class

---

## 4. Error Responses

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

## 5. Use Cases

### 5.1 Creating a Complete Class Setup
1. **Create Subjects First:**
   ```bash
   POST /api/subjects/
   {
       "name": "Mathematics",
       "code": "MATH101",
       "description": "Basic mathematics"
   }
   ```

2. **Create Teachers:**
   ```bash
   POST /api/teachers/
   {
       "name": "John Doe",
       "email": "john.doe@school.com",
       "subject_specialist": "Mathematics",
       "designation": "Senior Teacher",
       "qualification": "M.Sc. Mathematics"
   }
   ```

3. **Create Class with Teacher and Subjects:**
   ```bash
   POST /api/classes/
   {
       "class_name": "Class 10",
       "section": "A",
       "total_strength": 35,
       "room_number": "101",
       "class_teacher": 1,
       "subjects": [1, 2, 3]
   }
   ```

### 5.2 Managing Class Assignments
- Assign/change class teachers
- Add/remove subjects from classes
- Update student strength
- Change room assignments

### 5.3 Reporting and Analytics
- Get class statistics
- View subjects per class
- Track teacher assignments
- Monitor class capacity

---

## 6. Future Enhancements

1. **Timetable Integration**: Link classes to specific time slots
2. **Student Management**: Add student enrollment to classes
3. **Attendance Tracking**: Track student attendance per class
4. **Grade Management**: Associate grades with subjects and classes
5. **Room Scheduling**: Prevent room conflicts during timetable generation
6. **Class Capacity Management**: Automatic alerts for over-capacity classes 