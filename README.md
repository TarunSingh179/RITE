# RITE College Management System 🏫

A comprehensive, monolithic web application built with Python and Flask specifically designed to serve as the digital backbone for Radhakrishna Institute of Technology and Engineering (RITE). It provides distinct dashboards and functional endpoints for Admins, Faculty, and Students to manage the full academic lifecycle.

## 🚀 Core Modules & Features

- **Multi-Role Authentication:** Specialized access control using `flask_login` separating Admin (management), Faculty (teaching), and Students (learning).
- **Academic Administration (Admin):**
  - **User Management:** Register, edit, soft-delete, and toggle the status of students and staff.
  - **Financial Management:** Track fee statuses, generate invoices, and export fee reports to CSV/Excel.
  - **Global Dashboard:** View live metrics of total members, active attendance, exams, and pending feedback.
- **Faculty Operations:**
  - **Attendance Tracking:** Mark student attendance per subject and generate detailed date-range reports.
  - **Assignment & Exams:** Create assignments (file uploads), grade submissions, and manage exam schedules.
- **Student Portal:**
  - View enrolled courses, track personal attendance percentages, submit assignments digitally, and access library books.
- **Global Search Engine:** A unified search bar capable of querying Users, Courses, Subjects, and Books seamlessly.

## 💻 Tech Stack

- **Framework:** Python / Flask
- **Database:** Relational Database via SQLAlchemy ORM (SQLite/PostgreSQL)
- **Security:** `werkzeug.security` (Password Hashing)
- **Frontend Templates:** HTML5 / Jinja2 / Bootstrap (via `render_template`)
- **Other Utilities:** Standard Python `csv` & `io` for data exports, `smtplib` for SMTP email messaging (Notifications/Forgot Password).

## 📁 Key File Structure

- `app.py`: The massive core application router (~2400 lines) handling 90+ distinct endpoints across all user roles.
- `models/`: Contains the SQLAlchemy schema definitions (`user.py`, `course.py`, `attendance.py`, `fee.py`, etc.).
- `static/uploads/`: Dedicated directories for securely storing assignments, documents, profiles, books, and event photos.
- `templates/`: Jinja2 templates organized by role (`admin/`, `faculty/`, `student/`).

## 🛠️ Local Development

1. **Virtual Environment & Dependencies:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration:**

   Ensure a `.env` file exists defining standard keys like `SECRET_KEY`, `FLASK_ENV`, and `DATABASE_URI`.

3. **Run Application:**

   ```bash
   flask run
   ```

   *The application typically runs locally on port 5000.*