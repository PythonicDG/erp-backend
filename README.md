# Project Workflow Management System - Backend

This is the Django backend for the Project Workflow Management System.

## Tech Stack
- **Framework**: Django + Django REST Framework
- **Database**: PostgreSQL
- **Authentication**: Token-based Authentication
- **Environment Management**: python-dotenv

## Setup Instructions

1. **Clone the repository**
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in the details.
   ```bash
   cp .env.example .env
   ```
5. **Database Setup**:
   Ensure PostgreSQL is running and the database specified in `.env` exists.
6. **Migrations**:
   ```bash
   python manage.py migrate
   ```
7. **Run Server**:
   ```bash
   python manage.py runserver
   ```

## API Endpoints
- `admin/`: Django Admin interface
- `api/token/`: Get auth token (POST with username and password)
- `api-auth/`: DRF browsable API login
