# RITE Management System 📚

A comprehensive, all-in-one college management backend application tailored for the Radhakrishna Institute of Technology and Engineering (RITE). Engineered utilizing robust Python/Flask technologies and detailed database blueprints.

## 🚀 Features
- **User Roles & Authorization:** Support for Admins, Faculty, and Students, each with specific role-based access.
- **Audit Logs & Security:** Enhanced tracking for all user interactions, login trails, and secure 2FA/Email Verification.
- **Academic Ecosystem:** Tracks Courses, Events, Assignments, Attendance, Examinations, and Results.
- **Financial Module:** Fully functional fee management logic, online payment gateways, and printable fee receipts.
- **Library Management:** Cataloging, barcode, and QR code integration for tracking physical and digital assets.
- **Communication Hub:** Internal notifications and HTML email alerts for critical events (Fee Due, Fee Overdue).
- **Reporting & Dashboards:** Detailed analytical dashboards for both Admins and Faculty.

## 💻 Tech Stack
- **Framework:** Flask (Python)
- **Database Options:** SQLite (Basic testing) / PostgreSQL (Supported via scripts)
- **ORM Tooling:** SQLAlchemy, Alembic (Migrations)
- **Frontend Layer:** Jinja2 Templating, Vanilla JS (Admin/Frontend split scripts)

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- PosgreSQL / SQLite integration

### Quick Start
1. Ensure you are in the project root directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create your `.env` configuration file by mirroring `env.example`:
   ```bash
   cp env.example .env
   ```
4. Set up the development database:
   ```bash
   python init_db.py
   # OR
   python setup_database.py
   ```
5. Spin up the application engine:
   ```bash
   python app.py
   ```
6. Access the portal locally via:
   ```text
   http://127.0.0.1:5000
   ```

## 📁 Key Directories
- `models/`: Central SQLAlchemy objects governing system domains (users, fees, attendance).
- `templates/`: Categorized UI files mapped structurally via Jinja templates to route actions.
- `static/`: Contains the primary JS utility interactions, favicons, and styles.
- `migrations/`: Holds Alembic logic for transitioning database shapes effortlessly.