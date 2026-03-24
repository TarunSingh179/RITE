# RITE - College Management System

**RADHAKRISHNA INSTITUTE OF TECHNOLOGY AND ENGINEERING, KHORDHA, ODISHA**

A comprehensive web-based college management system built with Flask, featuring user management, course management, assignment handling, library management, and more. Optimized for PostgreSQL to handle 1000+ students efficiently.

## 🚀 Features

### 🔐 Authentication & User Management
- **Multi-role authentication**: Admin, Faculty, and Student roles
- **Secure login/logout system** with Flask-Login
- **User registration and management** by administrators
- **Role-based access control** with proper authorization

### 👨‍💼 Admin Features
- **Dashboard** with system statistics
- **User management** with CRUD operations
- **User registration** for new students and faculty
- **User status toggle** (activate/deactivate)
- **User deletion** with confirmation dialogs
- **Comprehensive user search and filtering**

### 👨‍🏫 Faculty Features
- **Faculty dashboard** with teaching statistics
- **Assignment management**:
  - Create new assignments
  - Edit existing assignments
  - Delete assignments
  - View assignment submissions
  - Set due dates and maximum marks
  - Upload assignment files
- **Subject management** for assigned courses
- **Student submission tracking**

### 👨‍🎓 Student Features
- **Student dashboard** with personalized information
- **Assignment viewing and submission**
- **Fee management** with payment tracking
- **Library book issuance**
- **Course and semester information**

### 📚 Library Management
- **Book catalog** with search functionality
- **Book issuance system** for students
- **Due date tracking**
- **Available copies management**

### 🎓 Course Management
- **Course creation and management**
- **Semester organization**
- **Subject assignment to faculty**
- **Student enrollment tracking**

### 💰 Fee Management
- **Fee structure** for different fee types
- **Payment tracking** with transaction IDs
- **Receipt generation**
- **Payment status monitoring**

### 📅 Events Management
- **Event creation and management**
- **Event categorization**
- **Featured events highlighting**
- **Event date tracking**

## 🛠️ Technical Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM (SQLite for development)
- **Authentication**: Flask-Login
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Icons**: Font Awesome
- **File Upload**: Werkzeug secure file handling
- **Performance**: Connection pooling, database indexing, query optimization

## 📦 Installation

### Development Setup (SQLite)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd college-management-system
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   ```bash
   python init_db.py
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Open your browser and go to `http://localhost:5000`

### Production Setup (PostgreSQL)

For production deployment with PostgreSQL, see the [Migration Guide](MIGRATION_GUIDE.md) for detailed instructions.

**Quick Setup:**
```bash
# 1. Install PostgreSQL
# 2. Create database and user
# 3. Set environment variables
cp env.example .env
# Edit .env with your PostgreSQL credentials

# 4. Create tables and migrate data
python app.py
python migrate_to_postgresql.py
python performance_optimization.py

# 5. Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 🔑 Default Login Credentials

After running `init_db.py`, the following users are created:

### Admin User
- **Username**: `admin`
- **Password**: `admin123`
- **Access**: Full system administration

### Faculty User
- **Username**: `faculty`
- **Password**: `faculty123`
- **Access**: Faculty dashboard and assignment management

### Student User
- **Username**: `student`
- **Password**: `student123`
- **Access**: Student dashboard and course materials

## 🎯 Key Fixes Implemented

### ✅ Authentication Issues
- Fixed Flask-Login dependency issues
- Proper user session management
- Role-based access control implementation

### ✅ Admin Delete Functionality
- Added proper delete user routes (`/admin/users/<id>/delete`)
- Added user status toggle functionality (`/admin/users/<id>/toggle_status`)
- Implemented confirmation dialogs for destructive actions
- Added proper error handling for user deletion

### ✅ Faculty Login & Assignment Management
- Fixed faculty authentication and dashboard access
- Created comprehensive assignment management system
- Added assignment creation, editing, and deletion
- Implemented file upload for assignments
- Added submission tracking for faculty

### ✅ Missing Routes & Templates
- Created `faculty/assignments.html` template
- Created `faculty/create_assignment.html` template
- Created `faculty/edit_assignment.html` template
- Added proper routing for all faculty functions
- Created error templates (404, 500)

### ✅ Database & Data Management
- Enhanced database initialization with sample data
- Added sample faculty and student users
- Created proper relationships between models
- Added sample courses, subjects, and fees

### ✅ UI/UX Improvements
- Modern Bootstrap 5 interface
- Responsive design for all screen sizes
- Interactive confirmation dialogs
- Real-time filtering and search functionality
- Professional error pages

### ✅ Security & Notification Enhancements
- Two-Factor Authentication (2FA) for admin logins: After entering the correct password, admins receive a one-time code by email and must enter it to complete login.
- Email notification system: Users receive email alerts for important events (e.g., account unlock, fee due, etc.)

## 📁 Project Structure

```
college-management-system/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── init_db.py            # Database initialization
├── requirements.txt      # Python dependencies
├── README.md            # Project documentation
├── models/              # Database models
│   ├── __init__.py
│   ├── user.py         # User model
│   ├── course.py       # Course, Semester, Subject models
│   ├── assignment.py   # Assignment models
│   ├── library.py      # Book models
│   ├── event.py        # Event model
│   ├── fee.py          # Fee model
│   └── result.py       # Result model
└── templates/           # HTML templates
    ├── base.html       # Base template
    ├── index.html      # Homepage
    ├── login.html      # Login page
    ├── admin/          # Admin templates
    ├── faculty/        # Faculty templates
    ├── student/        # Student templates
    └── errors/         # Error pages
```

## 🔧 Configuration

The application uses the following configuration (in `config.py`):

- **Database**: SQLite (`college.db`)
- **Secret Key**: Environment variable or default
- **File Upload**: 16MB max, supported formats: PDF, DOC, DOCX, TXT
- **Session Lifetime**: 24 hours

## 🚀 Usage Guide

### For Administrators
1. Login with admin credentials
2. Access admin dashboard to view system statistics
3. Manage users through the "Manage Users" section
4. Register new students and faculty members
5. Monitor system activities

### For Faculty
1. Login with faculty credentials
2. Access faculty dashboard to view teaching statistics
3. Create and manage assignments
4. Track student submissions
5. Manage course materials

### For Students
1. Login with student credentials
2. Access student dashboard to view assignments and fees
3. Submit assignments before due dates
4. Pay fees through the payment system
5. Issue books from the library

## 🛡️ Security Features

- **Password hashing** using Werkzeug security
- **Session management** with Flask-Login
- **Role-based access control**
- **Secure file uploads** with validation
- **CSRF protection** with Flask-WTF
- **Input validation** and sanitization

## 🔄 Database Schema

The system includes the following main entities:

- **Users**: Admin, Faculty, and Student accounts
- **Courses**: Academic programs with semesters
- **Subjects**: Course subjects assigned to faculty
- **Assignments**: Academic assignments with submissions
- **Books**: Library catalog with issuance tracking
- **Events**: College events and activities
- **Fees**: Student fee management
- **Results**: Academic results tracking

## 🐛 Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Install dependencies with `pip install -r requirements.txt`
2. **Database errors**: Run `python init_db.py` to initialize the database
3. **Login issues**: Verify credentials and user status in admin panel
4. **File upload errors**: Check file size and format restrictions

### Development

- **Debug mode**: Set `debug=True` in `app.py`
- **Database reset**: Delete `college.db` and run `init_db.py`
- **Logs**: Check console output for error messages

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 📞 Support

For support and questions, please contact the development team or create an issue in the repository.

---

**Note**: This is a comprehensive college management system with all major features working perfectly. The system is production-ready with proper security measures, error handling, and user-friendly interfaces.