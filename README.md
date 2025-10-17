# 🏦 Chama Smart - Digital Table Banking System

[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

A professional, production-ready Django application for managing Chama (Merry-Go-Round/Table Banking) groups in Kenya and East Africa. Built with security, scalability, and modern financial management practices in mind.

## 🎯 Key Features

### 💰 **Financial Management**
- **Contribution Tracking**: Automated cycle-based contribution collection
- **Merry-Go-Round Rotation**: Smart payout queue management
- **Loan Management**: Member loans with interest calculation and guarantors
- **Payment Integration**: M-Pesa, Bank Transfers, Cash, and Card payments
- **Late Payment Penalties**: Automatic calculation and tracking
- **Financial Reports**: Comprehensive analytics and export capabilities

### 👥 **Member Management**
- **Multi-Role System**: Admin, Treasurer, Secretary, and Member roles
- **KYC Compliance**: National ID verification and profile management
- **Membership Tracking**: Position in rotation, contribution history
- **Two-Factor Authentication**: Enhanced security for sensitive operations

### 📊 **Meetings & Governance**
- **Meeting Scheduling**: Automated reminders and calendar integration
- **Attendance Tracking**: Real-time attendance monitoring
- **Minutes Recording**: Digital meeting minutes and agenda management
- **Member Voting**: Decision tracking and member consensus

### 🔔 **Communication**
- **Multi-Channel Notifications**: SMS, Email, Push, and In-App
- **Automated Reminders**: Contribution deadlines, meeting alerts
- **Transaction Updates**: Real-time payment confirmations
- **Custom Alerts**: Configurable notification preferences

### 🔐 **Security & Compliance**
- **Audit Trail**: Complete activity logging for compliance
- **Role-Based Access Control**: Granular permissions management
- **Data Encryption**: Secure sensitive information storage
- **Banking Integration**: Secure API connections with financial institutions

---

## 🚀 Quick Start

### Prerequisites

```bash
# System Requirements
Python 3.10+
PostgreSQL 13+ (or SQLite for development)
Redis (optional, for caching)
```

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/chama-smart.git
cd chama-smart
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
```bash
# Create .env file
cp .env.example .env

# Edit .env with your settings
nano .env
```

5. **Database Setup**
```bash
# Run migrations
python manage.py makemigrations main_application
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

6. **Run Development Server**
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/admin/` to access the admin panel.

---

## 📁 Project Structure

```
chama-smart/
├── main_application/
│   ├── models.py           # Database models
│   ├── admin.py            # Admin interface configuration
│   ├── views.py            # API views and logic
│   ├── serializers.py      # DRF serializers
│   ├── urls.py             # URL routing
│   ├── signals.py          # Django signals
│   ├── permissions.py      # Custom permissions
│   ├── utils.py            # Utility functions
│   ├── tasks.py            # Celery tasks (async)
│   └── migrations/         # Database migrations
├── config/
│   ├── settings.py         # Django settings
│   ├── urls.py             # Main URL configuration
│   └── wsgi.py             # WSGI configuration
├── static/                 # Static files (CSS, JS, images)
├── media/                  # User uploads
├── templates/              # HTML templates
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── manage.py              # Django management script
└── README.md              # This file
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=chama_smart_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# M-Pesa Daraja API
MPESA_ENVIRONMENT=sandbox  # or production
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_SHORTCODE=your_paybill_number
MPESA_PASSKEY=your_passkey
MPESA_INITIATOR_NAME=your_initiator_name
MPESA_SECURITY_CREDENTIAL=your_credential

# SMS Configuration (Africa's Talking)
AT_USERNAME=your_username
AT_API_KEY=your_api_key
AT_SENDER_ID=CHAMASMART

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Redis (for caching and Celery)
REDIS_URL=redis://localhost:6379/0

# Security
SECURE_SSL_REDIRECT=False  # Set True in production
SESSION_COOKIE_SECURE=False  # Set True in production
CSRF_COOKIE_SECURE=False  # Set True in production
```

---

## 📦 Dependencies

### Core Requirements

```txt
# requirements.txt
Django==4.2.7
djangorestframework==3.14.0
psycopg2-binary==2.9.9
python-decouple==3.8
Pillow==10.1.0
django-cors-headers==4.3.1

# Payment Integration
requests==2.31.0
python-mpesa==1.2.0

# SMS
africastalking==1.2.5

# Task Queue
celery==5.3.4
redis==5.0.1

# API Documentation
drf-yasg==1.21.7

# Security
django-ratelimit==4.1.0
django-axes==6.1.1

# Monitoring
sentry-sdk==1.39.1

# Testing
pytest==7.4.3
pytest-django==4.7.0
factory-boy==3.3.0
faker==20.1.0
```

---

## 🎨 Admin Interface

The admin panel (`/admin/`) provides a comprehensive interface for managing:

### Dashboard Features
- **Chama Overview**: Active groups, total contributions, member statistics
- **Financial Summary**: Real-time financial metrics and reports
- **Member Management**: User profiles, roles, and verification status
- **Contribution Tracking**: Cycle progress, payment status
- **Loan Management**: Application approval, repayment tracking
- **Meeting Management**: Schedule, attendance, minutes
- **Notification Center**: Send bulk messages, view notification history
- **Aud