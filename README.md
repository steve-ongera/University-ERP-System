# University Management System (ERP) with Bank Integration

A comprehensive Django-based University Management System designed to handle all aspects of university operations including student management, academic records, faculty administration, research tracking, library management, financial operations, and **automated bank payment integration**.

## 🎯 Key Highlights

- **Multi-role Authentication & Access Control**
- **Complete Academic Management Suite**
- **Real-time Bank Payment Integration** (Equity Bank, KCB Bank, M-Pesa)
- **Automated Fee Processing & Reconciliation**
- **Research & Library Management**
- **Hostel & Accommodation System**
- **Communication & Notification System**

---

## Table of Contents

1. [Core Features](#-core-features)
2. [Bank Integration Overview](#-bank-integration-overview)
3. [Technology Stack](#-technology-stack)
4. [Prerequisites](#-prerequisites)
5. [Quick Start Guide](#-quick-start)
6. [Bank API Integration Setup](#-bank-api-integration-setup)
7. [Database Models](#-database-models-overview)
8. [Configuration](#-configuration)
9. [Security & Compliance](#-security-considerations)
10. [Testing & Deployment](#-testing--deployment)
11. [API Documentation](#-api-documentation)
12. [Troubleshooting](#-troubleshooting)
13. [Support & Contributing](#-support--contributing)

---

## 🎯 Core Features

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

### 💰 Financial Management (With Bank Integration)
- **Fee Structure**: Comprehensive fee breakdown by programme and year
- **Payment Processing**: Multiple payment methods (M-Pesa, bank transfer, etc.)
- **Real-time Bank Integration**: Automated payment posting from banks
- **Financial Aid**: Government subsidies, scholarships, bursaries
- **Payment Tracking**: Receipt generation and payment status monitoring
- **Automated Reconciliation**: Bank-to-ERP synchronization
- **Fee Reports**: Financial reporting and analytics

### 📱 Communication System
- **Notification System**: University-wide announcements
- **Priority Levels**: Urgent, high, medium, low priority messages
- **Multi-channel**: Email, SMS, and in-app notifications
- **Targeted Messaging**: Role-based and individual messaging
- **Payment Notifications**: Automatic receipts via SMS/Email

---

## 🏦 Bank Integration Overview

### How It Works

This integration allows **automatic posting of student fee payments** from Equity Bank, KCB Bank, and M-Pesa directly into the university ERP system without manual intervention.

#### Benefits

✅ **Real-time Updates**: Payments reflect immediately in student accounts  
✅ **Zero Manual Entry**: Eliminates data entry errors  
✅ **24/7 Processing**: Works even outside business hours  
✅ **Automatic Receipts**: Students receive instant confirmation  
✅ **Easy Reconciliation**: Automated tracking and auditing  

#### Payment Flow

```
Student Pays at Bank/M-Pesa
        ↓
Bank System Captures Payment
        ↓
Bank API Sends Webhook to ERP
        ↓
ERP Validates Student & Amount
        ↓
Creates Payment Record & Updates Account
        ↓
Sends SMS/Email Receipt to Student
        ↓
Student Receives Confirmation
```

#### Technical Process

1. **Student makes payment** at Equity/KCB bank or via M-Pesa
2. **Bank captures** student ID and amount
3. **Bank API sends webhook** to your ERP endpoint
4. **ERP validates** the payment data
5. **Database transaction** creates payment record
6. **Notifications sent** to student via SMS and email
7. **Receipt generated** with unique number

---

## 🛠️ Technology Stack

- **Backend**: Django 4.x (Python)
- **Database**: PostgreSQL (recommended) / MySQL / SQLite
- **Authentication**: Django's built-in authentication system
- **File Storage**: Django's file handling system
- **API Framework**: Django REST Framework
- **Bank Integration**: Webhook-based REST APIs
- **Payment Gateways**: Equity Bank API, KCB Bank API, M-Pesa Daraja API
- **Message Queue**: Celery + Redis (for async processing)
- **SMS Gateway**: Africa's Talking / Twilio
- **Email**: SMTP (Gmail, SendGrid, etc.)

---

## 📋 Prerequisites

### System Requirements

- Python 3.8+
- Django 4.0+
- PostgreSQL 12+ (recommended)
- Redis (for Celery tasks)
- pip (Python package manager)
- virtualenv (recommended)

### Bank Requirements

#### Equity Bank
- Corporate account with API access
- Merchant code/identification number
- API credentials (API Key + Secret Key)
- Webhook URL whitelisting

#### KCB Bank
- Business banking account
- API integration agreement
- API credentials
- SSL certificate

#### M-Pesa (Safaricom)
- Paybill or Till Number
- M-Pesa Daraja API credentials
- Shortcode and passkey
- Callback URL registration

### Additional Services
- SMS Gateway account (Africa's Talking recommended)
- Email SMTP credentials
- SSL certificate for production
- Domain name with HTTPS

---

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
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DATABASE_NAME=university_db
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password

# SMS Configuration (Africa's Talking)
AT_USERNAME=your_username
AT_API_KEY=your_api_key
AT_SENDER_ID=MUT

# Equity Bank API
EQUITY_API_URL=https://api.equitybank.co.ke/v1
EQUITY_MERCHANT_CODE=your_merchant_code
EQUITY_API_KEY=your_api_key
EQUITY_SECRET_KEY=your_secret_key

# KCB Bank API
KCB_API_URL=https://api.kcbgroup.com/v1
KCB_CLIENT_ID=your_client_id
KCB_CLIENT_SECRET=your_client_secret
KCB_MERCHANT_ID=your_merchant_id

# M-Pesa API
MPESA_ENVIRONMENT=sandbox  # or production
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://yourdomain.com/api/mpesa/callback/

# Celery/Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
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

### 7. Start Redis and Celery (For Bank Integration)

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker
celery -A university worker -l info

# Terminal 3: Start Celery Beat (for scheduled tasks)
celery -A university beat -l info
```

### 8. Run Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

---

## 🏦 Bank API Integration Setup

### Step 1: Install Additional Dependencies

```bash
pip install celery redis requests djangorestframework africastalking
```

### Step 2: Create Bank Integration Models

Add to `models.py`:

```python
from django.db import models
from django.utils import timezone

class BankPayment(models.Model):
    BANK_CHOICES = [
        ('equity', 'Equity Bank'),
        ('kcb', 'KCB Bank'),
        ('mpesa', 'M-Pesa'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('reversed', 'Reversed'),
    ]
    
    transaction_id = models.CharField(max_length=100, unique=True)
    bank_type = models.CharField(max_length=20, choices=BANK_CHOICES)
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference_number = models.CharField(max_length=100, blank=True)
    raw_data = models.JSONField(blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['student', 'payment_date']),
        ]
    
    def __str__(self):
        return f"{self.bank_type} - {self.transaction_id}"
```

### Step 3: Create Webhook Views

Create `views/bank_webhooks.py`:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .tasks import process_bank_payment
import json
import hmac
import hashlib

@method_decorator(csrf_exempt, name='dispatch')
class EquityWebhookView(APIView):
    def post(self, request):
        try:
            # Verify signature
            signature = request.headers.get('X-Equity-Signature')
            if not self.verify_signature(request.body, signature):
                return Response({'error': 'Invalid signature'}, 
                              status=status.HTTP_401_UNAUTHORIZED)
            
            data = request.data
            
            # Extract payment details
            payment_data = {
                'transaction_id': data.get('transactionId'),
                'student_id': data.get('studentId'),
                'amount': data.get('amount'),
                'bank_type': 'equity',
                'raw_data': data
            }
            
            # Process asynchronously
            process_bank_payment.delay(payment_data)
            
            return Response({'status': 'accepted'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': str(e)}, 
                          status=status.HTTP_400_BAD_REQUEST)
    
    def verify_signature(self, payload, signature):
        secret = settings.EQUITY_SECRET_KEY
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


@method_decorator(csrf_exempt, name='dispatch')
class KCBWebhookView(APIView):
    def post(self, request):
        # Similar implementation for KCB
        pass


@method_decorator(csrf_exempt, name='dispatch')
class MPesaWebhookView(APIView):
    def post(self, request):
        try:
            data = request.data
            
            # M-Pesa specific parsing
            result = data.get('Body', {}).get('stkCallback', {})
            
            if result.get('ResultCode') == 0:
                items = result.get('CallbackMetadata', {}).get('Item', [])
                
                payment_data = {
                    'transaction_id': result.get('CheckoutRequestID'),
                    'amount': next((i['Value'] for i in items if i['Name'] == 'Amount'), 0),
                    'phone': next((i['Value'] for i in items if i['Name'] == 'PhoneNumber'), ''),
                    'bank_type': 'mpesa',
                    'raw_data': data
                }
                
                process_bank_payment.delay(payment_data)
            
            return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})
            
        except Exception as e:
            return Response({'error': str(e)}, 
                          status=status.HTTP_400_BAD_REQUEST)
```

### Step 4: Create Celery Tasks

Create `tasks.py`:

```python
from celery import shared_task
from django.db import transaction
from .models import BankPayment, Student, FeePayment
from .utils import send_sms, send_email
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_bank_payment(payment_data):
    try:
        with transaction.atomic():
            # Create bank payment record
            bank_payment = BankPayment.objects.create(
                transaction_id=payment_data['transaction_id'],
                bank_type=payment_data['bank_type'],
                amount=payment_data['amount'],
                raw_data=payment_data.get('raw_data'),
                status='pending'
            )
            
            # Find student
            student = Student.objects.get(student_id=payment_data['student_id'])
            bank_payment.student = student
            
            # Create fee payment
            fee_payment = FeePayment.objects.create(
                student=student,
                amount=payment_data['amount'],
                payment_method=payment_data['bank_type'],
                transaction_id=payment_data['transaction_id'],
                status='completed'
            )
            
            # Update bank payment status
            bank_payment.status = 'completed'
            bank_payment.processed_at = timezone.now()
            bank_payment.save()
            
            # Send notifications
            send_payment_notifications.delay(student.id, fee_payment.id)
            
            logger.info(f"Payment processed: {payment_data['transaction_id']}")
            
    except Student.DoesNotExist:
        logger.error(f"Student not found: {payment_data.get('student_id')}")
        bank_payment.status = 'failed'
        bank_payment.save()
    except Exception as e:
        logger.error(f"Payment processing error: {str(e)}")
        raise


@shared_task
def send_payment_notifications(student_id, payment_id):
    try:
        student = Student.objects.get(id=student_id)
        payment = FeePayment.objects.get(id=payment_id)
        
        # Send SMS
        message = f"Payment of KES {payment.amount} received. Receipt: {payment.receipt_number}. Balance: KES {student.get_balance()}"
        send_sms(student.user.phone_number, message)
        
        # Send Email
        subject = "Payment Confirmation - MUT"
        email_message = f"""
        Dear {student.user.get_full_name()},
        
        Your payment has been received:
        Amount: KES {payment.amount}
        Receipt: {payment.receipt_number}
        Date: {payment.payment_date}
        
        Thank you.
        """
        send_email(student.user.email, subject, email_message)
        
    except Exception as e:
        logger.error(f"Notification error: {str(e)}")
```

### Step 5: Add URL Routing

In `urls.py`:

```python
from django.urls import path
from .views import bank_webhooks

urlpatterns = [
    # ... other URLs
    path('api/webhooks/equity/', bank_webhooks.EquityWebhookView.as_view()),
    path('api/webhooks/kcb/', bank_webhooks.KCBWebhookView.as_view()),
    path('api/webhooks/mpesa/', bank_webhooks.MPesaWebhookView.as_view()),
]
```

### Step 6: Configure Bank Webhooks

#### Equity Bank
1. Log in to Equity API portal
2. Navigate to Webhooks section
3. Add webhook URL: `https://yourdomain.com/api/webhooks/equity/`
4. Select events: `payment.received`
5. Save and test

#### KCB Bank
1. Contact KCB API support
2. Provide webhook URL: `https://yourdomain.com/api/webhooks/kcb/`
3. Request webhook activation
4. Test with sandbox

#### M-Pesa
1. Log in to M-Pesa Developer Portal
2. Register callback URL: `https://yourdomain.com/api/webhooks/mpesa/`
3. Configure validation URL (optional)
4. Test with sandbox

---

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

### Financial Models

| Model | Description |
|-------|-------------|
| `FeeStructure` | Fee breakdown by programme |
| `FeePayment` | Payment records and receipts |
| `BankPayment` | Bank transaction records |
| `FinancialAid` | Scholarships and bursaries |

### Additional Models

| Model | Description |
|-------|-------------|
| `Research` | Research projects and collaborations |
| `Library` | Library resources and catalog |
| `LibraryTransaction` | Book borrowing and returns |
| `Hostel` | University accommodation facilities |
| `HostelAllocation` | Student room assignments |
| `Notification` | System notifications and announcements |

---

## 🔧 Configuration

### Django Settings

Key configurations in `settings.py`:

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

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Nairobi'

# Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Static Files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

# Bank API Settings
EQUITY_API_URL = os.getenv('EQUITY_API_URL')
EQUITY_MERCHANT_CODE = os.getenv('EQUITY_MERCHANT_CODE')
EQUITY_API_KEY = os.getenv('EQUITY_API_KEY')
EQUITY_SECRET_KEY = os.getenv('EQUITY_SECRET_KEY')

KCB_API_URL = os.getenv('KCB_API_URL')
KCB_CLIENT_ID = os.getenv('KCB_CLIENT_ID')
KCB_CLIENT_SECRET = os.getenv('KCB_CLIENT_SECRET')

MPESA_ENVIRONMENT = os.getenv('MPESA_ENVIRONMENT', 'sandbox')
MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')
MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE')
MPESA_PASSKEY = os.getenv('MPESA_PASSKEY')

# SMS Configuration (Africa's Talking)
AT_USERNAME = os.getenv('AT_USERNAME')
AT_API_KEY = os.getenv('AT_API_KEY')
AT_SENDER_ID = os.getenv('AT_SENDER_ID', 'MUT')

# Security Settings
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

---

## 🔐 Security Considerations

### 1. API Authentication

```python
# Implement signature verification for all webhooks
def verify_bank_signature(payload, signature, secret_key):
    expected = hmac.new(
        secret_key.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### 2. IP Whitelisting

```python
# Middleware to whitelist bank IPs
ALLOWED_BANK_IPS = [
    '196.201.214.0/24',  # Equity Bank
    '41.90.64.0/24',     # KCB Bank
    '196.201.233.0/24',  # Safaricom
]
```

### 3. Data Encryption

- Store sensitive data encrypted in database
- Use HTTPS for all communications
- Implement SSL certificate pinning

### 4. Transaction Logging

```python
# Log all transactions for audit
class TransactionLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    transaction_type = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    details = models.JSONField()
    ip_address = models.GenericIPAddressField()
```

### 5. Rate Limiting

```python
# Use Django REST Framework throttling
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'webhook': '10000/hour'
    }
}
```

---

## 🧪 Testing & Deployment

### Unit Tests

```python
from django.test import TestCase
from myapp.models import BankPayment, Student

class BankPaymentTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            student_id='MUT/2024/001',
            # ... other fields
        )
    
    def test_payment_processing(self):
        payment_data = {
            'transaction_id': 'TEST123',
            'student_id': 'MUT/2024/001',
            'amount': 50000,
            'bank_type': 'equity'
        }
        
        from myapp.tasks import process_bank_payment
        process_bank_payment(payment_data)
        
        payment = BankPayment.objects.get(transaction_id='TEST123')
        self.assertEqual(payment.status, 'completed')
        self.assertEqual(payment.student, self.student)
```

### Integration Testing

```bash
# Test Equity webhook
curl -X POST https://yourdomain.com/api/webhooks/equity/ \
  -H "Content-Type: application/json" \
  -H "X-Equity-Signature: your-signature" \
  -d '{
    "transactionId": "EQ123456",
    "studentId": "MUT/2024/001",
    "amount": 50000,
    "timestamp": "2024-01-15T10:30:00Z"
  }'

# Test M-Pesa webhook
curl -X POST https://yourdomain.com/api/webhooks/mpesa/ \
  -H "Content-Type: application/json" \
  -d '{
    "Body": {
      "stkCallback": {
        "ResultCode": 0,
        "CheckoutRequestID": "ws_CO_150420241030",
        "CallbackMetadata": {
          "Item": [
            {"Name": "Amount", "Value": 50000},
            {"Name": "PhoneNumber", "Value": "254712345678"}
          ]
        }
      }
    }
  }'
```

### Production Deployment

#### 1. Server Setup (Ubuntu/Debian)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3-pip python3-venv postgresql nginx redis-server -y

# Create application user
sudo useradd -m -s /bin/bash mutadmin
sudo su - mutadmin
```

#### 2. Application Setup

```bash
# Clone repository
git clone https://github.com/yourusername/university-erp.git
cd university-erp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt gunicorn

# Configure environment
cp .env.example .env
nano .env  # Edit with production values

# Database setup
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

#### 3. Gunicorn Configuration

Create `/etc/systemd/system/mut-erp.service`:

```ini
[Unit]
Description=MUT ERP Gunicorn Service
After=network.target

[Service]
User=mutadmin
Group=www-data
WorkingDirectory=/home/mutadmin/university-erp
Environment="PATH=/home/mutadmin/university-erp/venv/bin"
ExecStart=/home/mutadmin/university-erp/venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/home/mutadmin/university-erp/mut-erp.sock \
    university.wsgi:application

[Install]
WantedBy=multi-user.target
```

#### 4. Celery Configuration

Create `/etc/systemd/system/mut-celery.service`:

```ini
[Unit]
Description=MUT ERP Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=mutadmin
Group=www-data
WorkingDirectory=/home/mutadmin/university-erp
Environment="PATH=/home/mutadmin/university-erp/venv/bin"
ExecStart=/home/mutadmin/university-erp/venv/bin/celery -A university worker -l info

[Install]
WantedBy=multi-user.target
```

#### 5. Nginx Configuration

Create `/etc/nginx/sites-available/mut-erp`:

```nginx
server {
    listen 80;
    server_name erp.mut.ac.ke;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name erp.mut.ac.ke;
    
    ssl_certificate /etc/letsencrypt/live/erp.mut.ac.ke/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/erp.mut.ac.ke/privkey.pem;
    
    client_max_body_size 100M;
    
    location /static/ {
        alias /home/mutadmin/university-erp/staticfiles/;
        expires 30d;
    }
    
    location /media/ {
        alias /home/mutadmin/university-erp/media/;
        expires 30d;
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