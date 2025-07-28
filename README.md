# University Management System (ERP)

A comprehensive Django-based University Management System designed to handle all aspects of university operations including student management, academic records, faculty administration, research tracking, library management, and financial operations.

## 🎯 Features

### 👥 User Management
- **Multi-role Authentication**: Students, Lecturers, Professors, Staff, Admins, Deans, HODs
- **Custom User Model**: Extended Django user with university-specific fields
- **Role-based Access Control**: Different permissions for different user types
- **Profile Management**: Complete user profiles with photos, contact information

### 🏛️ Academic Structure
- **Faculty Management**: Organize university into faculties
- **Department Management**: Departments within faculties with HODs
- **Programme Management**: Bachelor's, Master's, PhD, Diploma, Certificate programs
- **Course Management**: Individual courses with prerequisites, credit hours, and levels

### 👨‍🎓 Student Management
- **Student Registration**: Complete student profiles with academic history
- **Enrollment System**: Course enrollment with semester-based tracking
- **Academic Progress**: GPA calculation, credit hour tracking
- **Student Status**: Active, graduated, suspended, deferred status management
- **Guardian Information**: Emergency contacts and next-of-kin details

### 👨‍🏫 Faculty Management
- **Academic Ranks**: Professor, Associate Professor, Senior Lecturer, etc.
- **Employment Types**: Permanent, contract, part-time, visiting, adjunct
- **Professional Profiles**: Qualifications, research interests, publications
- **Teaching Assignments**: Course allocations and timetable management

### 📚 Academic Operations
- **Timetable Management**: Class scheduling with venue and time slots
- **Attendance Tracking**: Digital attendance with multiple status options
- **Examination System**: Exam scheduling, venue booking, invigilation
- **Grading System**: Comprehensive grading with GPA calculation
- **Academic Calendar**: Semester and academic year management

### 🔬 Research Management
- **Research Projects**: Track undergraduate, masters, PhD, and faculty research
- **Collaboration Tracking**: Principal investigators and co-investigators
- **Funding Management**: Research grants and funding sources
- **Ethics Approval**: Research ethics compliance tracking
- **Publication Tracking**: Research outcomes and publications

### 📖 Library Management
- **Resource Catalog**: Books, journals, e-books, multimedia resources
- **Borrowing System**: Check-out, return, renewal, reservation
- **Digital Resources**: Online databases and e-resource access
- **Fine Management**: Overdue and damage fine calculations
- **Inventory Management**: Track available and total copies

### 🏠 Accommodation Management
- **Hostel Management**: Male, female, mixed, and family hostels
- **Room Allocation**: Student room assignments with capacity tracking
- **Warden Management**: Hostel staff assignments
- **Occupancy Tracking**: Real-time room availability

### 💰 Financial Management
- **Fee Structure**: Comprehensive fee breakdown by programme and year
- **Payment Processing**: Multiple payment methods (M-Pesa, bank transfer, etc.)
- **Financial Aid**: Government subsidies, scholarships, bursaries
- **Payment Tracking**: Receipt generation and payment status monitoring
- **Fee Reports**: Financial reporting and analytics

### 📱 Communication System
- **Notification System**: University-wide announcements
- **Priority Levels**: Urgent, high, medium, low priority messages
- **Multi-channel**: Email, SMS, and in-app notifications
- **Targeted Messaging**: Role-based and individual messaging

## 🛠️ Technology Stack

- **Backend**: Django 4.x (Python)
- **Database**: PostgreSQL (recommended) / MySQL / SQLite
- **Authentication**: Django's built-in authentication system
- **File Storage**: Django's file handling system
- **API**: Django REST Framework (optional for API endpoints)

## 📋 Prerequisites

- Python 3.8+
- Django 4.0+
- PostgreSQL 12+ (recommended)
- pip (Python package manager)
- virtualenv (recommended)

## ⚡ Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/university-management-system.git
cd university-management-system
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_NAME=university_db
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
```

### 5. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 6. Load Sample Data (Optional)

```bash
python manage.py loaddata fixtures/sample_data.json
```

### 7. Run Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

## 📊 Database Models Overview

### Core Models

| Model | Description |
|-------|-------------|
| `User` | Extended Django user model with university-specific fields |
| `Faculty` | University faculties (e.g., Engineering, Medicine) |
| `Department` | Academic departments within faculties |
| `Programme` | Degree programs offered by the university |
| `Course` | Individual courses/subjects |
| `Student` | Student profiles and academic information |
| `Lecturer` | Faculty members and teaching staff |
| `Staff` | Non-academic staff members |

### Academic Models

| Model | Description |
|-------|-------------|
| `AcademicYear` | Academic year definitions |
| `Semester` | Semester periods within academic years |
| `Enrollment` | Student course enrollments |
| `Grade` | Student grades and assessments |
| `Timetable` | Class scheduling and time slots |
| `Attendance` | Student attendance records |
| `Examination` | Exam scheduling and management |

### Additional Models

| Model | Description |
|-------|-------------|
| `Research` | Research projects and collaborations |
| `Library` | Library resources and catalog |
| `LibraryTransaction` | Book borrowing and returns |
| `Hostel` | University accommodation facilities |
| `HostelAllocation` | Student room assignments |
| `FeeStructure` | Fee breakdown by programme |
| `FeePayment` | Payment records and receipts |
| `Notification` | System notifications and announcements |

## 🔧 Configuration

### Settings Configuration

Key settings in `settings.py`:

```python
# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT'),
    }
}

# Media Files Configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Static Files Configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
```

## 🔐 User Roles and Permissions

### User Types

1. **Admin**: Full system access
2. **Dean**: Faculty-level management
3. **HOD**: Department-level management
4. **Professor/Lecturer**: Course management and grading
5. **Registrar**: Student records and academic administration
6. **Staff**: Limited access based on role
7. **Student**: Personal academic records and course materials

### Permission Structure

```python
# Custom permissions in models
class Meta:
    permissions = [
        ("view_student_records", "Can view student academic records"),
        ("manage_grades", "Can manage student grades"),
        ("manage_timetable", "Can manage class timetables"),
        ("manage_research", "Can manage research projects"),
        ("manage_library", "Can manage library resources"),
        ("manage_hostel", "Can manage hostel allocations"),
        ("manage_fees", "Can manage fee structures and payments"),
    ]
```

## 📈 Usage Examples

### Creating a New Student

```python
from myapp.models import User, Student, Programme

# Create user account
user = User.objects.create_user(
    username='john.doe',
    email='john.doe@university.edu',
    first_name='John',
    last_name='Doe',
    user_type='student'
)

# Create student profile
programme = Programme.objects.get(code='CS001')
student = Student.objects.create(
    user=user,
    student_id='UNI/2024/001',
    programme=programme,
    current_year=1,
    current_semester=1,
    admission_date='2024-09-01',
    guardian_name='Jane Doe',
    guardian_phone='+254700000000'
)
```

### Enrolling a Student in Courses

```python
from myapp.models import Student, Course, Semester, Enrollment

student = Student.objects.get(student_id='UNI/2024/001')
semester = Semester.objects.get(is_current=True)

# Get courses for the student's year and semester
courses = Course.objects.filter(
    course_programmes__programme=student.programme,
    course_programmes__year=student.current_year,
    course_programmes__semester=student.current_semester
)

# Enroll student in courses
for course in courses:
    Enrollment.objects.create(
        student=student,
        course=course,
        semester=semester
    )
```

### Recording Grades

```python
from myapp.models import Enrollment, Grade

enrollment = Enrollment.objects.get(
    student__student_id='UNI/2024/001',
    course__code='CS101'
)

grade = Grade.objects.create(
    enrollment=enrollment,
    continuous_assessment=75.0,
    final_exam=82.0,
    practical_marks=88.0
)
# Grade calculation happens automatically in save() method
```

## 🚀 Deployment

### Production Setup

1. **Environment Variables**:
   ```bash
   export DEBUG=False
   export ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   export DATABASE_URL=postgresql://user:password@localhost:5432/university_db
   ```

2. **Static Files**:
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Database Migration**:
   ```bash
   python manage.py migrate --run-syncdb
   ```

4. **Web Server Configuration** (Nginx + Gunicorn):
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location /static/ {
           alias /path/to/staticfiles/;
       }
       
       location /media/ {
           alias /path/to/media/;
       }
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Docker Deployment

```dockerfile
FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "university.wsgi:application"]
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test myapp

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Sample Test

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from myapp.models import Student, Programme

User = get_user_model()

class StudentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            user_type='student'
        )
        
    def test_student_creation(self):
        programme = Programme.objects.create(
            name='Computer Science',
            code='CS001',
            programme_type='bachelor'
        )
        
        student = Student.objects.create(
            user=self.user,
            student_id='TEST001',
            programme=programme
        )
        
        self.assertEqual(student.student_id, 'TEST001')
        self.assertEqual(str(student), f"{self.user.get_full_name()} - TEST001")
```

## 🤝 Contributing

1. **Fork the Repository**
2. **Create Feature Branch**: `git checkout -b feature/AmazingFeature`
3. **Commit Changes**: `git commit -m 'Add some AmazingFeature'`
4. **Push to Branch**: `git push origin feature/AmazingFeature`
5. **Open Pull Request**

### Development Guidelines

- Follow PEP 8 coding standards
- Write comprehensive tests for new features
- Update documentation for any changes
- Use meaningful commit messages
- Create migrations for model changes

## 📝 API Documentation

### Available Endpoints

```
GET /api/students/ - List all students
POST /api/students/ - Create new student
GET /api/students/{id}/ - Get student details
PUT /api/students/{id}/ - Update student
DELETE /api/students/{id}/ - Delete student

GET /api/courses/ - List all courses
GET /api/enrollments/ - List enrollments
GET /api/grades/ - List grades
GET /api/timetable/ - Get timetable
```

### Authentication

The API uses Django's session authentication and token authentication:

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ]
}
```

## 🔍 Troubleshooting

### Common Issues

1. **Migration Errors**:
   ```bash
   python manage.py makemigrations --empty yourappname
   python manage.py migrate --fake-initial
   ```

2. **Static Files Not Loading**:
   ```bash
   python manage.py collectstatic --clear
   ```

3. **Database Connection Issues**:
   - Check database credentials in `.env`
   - Ensure database server is running
   - Verify database exists

4. **Permission Denied Errors**:
   ```bash
   sudo chown -R $USER:$USER /path/to/project
   ```

### Performance Optimization

- Use database indexes on frequently queried fields
- Implement caching for static data
- Optimize database queries with `select_related()` and `prefetch_related()`
- Use pagination for large datasets

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Best Practices](https://django-best-practices.readthedocs.io/)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Support

For support and questions:

- **Email**: support@university-system.com
- **Documentation**: [Wiki](https://github.com/yourusername/university-management-system/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/university-management-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/university-management-system/discussions)

## 🚧 Roadmap

### Upcoming Features

- [ ] Mobile application (React Native/Flutter)
- [ ] Advanced reporting and analytics dashboard
- [ ] Integration with external payment gateways
- [ ] Online examination system
- [ ] Video conferencing integration
- [ ] Alumni management system
- [ ] Advanced search and filtering
- [ ] Multi-language support
- [ ] API rate limiting and throttling
- [ ] Advanced notification system with templates

### Version History

- **v1.0.0** - Initial release with core functionality
- **v1.1.0** - Added research management and library system
- **v1.2.0** - Implemented hostel management and notifications
- **v2.0.0** - Complete UI overhaul and API improvements

---

**Developed by Steve Ongera for Educational Institutions**