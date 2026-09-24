# AllYourHelp

AllYourHelp is a Flask-based service marketplace that connects customers with professionals across different service categories. Customers can discover services, find professionals, book appointments, manage bookings, leave reviews, and receive notifications. Professionals can manage their profiles, services, availability, appointments, and earnings. Administrators can monitor and manage the platform through an admin dashboard.

## Features

### Customer features
- User registration and login
- Email verification and resend verification
- Password reset
- Customer dashboard
- Browse service categories and services
- Search and filtering
- View available professionals
- Professional profiles
- Favorites
- Book appointments
- View appointment details and history
- Cancel bookings
- Refund/test refund flow
- Reviews and ratings
- Notifications
- Email notifications
- User profile management
- Show/hide password fields

### Professional features
- Professional registration and profile
- Service request management
- Add/manage offered services
- Professional availability management
- Availability calendar
- Appointment management
- Booking conflict prevention
- Customer appointment details
- Earnings and payment history
- Notifications and email notifications
- Professional performance information

### Admin features
- Admin dashboard
- Booking overview
- Revenue overview
- Analytics
- Booking/revenue charts
- Reports
- Professional performance details
- User and platform monitoring

## Technology Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript, Jinja2
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Migrations:** Flask-Migrate / Alembic
- **Authentication:** Flask-Login
- **Email:** Flask-Mail
- **Environment configuration:** python-dotenv
- **Database driver:** psycopg2-binary

## Project Structure

```text
AllYourHelp/
├── app/
│   ├── models/
│   ├── routes/
│   ├── static/
│   ├── templates/
│   ├── utils/
│   ├── config.py
│   ├── extensions.py
│   ├── seed.py
│   └── __init__.py
├── migrations/
├── .gitignore
├── requirements.txt
└── run.py
```

## Requirements

Make sure the following are installed:

- Python 3.x
- PostgreSQL
- Git

A Python virtual environment is recommended.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Ajaybabu05/AllYourHelp.git
cd AllYourHelp
```

### 2. Create and activate a virtual environment

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

On macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root.

Do **not** commit this file to GitHub because it contains sensitive configuration.

The application expects configuration such as:

```env
SECRET_KEY=your-secret-key
DATABASE_URL=your-postgresql-connection-string

MAIL_SERVER=your-smtp-server
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your-email
MAIL_PASSWORD=your-email-password-or-app-password
MAIL_DEFAULT_SENDER=your-email
```

Use your own PostgreSQL database and SMTP credentials.

## Database Setup

Make sure PostgreSQL is running and the database specified by `DATABASE_URL` exists.

Apply the existing migrations with:

```bash
flask db upgrade
```

If you need to create a new migration after changing the models:

```bash
flask db migrate -m "Describe the database change"
flask db upgrade
```

The project also contains a seed script for development/test data:

```bash
python -m app.seed
```

## Running the Application

Start the Flask development server with:

```bash
python run.py
```

The application will normally be available at:

```text
http://127.0.0.1:5000
```

## Application Roles

AllYourHelp currently supports three main roles:

| Role | Purpose |
|---|---|
| Customer/User | Searches for services and professionals and makes bookings |
| Professional | Offers services and manages availability, appointments, and earnings |
| Admin | Monitors and manages the platform through the admin dashboard |

## Email Verification

New accounts use email verification before login is allowed.

The application sends verification emails using the configured SMTP server. Verification links are time-limited, and users can request a new verification email when necessary.

## Database Migrations

Database schema changes are managed through Flask-Migrate and Alembic.

Migration files are stored in the `migrations/` directory and should be committed to version control.

## Git Workflow

After making changes locally:

```bash
git add .
git commit -m "Describe your changes"
git push
```

If Git is not available directly in your Windows PATH, the Git executable can be invoked using:

```text
C:\Program Files\Git\cmd\git.exe
```

## Security Notes

- Keep `.env` out of version control.
- Never place database passwords, SMTP passwords, API keys, or other secrets directly in source code.
- Use strong values for `SECRET_KEY`.
- Use separate credentials for development and production.
- Review production security settings before deployment.

## Development Status

AllYourHelp is under active development. Core marketplace functionality, authentication, bookings, availability, notifications, reviews, favorites, professional earnings, email verification, and administration features are implemented.

Future work includes production hardening, improved error handling, security improvements, responsive UI polishing, deployment preparation, and automated testing.

## License

A project license has not yet been specified.
