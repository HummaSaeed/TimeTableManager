# Timetable Management System - User Guide

## 📖 **Overview**

The Timetable Management System is a comprehensive web application designed for school administrators to manage teachers, classes, subjects, and generate automated timetables. This guide will walk you through all the features and how to use them effectively.

## 🚀 **Getting Started**

### **1. Registration & Login**

#### **School Registration**
1. Navigate to `/api/register/`
2. Provide your email and password
3. You'll receive access and refresh tokens
4. Use these tokens for API authentication

**Example Registration:**
```json
POST /api/register/
{
    "email": "admin@school.com",
    "password": "securepassword123",
    "password_confirm": "securepassword123"
}
```

#### **Login**
1. Navigate to `/api/login/`
2. Use your email and password
3. Receive new access tokens

### **2. School Profile Setup**

After registration, set up your school profile:

1. **Access Profile:** `GET /api/school-profile/`
2. **Update Profile:** `PUT /api/school-profile/`

**Required Information:**
- School name and code
- School timings (start/end times)
- Number of classes and periods
- Break times and working days

## 👥 **Teacher Management**

### **Adding Teachers**

1. **Create Teacher:** `POST /api/teachers/`
2. **View All Teachers:** `GET /api/teachers/`
3. **Update Teacher:** `PUT /api/teachers/{id}/`
4. **Deactivate Teacher:** `DELETE /api/teachers/{id}/`

**Teacher Information Required:**
- Name and email
- Subject specialization
- Designation and qualifications
- Class teacher assignments (if applicable)

### **Teacher Features**
- **Automatic Account Creation:** System creates user accounts for teachers
- **Password Generation:** Secure passwords are generated automatically
- **Email Notifications:** Welcome emails sent to new teachers
- **Status Management:** Activate/deactivate teachers as needed

## 📚 **Subject Management**

### **Adding Subjects**

1. **Create Subject:** `POST /api/subjects/`
2. **View All Subjects:** `GET /api/subjects/`
3. **Update Subject:** `PUT /api/subjects/{id}/`
4. **Deactivate Subject:** `DELETE /api/subjects/{id}/`

**Subject Information:**
- Name and code
- Description
- Active status

## 🏫 **Class Management**

### **Creating Classes**

1. **Create Class:** `POST /api/classes/`
2. **View All Classes:** `GET /api/classes/`
3. **Update Class:** `PUT /api/classes/{id}/`
4. **Deactivate Class:** `DELETE /api/classes/{id}/`

**Class Information:**
- Class name and section
- Total strength
- Room number
- Class teacher assignment
- Subject assignments

### **Class Features**
- **Subject Assignment:** Assign multiple subjects to classes
- **Teacher Assignment:** Assign class teachers
- **Room Management:** Track classroom assignments

## 👨‍🏫 **Teacher-Subject Assignments**

### **Managing Assignments**

1. **Create Assignment:** `POST /api/teacher-assignments/`
2. **View Assignments:** `GET /api/teacher-assignments/`
3. **Update Assignment:** `PUT /api/teacher-assignments/{id}/`
4. **Delete Assignment:** `DELETE /api/teacher-assignments/{id}/`

**Assignment Features:**
- **Primary Teachers:** Mark primary subject teachers
- **Period Limits:** Set maximum periods per week
- **Workload Management:** Track teacher workload

## 📅 **Timetable Management**

### **Generating Timetables**

1. **Generate Timetable:** `POST /api/timetable/generate/`
2. **View Timetable Slots:** `GET /api/timetable/slots/`
3. **Timetable Statistics:** `GET /api/timetable/stats/`

**Generation Parameters:**
- Academic year
- Clear existing timetables
- Maximum generation attempts

### **Timetable Features**
- **Automated Generation:** AI-powered timetable creation
- **Conflict Resolution:** Automatic conflict detection and resolution
- **Workload Balancing:** Even distribution of teacher workload
- **Period Optimization:** Efficient use of available periods

## 📊 **Reports & Analytics**

### **Teacher Statistics**
- **Teacher Stats:** `GET /api/teachers/stats/`
- **Weekly Workload:** `GET /api/teachers/workload/`

### **Class Statistics**
- **Class Stats:** `GET /api/classes/stats/`

### **Timetable Statistics**
- **Timetable Stats:** `GET /api/timetable/stats/`

## 🔄 **Substitution Management**

### **Teacher Absence Handling**

1. **Mark Absence:** `POST /api/teachers/absent/`
2. **Auto-Substitution:** System automatically finds substitute teachers
3. **Substitution Logs:** Track all substitutions

**Features:**
- **Automatic Substitution:** Find available substitute teachers
- **Workload Consideration:** Consider teacher workload limits
- **Conflict Avoidance:** Avoid double-booking teachers

## 🔧 **System Configuration**

### **School Settings**
- **Working Days:** Configure school working days
- **Period Duration:** Set period lengths
- **Break Times:** Configure break schedules
- **Academic Year:** Set current academic year

### **Time Management**
- **School Hours:** Set school start and end times
- **Friday Schedule:** Special Friday closing times
- **Break Schedule:** Lunch and other break times

## 📱 **API Usage**

### **Authentication**
All API requests require authentication using JWT tokens:

```bash
Authorization: Bearer <your_access_token>
```

### **Common Headers**
```bash
Content-Type: application/json
Authorization: Bearer <token>
```

### **Response Format**
All API responses follow this format:
```json
{
    "message": "Success message",
    "data": {...},
    "count": 10
}
```

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Authentication Errors**
   - Check token validity
   - Ensure proper Authorization header
   - Refresh tokens if expired

2. **Data Validation Errors**
   - Check required fields
   - Validate data formats
   - Ensure unique constraints

3. **Timetable Generation Issues**
   - Verify teacher-subject assignments
   - Check class-subject assignments
   - Ensure sufficient teachers available

### **Error Handling**
- **400 Bad Request:** Invalid data or missing fields
- **401 Unauthorized:** Invalid or missing authentication
- **403 Forbidden:** Insufficient permissions
- **404 Not Found:** Resource doesn't exist
- **500 Internal Server Error:** Server-side issues

## 📞 **Support**

### **Getting Help**
1. Check the troubleshooting section
2. Review API documentation
3. Contact system administrator
4. Check error logs

### **Useful Endpoints**
- **API Documentation:** `/swagger/` or `/redoc/`
- **Admin Interface:** `/admin/`
- **Health Check:** Check server status

## 📋 **Best Practices**

### **Data Management**
1. **Regular Backups:** Backup data regularly
2. **Data Validation:** Always validate input data
3. **Consistent Naming:** Use consistent naming conventions
4. **Status Management:** Keep teacher/class statuses current

### **Timetable Generation**
1. **Complete Setup:** Ensure all data is properly set up
2. **Teacher Assignments:** Verify all teacher-subject assignments
3. **Class Setup:** Ensure classes have assigned subjects
4. **Review Results:** Always review generated timetables

### **Security**
1. **Strong Passwords:** Use strong passwords
2. **Token Management:** Keep tokens secure
3. **Regular Updates:** Update passwords regularly
4. **Access Control:** Limit access to authorized users

---

## 📚 **Additional Resources**

- **API Documentation:** Complete API reference
- **Enhanced API Docs:** Detailed examples and use cases
- **Troubleshooting Guide:** Common issues and solutions
- **Admin Guide:** Django admin interface usage

---

*Last updated: August 8, 2025*
*Version: 1.0.0* 