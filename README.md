# Flood Warning System

A Django-based real-time flood early warning and crowdsourced reporting system for Nairobi, Kenya. Features automatic geolocation, email notifications, admin dashboard, and interactive flood risk mapping.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.2-darkgreen)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

### Core Functionality
- **Automatic Geolocation** - Users submit flood reports with GPS coordinates captured automatically
- **Real-time Risk Mapping** - Interactive map showing ward-level flood risk (High/Medium/Low)
- **Crowdsourced Reports** - Residents can upload photos and detailed descriptions
- **Email Notifications** - Automated emails for report confirmations, validations, and alerts
- **Admin Dashboard** - Authority users can validate/reject reports with custom notes
- **Historical Analysis** - 10-year flood history with climate patterns and vulnerability data

### Technical Features
- **Responsive Design** - Works seamlessly on desktop, tablet, and mobile
- **Real-time Filters** - Filter wards by risk level on interactive map
- **User Location Tracking** - Shows user's current location on dashboard
- **Report Status Tracking** - Users can check their report status anytime
- **API Endpoints** - JSON APIs for ward data and historical flood statistics
- **Secure Authentication** - Role-based access (Resident/Authority)

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Django 5.2.8 |
| **Database** | PostgreSQL 16 |
| **Frontend** | Bootstrap 5, Leaflet.js |
| **Email** | Resend API |
| **Maps** | OpenStreetMap, Leaflet |
| **Geolocation** | Browser Geolocation API |
| **Python** | 3.12+ |

## Prerequisites

- Python 3.12 or higher
- PostgreSQL 14 or higher
- Git
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Resend account (free at https://resend.com)

## Installation & Setup

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/flood-warning-system.git
cd flood-project-new
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

```bash
# Create .env file
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux
```

Edit `.env` with your configuration:

```dotenv
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=flood_warning_db
DB_USER=flood_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Email (Resend)
EMAIL_BACKEND=core.email_backends.ResendEmailBackend
RESEND_API_KEY=re_your_api_key_here
DEFAULT_FROM_EMAIL=Flood Warning System <noreply@yourdomain.com>
SERVER_EMAIL=noreply@yourdomain.com

# Site
SITE_URL=http://localhost:8000
SITE_NAME=Flood Warning System
```

### 5. Set Up PostgreSQL Database

```bash
# Create database
createdb flood_warning_db

# Create user
createuser flood_user

# Set password (in PostgreSQL console)
ALTER USER flood_user WITH PASSWORD 'your_password';
ALTER ROLE flood_user CREATEDB;
```

### 6. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser Account

```bash
python manage.py createsuperuser
```

Follow prompts to create admin account.

### 8. Run Development Server

```bash
python manage.py runserver
```

Visit: http://localhost:8000

## 📖 Usage Guide

### For Residents

1. **Sign Up** - Create account at http://localhost:8000/signup/
2. **View Map** - Check flood risk levels in your area
3. **Submit Report** - Click "Submit Report" to:
   - Allow geolocation (automatic)
   - Add location description
   - Describe flood situation
   - Upload photo (optional)
4. **Track Report** - Check report status in your dashboard
5. **Receive Alerts** - Get email updates when your report is reviewed

### For Authorities

1. **Login** - Use admin credentials
2. **Access Dashboard** - Click "Admin Dashboard"
3. **Review Reports** - See pending flood reports
4. **Validate/Reject** - Open modal and:
   - Review report details
   - Add admin notes (optional)
   - Click Validate or Reject
5. **Send Alerts** - Use management commands to notify residents

## API Endpoints

### Public API (Authenticated Users)

**Get Ward Data**
```
GET /api/ward-data/
```
Returns GeoJSON with all wards and current risk levels.

**Get Historical Flood Data**
```
GET /api/historical-flood-data/
```
Returns historical flood statistics by ward.

### Example Request

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/ward-data/
```

## Management Commands

### Test Email Configuration

```bash
python manage.py test_email_complete your-email@example.com
```

Sends test emails to verify Resend configuration.

### Send Flood Alerts

```bash
# Send alert for all high-risk wards
python manage.py send_alert --risk-level High

# Send alert for specific ward
python manage.py send_alert --ward 1 --risk-level High

# Custom message
python manage.py send_alert --ward 1 --risk-level High --message "Heavy rainfall expected"
```

### Send Daily Summary

```bash
python manage.py send_daily_summary
```

Sends daily report summary to all authorities.

## Email Configuration

### Using Resend

1. Sign up at https://resend.com (free tier available)
2. Verify your domain (or use onboarding domain)
3. Create API key
4. Add to `.env`:
   ```
   RESEND_API_KEY=re_your_key_here
   DEFAULT_FROM_EMAIL=Flood Warning System <noreply@yourdomain.com>
   ```

### Email Types

| Email | Trigger | Recipient |
|-------|---------|-----------|
| Report Confirmation | User submits report | Reporter |
| Report Validated | Admin validates report | Reporter |
| Report Rejected | Admin rejects report | Reporter + reason |
| New Report Alert | Report submitted | All authorities |
| Daily Summary | Scheduled (daily) | All authorities |
| Flood Alert | Manual send | All users |

## Project Structure

```
flood-project-new/
├── core/                          # Main Django app
│   ├── models.py                 # Database models
│   ├── views.py                  # View functions
│   ├── urls.py                   # URL routing
│   ├── forms.py                  # Django forms
│   ├── decorators.py             # Custom decorators
│   ├── admin.py                  # Django admin
│   ├── apps.py                   # App config
│   ├── services/
│   │   ├── email_service.py      # Email functionality
│   │   └── __init__.py
│   ├── email_backends.py         # Resend backend
│   ├── management/
│   │   └── commands/             # Custom commands
│   │       ├── test_email.py
│   │       ├── test_email_complete.py
│   │       ├── send_alert.py
│   │       └── send_daily_summary.py
│   ├── migrations/               # Database migrations
│   └── templates/core/           # HTML templates
│       ├── submit_report.html
│       ├── authority_dashboard.html
│       ├── report_status.html
│       ├── dashboard.html
│       └── ...
├── flood_warning_system/         # Project settings
│   ├── settings.py              # Django settings
│   ├── urls.py                  # Main URL config
│   ├── wsgi.py                  # WSGI config
│   └── asgi.py                  # ASGI config
├── templates/                    # Base templates
│   ├── base.html
│   ├── home.html
│   ├── login.html
│   ├── signup.html
│   └── ...
├── static/                       # CSS, JS, images
│   ├── css/
│   ├── js/
│   └── images/
├── media/                        # User uploaded files
├── logs/                         # Application logs
├── .env                          # Environment variables
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
├── manage.py                     # Django CLI
└── README.md                     # This file
```

## Database Models

### Core Models

**CustomUser**
- Extends Django User
- Fields: role (resident/authority), phone_number, subscribed_wards

**Ward**
- Nairobi administrative division
- Fields: name, geom_json, current_risk_level, population, critical_infrastructure

**CrowdReport**
- User-submitted flood reports
- Fields: location, description, photo, latitude, longitude, status, upvotes/downvotes

**ReportAction**
- Admin actions on reports
- Fields: report, action (validate/reject), admin user, notes

**HistoricalFloodEvent**
- Past flood events (2015-2025)
- Fields: name, date, affected_wards, casualties, damage, risk_level

**WeatherDataLake**
- Raw weather data from multiple sources
- Fields: ward, source, rainfall, temperature, humidity, soil_moisture

## Security Features

- **Django CSRF Protection** - All forms protected
- **Authentication Required** - Most pages require login
- **Role-based Access** - Authority functions restricted
- **Environment Variables** - Secrets not in code
- **SQL Injection Prevention** - ORM queries parameterized
- **XSS Protection** - Django template escaping

## Troubleshooting

### Database Connection Error
```bash
# Check PostgreSQL is running
# Verify credentials in .env
# Test connection:
psql -h localhost -U flood_user -d flood_warning_db
```

### Email Not Sending
```bash
# Test configuration
python manage.py test_email_complete your-email@example.com

# Check Resend API key
# Verify sender email is verified in Resend
# Check logs for errors
```

### Geolocation Not Working
- Browser must request permission
- User must be on HTTPS (or localhost)
- Check browser console for errors
- Some browsers block geolocation in private mode

### Migration Issues
```bash
# Show migration status
python manage.py showmigrations

# Rollback to previous state
python manage.py migrate core <migration_name>

# Create new migration
python manage.py makemigrations
```

## Data Models

### Risk Levels
- **High Risk**: >70% probability of flooding
- **Medium Risk**: 40-70% probability
- **Low Risk**: <40% probability

### Report Status
- **Pending** - Awaiting admin review
- **Validated** - Approved and active
- **Rejected** - Did not meet criteria

## Deployment

### Production Checklist

```bash
# Set DEBUG to False
DEBUG=False

# Generate new SECRET_KEY
python manage.py shell
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Use production server (Gunicorn)
pip install gunicorn
gunicorn flood_warning_system.wsgi --bind 0.0.0.0:8000
```

### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "flood_warning_system.wsgi", "--bind", "0.0.0.0:8000"]
```

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -m 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Open Pull Request

## Contact & Support

- **Issues**: https://github.com/YOUR_USERNAME/flood-warning-system/issues
- **Email**: deborahndege19@gmail.com

## Acknowledgments

- Nairobi County Government for flood data
- Kenya Meteorological Department
- OpenStreetMap contributors
- Django & Python communities

---

**Last Updated**: December 2025  
**Status**: Active Development