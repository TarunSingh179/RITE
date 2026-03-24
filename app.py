from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import os
from datetime import datetime, timedelta, date
import uuid
import smtplib
from email.message import EmailMessage
import ssl
from sqlalchemy import func
from typing import Optional
import json
import io
import csv

from config import Config, config
from models.user import db, User
from models import *
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure app based on environment
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create upload directories
os.makedirs('static/uploads/assignments', exist_ok=True)
os.makedirs('static/uploads/documents', exist_ok=True)
os.makedirs('static/uploads/profiles', exist_ok=True)
os.makedirs('static/uploads/books', exist_ok=True)
os.makedirs('static/uploads/events', exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def is_valid_email(email):
    import re
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def is_strong_password(password):
    # At least 8 chars, 1 uppercase, 1 lowercase, 1 digit
    import re
    return (
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"[0-9]", password)
    )

# Routes
@app.route('/')
def index():
    events = Event.query.filter_by(is_active=True).order_by(Event.event_date.desc()).limit(6).all()
    courses = Course.query.filter_by(is_active=True).all()
    notifications = Notification.query.filter_by(is_active=True, target_role='all').order_by(Notification.created_at.desc()).limit(5).all()
    return render_template('index.html', events=events, courses=courses, notifications=notifications)

# Global search endpoint
@app.route('/search')
@login_required
def global_search():
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 5)), 10)  # hard cap
    if not query:
        return jsonify({
            'users': [], 'courses': [], 'subjects': [], 'books': []
        })

    # Basic LIKE searches; adjust fields per model
    like = f"%{query}%"
    results = {
        'users': [],
        'courses': [],
        'subjects': [],
        'books': []
    }
    try:
        # Users
        users = User.query.filter(
            (User.first_name.ilike(like)) |
            (User.last_name.ilike(like)) |
            (User.email.ilike(like)) |
            (User.username.ilike(like))
        ).order_by(User.id.asc()).limit(limit).all()
        results['users'] = [
            {
                'id': u.id,
                'name': getattr(u, 'get_full_name', lambda: f"{getattr(u,'first_name','')} {getattr(u,'last_name','')}")(),
                'email': getattr(u, 'email', ''),
                'role': getattr(u, 'role', '')
            }
            for u in users
        ]

        # Courses
        courses = Course.query.filter(Course.name.ilike(like)).order_by(Course.id.asc()).limit(limit).all()
        results['courses'] = [
            {'id': c.id, 'name': c.name}
            for c in courses
        ]

        # Subjects
        subjects = Subject.query.filter(Subject.name.ilike(like)).order_by(Subject.id.asc()).limit(limit).all()
        results['subjects'] = [
            {'id': s.id, 'name': s.name}
            for s in subjects
        ]

        # Books
        books = Book.query.filter(
            (Book.title.ilike(like)) | (Book.author.ilike(like)) | (Book.isbn.ilike(like))
        ).order_by(Book.id.asc()).limit(limit).all()
        results['books'] = [
            {'id': b.id, 'title': b.title, 'author': b.author}
            for b in books
        ]
    except Exception as e:
        app.logger.exception('Global search error: %s', e)
        return jsonify({'error': 'Search failed'}), 500

    return jsonify(results)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            flash('Login successful!', 'success')
            if user.is_admin():
                return redirect(url_for('admin_dashboard'))
            elif user.is_faculty():
                return redirect(url_for('faculty_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Admin Routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    total_students = User.query.filter_by(role='student').count()
    total_faculty = User.query.filter_by(role='faculty').count()
    total_courses = Course.query.count()
    total_books = Book.query.count()
    total_attendance = Attendance.query.filter_by(date=date.today()).count()
    total_exams = Exam.query.count()
    pending_feedback = Feedback.query.filter_by(status='pending').count()
    
    # Recent activities
    recent_attendance = Attendance.query.order_by(Attendance.created_at.desc()).limit(5).all()
    recent_exams = Exam.query.order_by(Exam.created_at.desc()).limit(5).all()
    recent_feedback = Feedback.query.order_by(Feedback.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         total_students=total_students,
                         total_faculty=total_faculty,
                         total_courses=total_courses,
                         total_books=total_books,
                         total_attendance=total_attendance,
                         total_exams=total_exams,
                         pending_feedback=pending_feedback,
                         recent_attendance=recent_attendance,
                         recent_exams=recent_exams,
                         recent_feedback=recent_feedback)

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    users = User.query.filter_by(is_active=True).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    app.logger.info('[ADMIN] Delete request for user_id=%s by admin_id=%s', user_id, getattr(current_user, 'id', None))
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    app.logger.info('[ADMIN] Target delete user found id=%s username=%s role=%s active=%s', user.id, user.username, user.role, user.is_active)
    
    if user.id == current_user.id:
        flash('You cannot delete yourself', 'error')
        return redirect(url_for('admin_users'))
    
    # Check for related data
    related = []
    if hasattr(user, 'assignments') and user.assignments:
        related.append('assignments')
    if hasattr(user, 'attendance_records') and user.attendance_records:
        related.append('attendance')
    if hasattr(user, 'exam_marks') and user.exam_marks:
        related.append('exam marks')
    if hasattr(user, 'assignment_submissions') and user.assignment_submissions:
        related.append('assignment submissions')
    # Add more checks as needed for your models
    
    if related:
        # Soft delete
        user.is_active = False
        db.session.commit()
        app.logger.info('[ADMIN] Soft-deactivated user_id=%s due to related=%s', user.id, related)
        flash(f"User has related data ({', '.join(related)}). User was deactivated instead of deleted.", 'warning')
        return redirect(url_for('admin_users'))
    try:
        db.session.delete(user)
        db.session.commit()
        app.logger.info('[ADMIN] Hard-deleted user_id=%s', user_id)
        flash('User deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.exception('[ADMIN] Error deleting user_id=%s: %s', user_id, e)
        flash('Error deleting user. User may have associated data.', 'error')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/toggle_status', methods=['POST'])
@login_required
def admin_toggle_user_status(user_id):
    app.logger.info('[ADMIN] Toggle status request for user_id=%s by admin_id=%s', user_id, getattr(current_user, 'id', None))
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    app.logger.info('[ADMIN] Target toggle user found id=%s username=%s role=%s active=%s', user.id, user.username, user.role, user.is_active)
    
    if user.id == current_user.id:
        flash('You cannot deactivate yourself', 'error')
        return redirect(url_for('admin_users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    app.logger.info('[ADMIN] User id=%s %s', user.id, status)
    flash(f'User {status} successfully.', 'success')
    return redirect(url_for('admin_users'))

# -----------------------------
# Admin: Users - Export & Edit
# -----------------------------
@app.route('/admin/users/export.csv')
@login_required
def export_users_csv():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Username', 'Email', 'Role', 'Active', 'Created'])
    for u in User.query.order_by(User.id.asc()).all():
        writer.writerow([
            u.id,
            getattr(u, 'username', ''),
            getattr(u, 'email', ''),
            getattr(u, 'role', ''),
            'Yes' if getattr(u, 'is_active', False) else 'No',
            u.created_at.strftime('%Y-%m-%d') if getattr(u, 'created_at', None) else ''
        ])
    csv_data = output.getvalue()
    from flask import Response
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=users.csv'}
    )


@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.first_name = request.form.get('first_name', user.first_name)
        user.last_name = request.form.get('last_name', user.last_name)
        new_email = request.form.get('email', user.email)
        new_role = request.form.get('role', user.role)
        if new_email != user.email and User.query.filter_by(email=new_email).first():
            flash('Email already in use', 'error')
            return redirect(url_for('admin_edit_user', user_id=user.id))
        user.email = new_email
        user.role = new_role
        # Role specific updates
        if new_role == 'student':
            user.student_id = user.student_id or f"STU{datetime.now().year}{User.query.filter_by(role='student').count() + 1:04d}"
            user.course_id = request.form.get('course_id') or user.course_id
            user.semester_id = request.form.get('semester_id') or user.semester_id
            # clear faculty-only fields
            user.faculty_id = None
            user.department = None
            user.qualification = None
            user.experience_years = None
        elif new_role == 'faculty':
            user.faculty_id = user.faculty_id or f"FAC{datetime.now().year}{User.query.filter_by(role='faculty').count() + 1:04d}"
            user.department = request.form.get('department') or user.department
            user.qualification = request.form.get('qualification') or user.qualification
            user.experience_years = request.form.get('experience_years') or user.experience_years
            # clear student-only fields
            user.student_id = None
            user.course_id = None
            user.semester_id = None
        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin_users'))
    # GET: provide supporting data
    courses = Course.query.all()
    semesters = Semester.query.all()
    return render_template('admin/edit_user.html', user=user, courses=courses, semesters=semesters)

@app.route('/admin/register', methods=['GET', 'POST'])
@login_required
def admin_register():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('admin_register'))
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('admin_register'))
        if not is_valid_email(email):
            flash('Invalid email format', 'error')
            return redirect(url_for('admin_register'))
        if not is_strong_password(password):
            flash('Password must be at least 8 characters, include uppercase, lowercase, and a digit.', 'error')
            return redirect(url_for('admin_register'))
        user = User(
            username=username,
            email=email,
            role=role,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        if role == 'student':
            user.student_id = f"STU{datetime.now().year}{User.query.filter_by(role='student').count() + 1:04d}"
            user.course_id = request.form.get('course_id')
            user.semester_id = request.form.get('semester_id')
        elif role == 'faculty':
            user.faculty_id = f"FAC{datetime.now().year}{User.query.filter_by(role='faculty').count() + 1:04d}"
            user.department = request.form.get('department')
            user.qualification = request.form.get('qualification')
        try:
            db.session.add(user)
            db.session.commit()
            flash('User registered successfully', 'success')
        except Exception as e:
            db.session.rollback()
            if 'UNIQUE constraint failed: user.email' in str(e):
                flash('Email already exists', 'error')
            else:
                flash('Error registering user', 'error')
        return redirect(url_for('admin_users'))
    courses = Course.query.all()
    semesters = Semester.query.all()
    return render_template('admin/register.html', courses=courses, semesters=semesters)

 

@app.route('/admin/export/fees.csv')
@login_required
def export_fees_csv():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    import csv
    import io
    from flask import make_response
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Student Name', 'Student Email', 'Fee Type', 'Amount', 'Due Date', 'Status', 'Paid Date', 'Created At'])
    
    # Write fee data
    fees = Fee.query.join(User).all()
    for fee in fees:
        paid_date = fee.paid_date.strftime('%Y-%m-%d') if fee.paid_date else 'Not Paid'
        
        writer.writerow([
            fee.id,
            f"{fee.student.first_name} {fee.student.last_name}",
            fee.student.email,
            fee.fee_type,
            fee.amount,
            fee.due_date.strftime('%Y-%m-%d'),
            fee.status,
            paid_date,
            fee.created_at.strftime('%Y-%m-%d %H:%M:%S') if fee.created_at else 'N/A'
        ])
    
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=fees_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

@app.route('/admin/export/fees.xlsx')
@login_required
def export_fees_xlsx():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))

    try:
        from openpyxl import Workbook
    except Exception:
        flash('Excel export requires openpyxl. Please install it.', 'error')
        return redirect(url_for('admin_fees'))

    wb = Workbook()
    ws = wb.active
    ws.title = 'Fees'
    headers = ['ID', 'Student Name', 'Student Email', 'Fee Type', 'Amount', 'Paid Amount', 'Balance', 'Due Date', 'Status', 'Paid Date', 'Receipt No', 'Created At']
    ws.append(headers)
    fees = Fee.query.join(User).all()
    for f in fees:
        paid_date = f.paid_date.strftime('%Y-%m-%d %H:%M') if f.paid_date else ''
        balance = (f.amount or 0) - (f.paid_amount or 0)
        ws.append([
            f.id,
            f"{f.student.first_name} {f.student.last_name}",
            f.student.email,
            f.fee_type,
            f.amount,
            f.paid_amount or 0,
            round(balance, 2),
            f.due_date.strftime('%Y-%m-%d'),
            f.status,
            paid_date,
            f.receipt_number or '',
            f.created_at.strftime('%Y-%m-%d %H:%M:%S') if f.created_at else ''
        ])

    from io import BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    from flask import send_file
    return send_file(output, as_attachment=True, download_name=f'fees_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/admin/export/attendance.csv')
@login_required
def export_attendance_csv():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    import csv
    import io
    from flask import make_response
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Student Name', 'Student Email', 'Subject', 'Date', 'Status', 'Marked By', 'Created At'])
    
    # Write attendance data
    attendance_records = Attendance.query.join(User, Attendance.student_id == User.id).join(Subject).all()
    for record in attendance_records:
        marked_by_name = f"{record.faculty.first_name} {record.faculty.last_name}" if record.faculty else 'N/A'
        
        writer.writerow([
            record.id,
            f"{record.student.first_name} {record.student.last_name}",
            record.student.email,
            record.subject.name,
            record.date.strftime('%Y-%m-%d'),
            record.status.title(),
            marked_by_name,
            record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else 'N/A'
        ])
    
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=attendance_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

# Attendance Management Routes
@app.route('/admin/attendance')
@login_required
def admin_attendance():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    attendance_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    attendance_records = Attendance.query.filter_by(date=datetime.strptime(attendance_date, '%Y-%m-%d').date()).all()
    subjects = Subject.query.all()
    
    return render_template('admin/attendance.html', 
                         attendance_records=attendance_records, 
                         subjects=subjects, 
                         attendance_date=attendance_date)

@app.route('/admin/attendance/report')
@login_required
def admin_attendance_report():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    subject_id = request.args.get('subject_id')
    start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', date.today().strftime('%Y-%m-%d'))
    
    query = Attendance.query
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    query = query.filter(Attendance.date.between(start_date, end_date))
    
    attendance_records = query.all()
    subjects = Subject.query.all()
    
    return render_template('admin/attendance_report.html', 
                         attendance_records=attendance_records,
                         subjects=subjects,
                         selected_subject=subject_id,
                         start_date=start_date,
                         end_date=end_date)

# Faculty Routes
@app.route('/faculty/dashboard')
@login_required
def faculty_dashboard():
    if not current_user.is_faculty():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    subjects = Subject.query.filter_by(faculty_id=current_user.id).all()
    assignments = Assignment.query.filter_by(faculty_id=current_user.id).order_by(Assignment.created_at.desc()).limit(5).all()
    exams = Exam.query.join(Subject).filter(Subject.faculty_id == current_user.id).order_by(Exam.created_at.desc()).limit(5).all()
    
    # Today's attendance stats
    today_attendance = Attendance.query.join(Subject).filter(
        Subject.faculty_id == current_user.id,
        Attendance.date == date.today()
    ).all()
    
    return render_template('faculty/dashboard.html', 
                         subjects=subjects, 
                         assignments=assignments, 
                         exams=exams,
                         today_attendance=today_attendance,
                         now=datetime.utcnow())

@app.route('/faculty/attendance')
@login_required
def faculty_attendance():
    if not current_user.is_faculty():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    subjects = Subject.query.filter_by(faculty_id=current_user.id).all()
    selected_subject = request.args.get('subject_id')
    attendance_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    
    if selected_subject:
        students = User.query.filter_by(role='student', semester_id=Subject.query.get(selected_subject).semester_id).all()
        attendance_records = Attendance.query.filter_by(
            subject_id=selected_subject, 
            date=datetime.strptime(attendance_date, '%Y-%m-%d').date()
        ).all()
    else:
        students = []
        attendance_records = []
    
    return render_template('faculty/attendance.html',
                         subjects=subjects,
                         students=students,
                         attendance_records=attendance_records,
                         selected_subject=selected_subject,
                         attendance_date=attendance_date)

@app.route('/faculty/attendance/mark', methods=['POST'])
@login_required
def faculty_mark_attendance():
    if not current_user.is_faculty():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    subject_id = request.form['subject_id']
    attendance_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
    
    # Get all students for this semester
    students = User.query.filter_by(role='student', semester_id=Subject.query.get(subject_id).semester_id).all()
    
    # Process each student's attendance status
    for student in students:
        status = request.form.get(f'status_{student.id}', 'absent')
        
        # Check if attendance record already exists for this student, subject, and date
        existing_record = Attendance.query.filter_by(
            student_id=student.id,
            subject_id=subject_id,
            date=attendance_date
        ).first()
        
        if existing_record:
            # Update existing record
            existing_record.status = status
            existing_record.marked_by = current_user.id
            existing_record.created_at = datetime.utcnow()
        else:
            # Create new attendance record
            attendance = Attendance(
                student_id=student.id,
                subject_id=subject_id,
                date=attendance_date,
                status=status,
                marked_by=current_user.id
            )
            db.session.add(attendance)
    
    db.session.commit()
    flash('Attendance marked successfully', 'success')
    return redirect(url_for('faculty_attendance', subject_id=subject_id, date=request.form['date']))

@app.route('/faculty/attendance/report')
@login_required
def faculty_attendance_report():
    if not current_user.is_faculty():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    # Get subjects taught by current faculty
    subjects = Subject.query.filter_by(faculty_id=current_user.id).all()
    selected_subject = request.args.get('subject_id')
    
    # Default to last 30 days
    start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', date.today().strftime('%Y-%m-%d'))
    
    attendance_report = None
    student_attendance_details = []
    
    if selected_subject:
        # Generate attendance report for the selected subject and date range
        subject = Subject.query.get(selected_subject)
        semester_id = subject.semester_id
        
        # Get all attendance records for this subject within the date range
        attendance_records = Attendance.query.filter(
            Attendance.subject_id == selected_subject,
            Attendance.date.between(start_date, end_date)
        ).all()
        
        # Calculate statistics
        total_students = User.query.filter_by(role='student', semester_id=semester_id).count()
        present_count = len([r for r in attendance_records if r.status == 'present'])
        late_count = len([r for r in attendance_records if r.status == 'late'])
        absent_count = len([r for r in attendance_records if r.status == 'absent'])
        
        # Calculate attendance percentage
        total_records = len(attendance_records)
        attendance_percentage = ((present_count + late_count) / total_records * 100) if total_records > 0 else 0
        
        # Create or update AttendanceReport
        attendance_report = AttendanceReport(
            subject_id=selected_subject,
            semester_id=semester_id,
            report_date=date.today(),
            total_students=total_students,
            present_count=present_count,
            late_count=late_count,
            absent_count=absent_count,
            attendance_percentage=attendance_percentage
        )
        
        # Get detailed attendance per student
        students = User.query.filter_by(role='student', semester_id=semester_id).all()
        for student in students:
            student_records = [r for r in attendance_records if r.student_id == student.id]
            total_classes = len(student_records)
            present = len([r for r in student_records if r.status == 'present'])
            late = len([r for r in student_records if r.status == 'late'])
            absent = len([r for r in student_records if r.status == 'absent'])
            percentage = ((present + late) / total_classes * 100) if total_classes > 0 else 0
            
            student_attendance_details.append({
                'student': student,
                'total_classes': total_classes,
                'present_count': present,
                'late_count': late,
                'absent_count': absent,
                'percentage': percentage
            })
    
    return render_template('faculty/attendance_report.html',
                         subjects=subjects,
                         attendance_report=attendance_report,
                         student_attendance_details=student_attendance_details,
                         selected_subject=selected_subject,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/faculty/assignments')
@login_required
def faculty_assignments():
    if not current_user.is_faculty():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    assignments = Assignment.query.filter_by(faculty_id=current_user.id).all()
    return render_template('faculty/assignments.html', assignments=assignments, now=datetime.utcnow())

@app.route('/faculty/assignments/create', methods=['GET', 'POST'])
@login_required
def create_assignment():
    if not current_user.is_faculty():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        subject_id = request.form['subject_id']
        due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%dT%H:%M')
        max_marks = request.form['max_marks']
        
        assignment = Assignment(
            title=title,
            description=description,
            subject_id=subject_id,
            faculty_id=current_user.id,
            due_date=due_date,
            max_marks=max_marks
        )
        
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'assignments', filename))
                assignment.file_path = f"uploads/assignments/{filename}"
        
        db.session.add(assignment)
        db.session.commit()
        flash('Assignment created successfully', 'success')
        return redirect(url_for('faculty_assignments'))
    
    subjects = Subject.query.filter_by(faculty_id=current_user.id).all()
    return render_template('faculty/create_assignment.html', subjects=subjects)

@app.route('/faculty/assignments/<int:assignment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_assignment(assignment_id):
    if not current_user.is_faculty():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    assignment = Assignment.query.get_or_404(assignment_id)
    
    if assignment.faculty_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('faculty_assignments'))
    
    if request.method == 'POST':
        assignment.title = request.form['title']
        assignment.description = request.form['description']
        assignment.subject_id = request.form['subject_id']
        assignment.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%dT%H:%M')
        assignment.max_marks = request.form['max_marks']
        assignment.is_active = 'is_active' in request.form
        
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'assignments', filename))
                assignment.file_path = f"uploads/assignments/{filename}"
        
        db.session.commit()
        flash('Assignment updated successfully', 'success')
        return redirect(url_for('faculty_assignments'))
    
    subjects = Subject.query.filter_by(faculty_id=current_user.id).all()
    return render_template('faculty/edit_assignment.html', assignment=assignment, subjects=subjects)

@app.route('/faculty/assignments/<int:assignment_id>/delete', methods=['POST'])
@login_required
def delete_assignment(assignment_id):
    if not current_user.is_faculty():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    assignment = Assignment.query.get_or_404(assignment_id)
    
    if assignment.faculty_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('faculty_assignments'))
    
    try:
        db.session.delete(assignment)
        db.session.commit()
        flash('Assignment deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting assignment', 'error')
    
    return redirect(url_for('faculty_assignments'))

# Exam Management Routes
@app.route('/faculty/exams')
@login_required
def faculty_exams():
    if not current_user.is_faculty():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    exams = Exam.query.join(Subject).filter(Subject.faculty_id == current_user.id).all()
    return render_template('faculty/exams.html', exams=exams)

@app.route('/faculty/exams/create', methods=['GET', 'POST'])
@login_required
def create_exam():
    if not current_user.is_faculty():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form['name']
        subject_id = request.form['subject_id']
        exam_type = request.form['exam_type']
        total_marks = request.form['total_marks']
        exam_date = datetime.strptime(request.form['exam_date'], '%Y-%m-%d').date()
        duration = request.form.get('duration')
        description = request.form.get('description')
        
        exam = Exam(
            name=name,
            subject_id=subject_id,
            exam_type=exam_type,
            total_marks=total_marks,
            date=exam_date,
            duration=duration,
            description=description
        )
        
        db.session.add(exam)
        db.session.commit()
        flash('Exam created successfully', 'success')
        return redirect(url_for('faculty_exams'))
    
    subjects = Subject.query.filter_by(faculty_id=current_user.id).all()
    return render_template('faculty/create_exam.html', subjects=subjects)

@app.route('/faculty/exams/<int:exam_id>/marks')
@login_required
def exam_marks(exam_id):
    if not current_user.is_faculty():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    exam = Exam.query.get_or_404(exam_id)
    if exam.subject.faculty_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('faculty_exams'))
    
    students = User.query.filter_by(role='student', semester_id=exam.subject.semester_id).all()
    marks = ExamMark.query.filter_by(exam_id=exam_id).all()
    
    return render_template('faculty/exam_marks.html', exam=exam, students=students, marks=marks)

@app.route('/faculty/exams/<int:exam_id>/marks/add', methods=['POST'])
@login_required
def add_exam_marks(exam_id):
    if not current_user.is_faculty():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    exam = Exam.query.get_or_404(exam_id)
    if exam.subject.faculty_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('faculty_exams'))
    
    for key, value in request.form.items():
        if key.startswith('marks_'):
            student_id = key.split('_')[1]
            marks_obtained = float(value) if value else 0
            remarks = request.form.get(f'remarks_{student_id}', '')
            
            # Check if marks already exist
            existing_mark = ExamMark.query.filter_by(exam_id=exam_id, student_id=student_id).first()
            
            if existing_mark:
                existing_mark.marks_obtained = marks_obtained
                existing_mark.remarks = remarks
                existing_mark.graded_by = current_user.id
                existing_mark.graded_at = datetime.utcnow()
            else:
                mark = ExamMark(
                    exam_id=exam_id,
                    student_id=student_id,
                    marks_obtained=marks_obtained,
                    remarks=remarks,
                    graded_by=current_user.id
                )
                db.session.add(mark)
    
    db.session.commit()
    flash('Marks added successfully', 'success')
    return redirect(url_for('exam_marks', exam_id=exam_id))

# Student Routes
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if not current_user.is_student():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    assignments = Assignment.query.join(Subject).filter(Subject.semester_id == current_user.semester_id).all()
    fees = Fee.query.filter_by(student_id=current_user.id).order_by(Fee.due_date.desc()).limit(5).all()
    books = BookIssue.query.filter_by(student_id=current_user.id, status='issued').all()
    
    # Attendance summary
    attendance_records = Attendance.query.filter_by(student_id=current_user.id).all()
    total_classes = len(attendance_records)
    present_classes = len([a for a in attendance_records if a.status == 'present'])
    attendance_percentage = (present_classes / total_classes * 100) if total_classes > 0 else 0
    
    # Recent exams
    recent_exams = Exam.query.join(Subject).filter(Subject.semester_id == current_user.semester_id).order_by(Exam.date.desc()).limit(5).all()
    
    return render_template('student/dashboard.html', 
                         assignments=assignments, 
                         fees=fees, 
                         books=books,
                         attendance_percentage=attendance_percentage,
                         total_classes=total_classes,
                         present_classes=present_classes,
                         recent_exams=recent_exams,
                         now=datetime.utcnow())

@app.route('/student/attendance')
@login_required
def student_attendance():
    if not current_user.is_student():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    # Get filter parameters
    selected_subject = request.args.get('subject_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build query for attendance records
    query = Attendance.query.filter_by(student_id=current_user.id)
    
    if selected_subject:
        query = query.filter_by(subject_id=selected_subject)
    
    if start_date and end_date:
        query = query.filter(Attendance.date.between(start_date, end_date))
    
    attendance_records = query.order_by(Attendance.date.desc()).all()
    subjects = Subject.query.filter_by(semester_id=current_user.semester_id).all()
    
    return render_template('student/attendance.html', 
                         attendance_records=attendance_records,
                         subjects=subjects,
                         selected_subject=selected_subject,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/student/marks')
@login_required
def student_marks():
    if not current_user.is_student():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    exam_marks = ExamMark.query.filter_by(student_id=current_user.id).all()
    subjects = Subject.query.filter_by(semester_id=current_user.semester_id).all()
    
    return render_template('student/marks.html', 
                         exam_marks=exam_marks,
                         subjects=subjects)

@app.route('/student/assignments')
@login_required
def student_assignments():
    if not current_user.is_student():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    assignments = Assignment.query.join(Subject).filter(Subject.semester_id == current_user.semester_id).all()
    return render_template('student/assignments.html', assignments=assignments, now=datetime.utcnow())

@app.route('/student/assignments/<int:assignment_id>/submit', methods=['GET', 'POST'])
@login_required
def submit_assignment(assignment_id):
    if not current_user.is_student():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    assignment = Assignment.query.get_or_404(assignment_id)
    
    if request.method == 'POST':
        submission_text = request.form.get('submission_text')
        
        submission = AssignmentSubmission(
            assignment_id=assignment_id,
            student_id=current_user.id,
            submission_text=submission_text
        )
        
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'assignments', filename))
                submission.submission_file = f"uploads/assignments/{filename}"
        
        submission.is_late = datetime.utcnow() > assignment.due_date
        
        db.session.add(submission)
        db.session.commit()
        flash('Assignment submitted successfully', 'success')
        return redirect(url_for('student_assignments'))
    
    return render_template('student/submit_assignment.html', assignment=assignment, now=datetime.utcnow())

 

@app.route('/student/fees/<int:fee_id>/pay', methods=['GET', 'POST'])
@login_required
def pay_fee(fee_id):
    if not current_user.is_student():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    fee = Fee.query.get_or_404(fee_id)
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        payment_method = request.form['payment_method']
        
        fee.paid_amount += amount
        fee.payment_method = payment_method
        fee.paid_date = datetime.utcnow()
        fee.transaction_id = f"TXN{uuid.uuid4().hex[:8].upper()}"
        fee.receipt_number = f"RCP{uuid.uuid4().hex[:8].upper()}"
        
        if fee.paid_amount >= fee.amount:
            fee.status = 'paid'
        
        db.session.commit()
        flash('Payment processed successfully', 'success')
        return redirect(url_for('student_fees'))
    
    return render_template('student/pay_fee.html', fee=fee)

# Notification Routes
@app.route('/notifications')
@login_required
def notifications():
    # Full notifications page for current user
    items = NotificationRecipient.query.join(Notification).filter(
        NotificationRecipient.user_id == current_user.id,
    ).order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', items=items)

# Notification APIs
@app.route('/api/notifications/unread_count')
@login_required
def api_notifications_unread_count():
    count = NotificationRecipient.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'unread': count})


@app.route('/api/notifications')
@login_required
def api_notifications_list():
    limit = min(int(request.args.get('limit', 20)), 50)
    items = NotificationRecipient.query.join(Notification).filter(
        NotificationRecipient.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(limit).all()
    def to_dict(nr: NotificationRecipient):
        n = nr.notification
        return {
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'priority': n.priority,
            'created_at': n.created_at.isoformat() if n.created_at else None,
            'is_read': nr.is_read
        }
    return jsonify({'items': [to_dict(nr) for nr in items]})


@app.route('/api/notifications/mark_read', methods=['POST'])
@login_required
def api_notifications_mark_read():
    nid = request.json.get('id')
    if not nid:
        return jsonify({'error': 'id required'}), 400
    nr = NotificationRecipient.query.filter_by(user_id=current_user.id, notification_id=nid).first()
    if not nr:
        return jsonify({'error': 'not found'}), 404
    nr.is_read = True
    nr.read_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'status': 'ok'})


@app.route('/api/notifications/mark_all_read', methods=['POST'])
@login_required
def api_notifications_mark_all_read():
    q = NotificationRecipient.query.filter_by(user_id=current_user.id, is_read=False)
    updated = 0
    for nr in q.all():
        nr.is_read = True
        nr.read_at = datetime.utcnow()
        updated += 1
    if updated:
        db.session.commit()
    return jsonify({'status': 'ok', 'updated': updated})


# Simple SMTP email broadcast utility
def send_email_broadcast(subject: str, body: str, recipients: list[str]):
    if not recipients:
        return
    host = os.environ.get('SMTP_HOST')
    port = int(os.environ.get('SMTP_PORT', '587'))
    username = os.environ.get('SMTP_USERNAME')
    password = os.environ.get('SMTP_PASSWORD')
    sender = os.environ.get('SMTP_FROM')
    use_tls = os.environ.get('SMTP_TLS', 'true').lower() == 'true'

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg.set_content(body)

    if use_tls:
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port) as server:
            server.starttls(context=context)
            if username and password:
                server.login(username, password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(host, port) as server:
            if username and password:
                server.login(username, password)
            server.send_message(msg)

@app.route('/admin/notifications/create', methods=['GET', 'POST'])
@login_required
def create_notification():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form['title']
        message = request.form['message']
        notification_type = request.form['type']
        priority = request.form['priority']
        target_role = request.form['target_role']  # 'admin','faculty','student','all'

        notification = Notification(
            title=title,
            message=message,
            type=notification_type,
            priority=priority,
            target_role=target_role,
            created_by=current_user.id
        )

        db.session.add(notification)
        db.session.flush()  # get notification.id before commit

        # Create recipients based on role
        roles = ['admin', 'faculty', 'student'] if target_role == 'all' else [target_role]
        users_q = User.query.filter(User.is_active == True, User.role.in_(roles))
        recipients = []
        for u in users_q.all():
            recipients.append(NotificationRecipient(notification_id=notification.id, user_id=u.id))
        if recipients:
            db.session.add_all(recipients)

        db.session.commit()

        # Optional: email fallback (env configured)
        try:
            if os.environ.get('SMTP_HOST') and os.environ.get('SMTP_FROM'):
                send_email_broadcast(title, message, [u.email for u in users_q.limit(1000).all()])
        except Exception as e:
            app.logger.warning('Email broadcast failed: %s', e)

        flash('Notification created and sent', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/create_notification.html')

# Feedback Routes
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        subject = request.form['subject']
        message = request.form['message']
        feedback_type = request.form['feedback_type']
        priority = request.form['priority']
        
        feedback = Feedback(
            subject=subject,
            message=message,
            feedback_type=feedback_type,
            priority=priority,
            submitted_by=current_user.id if current_user.is_authenticated else None
        )
        
        db.session.add(feedback)
        db.session.commit()
        flash('Feedback submitted successfully', 'success')
        return redirect(url_for('feedback'))
    
    return render_template('feedback.html')

@app.route('/admin/feedback')
@login_required
def admin_feedback():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    feedback_list = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return render_template('admin/feedback.html', feedback_list=feedback_list)

@app.route('/admin/feedback/<int:feedback_id>/respond', methods=['POST'])
@login_required
def respond_feedback(feedback_id):
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    feedback = Feedback.query.get_or_404(feedback_id)
    response = request.form['response']
    status = request.form['status']
    
    feedback.response = response
    feedback.status = status
    feedback.responded_by = current_user.id
    feedback.responded_at = datetime.utcnow()
    
    db.session.commit()
    flash('Response sent successfully', 'success')
    return redirect(url_for('admin_feedback'))

# Library Routes
@app.route('/library')
def library():
    books = Book.query.filter_by(is_active=True).all()
    return render_template('library.html', books=books)

@app.route('/library/issue/<int:book_id>', methods=['POST'])
@login_required
def issue_book(book_id):
    if not current_user.is_student():
        flash('Only students can issue books', 'error')
        return redirect(url_for('library'))
    
    book = Book.query.get_or_404(book_id)
    
    if book.available_copies <= 0:
        flash('No copies available', 'error')
        return redirect(url_for('library'))
    
    # Check if student already has this book
    existing_issue = BookIssue.query.filter_by(
        student_id=current_user.id,
        book_id=book_id,
        status='issued'
    ).first()
    
    if existing_issue:
        flash('You already have this book issued', 'error')
        return redirect(url_for('library'))
    
    issue = BookIssue(
        book_id=book_id,
        student_id=current_user.id,
        due_date=datetime.utcnow() + timedelta(days=14)  # 2 weeks
    )
    
    book.available_copies -= 1
    
    db.session.add(issue)
    db.session.commit()
    
    flash('Book issued successfully', 'success')
    return redirect(url_for('library'))

@app.route('/library/reserve/<int:book_id>', methods=['POST'])
@login_required
def reserve_book(book_id):
    if not current_user.is_student():
        flash('Only students can reserve books', 'error')
        return redirect(url_for('library'))
    
    book = Book.query.get_or_404(book_id)
    
    # Check if student already has this book reserved or issued
    existing_reservation = BookIssue.query.filter_by(
        student_id=current_user.id,
        book_id=book_id,
        status__in=['reserved', 'issued']
    ).first()
    
    if existing_reservation:
        flash('You already have this book reserved or issued', 'error')
        return redirect(url_for('library'))
    
    reservation = BookIssue(
        book_id=book_id,
        student_id=current_user.id,
        status='reserved',
        due_date=datetime.utcnow() + timedelta(days=3)  # 3 days to collect
    )
    
    db.session.add(reservation)
    db.session.commit()
    
    flash('Book reserved successfully! Please collect within 3 days.', 'success')
    return redirect(url_for('library'))

@app.route('/library/book/<int:book_id>/barcode')
def book_barcode(book_id):
    book = Book.query.get_or_404(book_id)
    # Simple barcode representation using book ID
    barcode_data = f"BOOK-{book.id:06d}"
    return render_template('library/barcode.html', book=book, barcode_data=barcode_data)

@app.route('/library/book/<int:book_id>/qrcode')
def book_qrcode(book_id):
    book = Book.query.get_or_404(book_id)
    # QR code data with book information
    qr_data = f"Book: {book.title}\nAuthor: {book.author}\nISBN: {book.isbn}\nID: {book.id}"
    return render_template('library/qrcode.html', book=book, qr_data=qr_data)

# Events Routes
@app.route('/events')
def events():
    events = Event.query.filter_by(is_active=True).order_by(Event.event_date.desc()).all()
    return render_template('events.html', events=events, now=datetime.utcnow())

# Courses Routes
@app.route('/courses')
def courses():
    courses = Course.query.filter_by(is_active=True).all()
    return render_template('courses.html', courses=courses)

# Contact Route
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form.get('phone')
        subject = request.form['subject']
        message = request.form['message']
        contact_type = request.form.get('contact_type', 'general')
        
        contact = Contact(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message,
            contact_type=contact_type,
            ip_address=request.remote_addr
        )
        
        db.session.add(contact)
        db.session.commit()
        flash('Message sent successfully! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

# Public info pages
@app.route('/admissions')
def admissions():
    return render_template('admissions.html')

@app.route('/departments')
def departments():
    return render_template('departments.html')

@app.route('/placements')
def placements():
    return render_template('placements.html')

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500


# ==============================
# Admin Fees Management Routes
# ==============================
@app.route('/admin/fees')
@login_required
def admin_fees():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))

    # Filters
    status = request.args.get('status')  # pending, paid, overdue
    course_id = request.args.get('course_id')
    semester_id = request.args.get('semester_id')
    start = request.args.get('start')  # YYYY-MM-DD
    end = request.args.get('end')

    # Aggregate totals per student with filters
    q = db.session.query(
        User.id.label('student_id'),
        (User.first_name + ' ' + User.last_name).label('name'),
        User.email.label('email'),
        func.sum(Fee.amount).label('total_amount'),
        func.coalesce(func.sum(Fee.paid_amount), 0).label('total_paid')
    ).join(Fee, Fee.student_id == User.id)

    # Apply filters
    q = q.filter(User.role == 'student')
    if course_id:
        q = q.filter(User.course_id == course_id)
    if semester_id:
        q = q.filter(User.semester_id == semester_id)
    if start and end:
        q = q.filter(Fee.due_date.between(start, end))
    if status == 'paid':
        q = q.filter(Fee.status == 'paid')
    elif status == 'overdue':
        q = q.filter(Fee.status == 'overdue')
    elif status == 'pending':
        q = q.filter(Fee.status == 'pending')

    q = q.group_by(User.id, 'name', User.email)
    totals = q.all()

    # Summary stats
    all_fees = Fee.query
    if start and end:
        all_fees = all_fees.filter(Fee.due_date.between(start, end))
    if status:
        all_fees = all_fees.filter(Fee.status == status)
    collected = sum((f.paid_amount or 0) for f in all_fees.all())
    outstanding = sum((f.amount - (f.paid_amount or 0)) for f in all_fees.all())
    overdue_count = all_fees.filter(Fee.status == 'overdue').count()

    courses = Course.query.all()
    semesters = Semester.query.all()
    return render_template(
        'admin/fees.html',
        totals=totals,
        courses=courses,
        semesters=semesters,
        filters={'status': status, 'course_id': course_id, 'semester_id': semester_id, 'start': start, 'end': end},
        summary={'collected': collected, 'outstanding': outstanding, 'overdue_count': overdue_count}
    )


@app.route('/admin/fee/<int:fee_id>/remind', methods=['POST'])
@login_required
def admin_fee_remind(fee_id):
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    fee = Fee.query.get_or_404(fee_id)
    student = User.query.get_or_404(fee.student_id)
    # Create in-app notification
    n = Notification(
        title='Fee Reminder',
        message=f'Your {fee.fee_type} fee of {fee.amount:.2f} is due on {fee.due_date}.',
        type='notification',
        priority='normal',
        target_role='student',
        created_by=current_user.id
    )
    db.session.add(n)
    db.session.flush()
    nr = NotificationRecipient(notification_id=n.id, user_id=student.id)
    db.session.add(nr)
    db.session.commit()
    # Optional email/SMS
    try:
        if os.environ.get('SMTP_HOST') and os.environ.get('SMTP_FROM'):
            send_email_broadcast(
                'Fee Reminder',
                f'Dear {student.first_name}, your {fee.fee_type} fee of {fee.amount:.2f} is due on {fee.due_date}.',
                [student.email]
            )
        send_sms_if_configured(student.phone, f"Fee Reminder: {fee.fee_type} {fee.amount:.2f} due {fee.due_date}")
    except Exception as e:
        app.logger.warning('Email reminder failed: %s', e)
    flash('Reminder sent.', 'success')
    return redirect(url_for('admin_fees_student', student_id=student.id))


# ---------------
# Fee rule helpers
# ---------------
def get_applicable_benefit_rules(student: User, category: Optional[str]):
    """Return active ScholarshipRule and ConcessionRule applicable to the given student context.
    Matching logic: rule is_active and matches any provided scope fields.
    """
    sch_q = ScholarshipRule.query.filter_by(is_active=True)
    con_q = ConcessionRule.query.filter_by(is_active=True)

    def apply_scope_filters(q):
        filters = []
        # scope by user
        filters.append((q.entity.user_id == student.id) | (q.entity.user_id.is_(None))) if False else None
        return q

    # Filter by various fields if present on rules
    if category:
        sch_q = sch_q.filter((ScholarshipRule.category == category) | (ScholarshipRule.category.is_(None)))
        con_q = con_q.filter((ConcessionRule.category == category) | (ConcessionRule.category.is_(None)))
    if student.course_id:
        sch_q = sch_q.filter((ScholarshipRule.course_id == student.course_id) | (ScholarshipRule.course_id.is_(None)))
        con_q = con_q.filter((ConcessionRule.course_id == student.course_id) | (ConcessionRule.course_id.is_(None)))
    if student.semester_id:
        sch_q = sch_q.filter((ScholarshipRule.semester_id == student.semester_id) | (ScholarshipRule.semester_id.is_(None)))
        con_q = con_q.filter((ConcessionRule.semester_id == student.semester_id) | (ConcessionRule.semester_id.is_(None)))

    # user-specific rules
    sch_q = sch_q.filter((ScholarshipRule.user_id == student.id) | (ScholarshipRule.user_id.is_(None)))
    con_q = con_q.filter((ConcessionRule.user_id == student.id) | (ConcessionRule.user_id.is_(None)))

    # Order: user-specific first, then course/semester/category, then others
    sch_q = sch_q.order_by(ScholarshipRule.user_id.desc().nullslast())
    con_q = con_q.order_by(ConcessionRule.user_id.desc().nullslast())

    return sch_q.all(), con_q.all()


def apply_discount_rules(base_amount: float, scholarships: list, concessions: list) -> float:
    """Apply scholarship then concession rules. Respect is_cumulative. Clamp at >= 0.
    For simplicity, apply percent on current amount; apply fixed as subtraction.
    """
    amt = float(base_amount)
    # Scholarships first
    for r in scholarships:
        if r.rule_type == 'percent' and r.percent:
            amt = amt * (1 - (r.percent / 100.0))
        elif r.rule_type == 'fixed' and r.amount:
            amt = amt - r.amount
        if not r.is_cumulative:
            break
    # Concessions next
    for r in concessions:
        if r.rule_type == 'percent' and r.percent:
            amt = amt * (1 - (r.percent / 100.0))
        elif r.rule_type == 'fixed' and r.amount:
            amt = amt - r.amount
        if not r.is_cumulative:
            break
    return max(0.0, round(amt, 2))


@app.route('/admin/fees/<int:student_id>/copy_from_student', methods=['POST'])
@login_required
def admin_copy_fees_from_student(student_id):
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    target = User.query.get_or_404(student_id)
    try:
        source_email = request.form.get('source_email')
        if not source_email:
            flash('Source student email is required.', 'warning')
            return redirect(url_for('admin_fees_student', student_id=target.id))
        source = User.query.filter_by(email=source_email, role='student').first()
        if not source:
            flash('Source student not found.', 'warning')
            return redirect(url_for('admin_fees_student', student_id=target.id))

        include_paid = request.form.get('include_paid') == 'on'
        only_types = request.form.getlist('only_types')  # optional multi-select
        due_override_str = request.form.get('due_date')
        due_override = datetime.strptime(due_override_str, '%Y-%m-%d').date() if due_override_str else None
        remarks_add = request.form.get('remarks')

        q = Fee.query.filter_by(student_id=source.id)
        if not include_paid:
            q = q.filter(Fee.status != 'paid')
        fees_to_copy = q.all()

        created = 0
        for sf in fees_to_copy:
            if only_types and sf.fee_type not in only_types:
                continue
            f = Fee(
                student_id=target.id,
                fee_type=sf.fee_type,
                amount=sf.amount,
                due_date=due_override or sf.due_date,
                remarks=(sf.remarks or '') + (f" | Copied from {source.email}" if remarks_add is None else f" | {remarks_add}")
            )
            db.session.add(f)
            created += 1

        if created == 0:
            flash('No fees matched the selection to copy.', 'warning')
            return redirect(url_for('admin_fees_student', student_id=target.id))

        db.session.commit()
        log_audit('copy_fees', 'User', target.id, {'from': source.email, 'to': target.email, 'created': created})
        flash(f'Copied {created} fee item(s) from {source.email}.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.exception('Copy fees failed: %s', e)
        flash('Failed to copy fees', 'error')
    return redirect(url_for('admin_fees_student', student_id=target.id))

@app.route('/admin/fees/run_reminders', methods=['POST'])
@login_required
def admin_fees_run_reminders():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    days_ahead = int(request.form.get('days_ahead', '3'))
    today = date.today()
    upcoming = Fee.query.filter(Fee.status == 'pending', Fee.due_date.between(today, today + timedelta(days=days_ahead))).all()
    overdue = Fee.query.filter(Fee.status == 'overdue').all()
    sent = 0
    for fee in upcoming + overdue:
        student = User.query.get(fee.student_id)
        if not student:
            continue
        msg = 'Fee Due Soon' if fee in upcoming else 'Fee Overdue'
        # Create in-app notification
        n = Notification(
            title='Fee Reminder',
            message=f'{msg}: {fee.fee_type} of {fee.amount:.2f} due {fee.due_date}',
            type='notification',
            priority='normal',
            target_role='student',
            created_by=current_user.id
        )
        db.session.add(n)
        sent += 1
        # optional email/SMS
        try:
            if os.environ.get('SMTP_HOST') and os.environ.get('SMTP_FROM') and student.email:
                tpl = 'emails/fee_due_soon.html' if fee in upcoming else 'emails/fee_overdue.html'
                send_email_html(
                    subject='Fee Reminder',
                    template_name=tpl,
                    context={'student': student, 'fee': fee, 'today': today},
                    recipients=[student.email]
                )
            send_sms_if_configured(student.phone, f"{msg}: {fee.fee_type} - {fee.amount:.2f} due {fee.due_date}")
        except Exception as e:
            app.logger.warning('Email reminder failed: %s', e)
    db.session.commit()
    flash(f'Reminders queued: {sent}', 'success')
    return redirect(url_for('admin_fees'))


# ------------------------------
# Admin: Fees Bulk Assign & Edit
# ------------------------------
@app.route('/admin/fees/assign_bulk', methods=['POST'])
@login_required
def admin_fees_assign_bulk():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))

    fee_type = request.form.get('fee_type', 'Tuition')
    amount = float(request.form.get('amount', '0'))
    due_date_str = request.form.get('due_date')
    remarks = request.form.get('remarks')
    notify = request.form.get('notify') == 'on'
    course_id = request.form.get('course_id')
    semester_id = request.form.get('semester_id')
    emails_raw = request.form.get('emails')  # optional newline/comma separated

    try:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
    except Exception:
        flash('Invalid due date', 'error')
        return redirect(url_for('admin_fees'))

    q = User.query.filter_by(role='student')
    if course_id:
        q = q.filter(User.course_id == course_id)
    if semester_id:
        q = q.filter(User.semester_id == semester_id)

    if emails_raw:
        # reduce to provided emails only
        emails = [e.strip() for e in emails_raw.replace('\n', ',').split(',') if e.strip()]
        q = q.filter(User.email.in_(emails))

    students = q.all()
    created = 0
    emails_to_notify = []
    for s in students:
        try:
            db.session.add(Fee(student_id=s.id, fee_type=fee_type, amount=amount, due_date=due_date, remarks=remarks))
            created += 1
            if notify:
                emails_to_notify.append(s.email)
        except Exception as e:
            app.logger.warning('Bulk assign error for student_id=%s: %s', s.id, e)
    db.session.commit()

    if notify and emails_to_notify:
        try:
            n = Notification(
                title='New Fee Assigned',
                message=f'{fee_type} fee of {amount:.2f} due on {due_date} assigned to you.',
                type='notification', priority='normal', target_role='student', created_by=current_user.id)
            db.session.add(n)
            db.session.flush()
            targets = User.query.filter(User.email.in_(emails_to_notify)).all()
            db.session.add_all([NotificationRecipient(notification_id=n.id, user_id=u.id) for u in targets])
            db.session.commit()
            if os.environ.get('SMTP_HOST') and os.environ.get('SMTP_FROM'):
                send_email_broadcast('New Fee Assigned', f'{fee_type} fee of {amount:.2f} due on {due_date}', emails_to_notify)
            # optional SMS broadcast
            for u in targets:
                send_sms_if_configured(u.phone, f'New Fee: {fee_type} {amount:.2f} due {due_date}')
        except Exception as e:
            db.session.rollback()
            app.logger.warning('Bulk notify failed: %s', e)

    flash(f'Assigned {created} fees to students.', 'success' if created else 'warning')
    return redirect(url_for('admin_fees'))


@app.route('/admin/fee/<int:fee_id>/edit', methods=['POST'])
@login_required
def admin_edit_fee(fee_id):
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    fee = Fee.query.get_or_404(fee_id)
    try:
        fee.fee_type = request.form.get('fee_type', fee.fee_type)
        amount_str = request.form.get('amount')
        if amount_str is not None and amount_str != '':
            fee.amount = float(amount_str)
        due_str = request.form.get('due_date')
        if due_str:
            fee.due_date = datetime.strptime(due_str, '%Y-%m-%d').date()
        fee.remarks = request.form.get('remarks', fee.remarks)
        # adjust status if fully paid
        if (fee.paid_amount or 0) >= (fee.amount or 0):
            fee.status = 'paid'
        elif fee.due_date < date.today():
            fee.status = 'overdue'
        else:
            fee.status = 'pending'
        db.session.commit()
        flash('Fee updated.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.exception('Edit fee failed: %s', e)
        flash('Failed to update fee', 'error')
    return redirect(url_for('admin_fees_student', student_id=fee.student_id))
@login_required
def admin_assign_from_structure(student_id):
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    student = User.query.get_or_404(student_id)
    try:
        fs_id = request.form.get('structure_id')
        category = request.form.get('category') or None
        due_date_str = request.form.get('due_date')
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else date.today()
        remarks = request.form.get('remarks')

        # Locate structure
        fs = None
        if fs_id:
            fs = FeeStructure.query.get(int(fs_id))
        else:
            q = FeeStructure.query.filter(
                (FeeStructure.course_id == student.course_id) | (FeeStructure.course_id.is_(None)),
                (FeeStructure.semester_id == student.semester_id) | (FeeStructure.semester_id.is_(None)),
                FeeStructure.is_active.is_(True)
            )
            if category:
                q = q.filter((FeeStructure.category == category) | (FeeStructure.category.is_(None)))
            fs = q.order_by(FeeStructure.effective_from.desc().nullslast()).first()
        if not fs:
            flash('No active fee structure found.', 'warning')
            return redirect(url_for('admin_fees_student', student_id=student.id))

        # Options
        prevent_dups = request.form.get('prevent_duplicates', 'on') == 'on'
        dup_scope = request.form.get('dup_scope', 'same_month')  # exact_date | same_month
        apply_rules = request.form.get('apply_rules', 'on') == 'on'

        # Collect components
        components = [
            ('include_tuition', 'Tuition', fs.tuition or 0),
            ('include_hostel', 'Hostel', fs.hostel or 0),
            ('include_transport', 'Transport', fs.transport or 0),
            ('include_exam', 'Exam', fs.exam or 0),
            ('include_misc', 'Misc', fs.misc or 0),
        ]

        # Get rules if requested
        sch_rules, con_rules = ([], [])
        if apply_rules:
            sch_rules, con_rules = get_applicable_benefit_rules(student, category)

        created = 0

        for field_name, label, amount in components:
            if request.form.get(field_name) != 'on':
                continue
            base = float(amount or 0)
            if base <= 0:
                continue

            final_amount = base
            if apply_rules:
                final_amount = apply_discount_rules(base, sch_rules, con_rules)
                # Ensure not below zero
                final_amount = max(0.0, round(final_amount, 2))

            if prevent_dups:
                if dup_scope == 'exact_date':
                    exists = Fee.query.filter_by(student_id=student.id, fee_type=label, due_date=due_date).first()
                else:  # same_month
                    first_day = date(due_date.year, due_date.month, 1)
                    # next month first day
                    nm = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1)
                    last_day = nm - timedelta(days=1)
                    exists = Fee.query.filter(
                        Fee.student_id == student.id,
                        Fee.fee_type == label,
                        Fee.due_date.between(first_day, last_day),
                    ).first()
                if exists:
                    continue

            f = Fee(student_id=student.id, fee_type=label, amount=final_amount, due_date=due_date, remarks=remarks)
            db.session.add(f)
            created += 1

        if created == 0:
            flash('No components selected or all zero.', 'warning')
            return redirect(url_for('admin_fees_student', student_id=student.id))

        db.session.commit()
        log_audit('assign_from_structure', 'FeeStructure', fs.id, {'student_id': student.id, 'created': created})
        flash(f'Assigned {created} fee item(s) from structure.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.exception('Assign from structure failed: %s', e)
        flash('Failed to assign from structure', 'error')
    return redirect(url_for('admin_fees_student', student_id=student.id))


# ------------------
# SMS helper (optional)
# ------------------
def send_sms_if_configured(phone: Optional[str], body: str) -> None:
    """Send SMS if TWILIO_* env vars present and phone exists. Fail silently."""
    if not phone:
        return
    sid = os.environ.get('TWILIO_ACCOUNT_SID')
    token = os.environ.get('TWILIO_AUTH_TOKEN')
    sender = os.environ.get('TWILIO_FROM')
    if not (sid and token and sender):
        return
    try:
        from twilio.rest import Client
        client = Client(sid, token)
        client.messages.create(to=phone, from_=sender, body=body)
    except Exception as e:
        app.logger.warning('SMS send failed: %s', e)


# ------------------------------
# Admin: Fee Configuration (Structures & Late Fee Rules)
# ------------------------------
@app.route('/admin/fees/config')
@login_required
def admin_fees_config():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    fee_structures = FeeStructure.query.order_by(FeeStructure.created_at.desc()).all()
    late_rules = LateFeeRule.query.order_by(LateFeeRule.created_at.desc()).all()
    courses = Course.query.all()
    semesters = Semester.query.all()
    return render_template('admin/fees_config.html', fee_structures=fee_structures, late_rules=late_rules, courses=courses, semesters=semesters)


@app.route('/admin/fees/config/structure/create', methods=['POST'])
@login_required
def admin_create_fee_structure():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    try:
        fs = FeeStructure(
            course_id=request.form.get('course_id') or None,
            semester_id=request.form.get('semester_id') or None,
            category=request.form.get('category') or None,
            tuition=float(request.form.get('tuition') or 0),
            hostel=float(request.form.get('hostel') or 0),
            transport=float(request.form.get('transport') or 0),
            exam=float(request.form.get('exam') or 0),
            misc=float(request.form.get('misc') or 0),
            effective_from=datetime.strptime(request.form.get('effective_from'), '%Y-%m-%d') if request.form.get('effective_from') else None,
            effective_to=datetime.strptime(request.form.get('effective_to'), '%Y-%m-%d') if request.form.get('effective_to') else None,
            is_active=True if request.form.get('is_active') == 'on' else False,
            late_fee_rule_id=request.form.get('late_fee_rule_id') or None,
        )
        db.session.add(fs)
        db.session.commit()
        log_audit('create', 'FeeStructure', fs.id, {'course_id': fs.course_id, 'semester_id': fs.semester_id, 'category': fs.category})
        flash('Fee structure created.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.exception('Create fee structure failed: %s', e)
        flash('Failed to create fee structure', 'error')
    return redirect(url_for('admin_fees_config'))


@app.route('/admin/fees/config/structure/<int:fs_id>/delete', methods=['POST'])
@login_required
def admin_delete_fee_structure(fs_id):
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    fs = FeeStructure.query.get_or_404(fs_id)
    try:
        db.session.delete(fs)
        db.session.commit()
        log_audit('delete', 'FeeStructure', fs_id, {})
        flash('Fee structure deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.exception('Delete fee structure failed: %s', e)
        flash('Failed to delete fee structure', 'error')
    return redirect(url_for('admin_fees_config'))


@app.route('/admin/fees/config/late_rule/create', methods=['POST'])
@login_required
def admin_create_late_rule():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    try:
        lr = LateFeeRule(
            name=request.form.get('name'),
            rule_type=request.form.get('rule_type') or 'fixed_per_day',
            grace_days=int(request.form.get('grace_days') or 0),
            per_day_amount=float(request.form.get('per_day_amount') or 0) if request.form.get('rule_type') == 'fixed_per_day' else None,
            per_day_percent=float(request.form.get('per_day_percent') or 0) if request.form.get('rule_type') == 'percent_per_day' else None,
            slabs=request.form.get('slabs') if request.form.get('rule_type') == 'slabbed' else None,
            is_active=True,
        )
        db.session.add(lr)
        db.session.commit()
        log_audit('create', 'LateFeeRule', lr.id, {'rule_type': lr.rule_type})
        flash('Late fee rule created.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.exception('Create late rule failed: %s', e)
        flash('Failed to create late fee rule', 'error')
    return redirect(url_for('admin_fees_config'))


@app.route('/admin/fees/config/late_rule/<int:lr_id>/delete', methods=['POST'])
@login_required
def admin_delete_late_rule(lr_id):
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    lr = LateFeeRule.query.get_or_404(lr_id)
    try:
        db.session.delete(lr)
        db.session.commit()
        log_audit('delete', 'LateFeeRule', lr_id, {})
        flash('Late fee rule deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.exception('Delete late rule failed: %s', e)
        flash('Failed to delete late fee rule', 'error')
    return redirect(url_for('admin_fees_config'))


@app.route('/admin/fee/<int:fee_id>/receipt')
@login_required
def admin_fee_receipt(fee_id):
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    fee = Fee.query.get_or_404(fee_id)
    student = User.query.get_or_404(fee.student_id)
    return render_template('admin/fee_receipt.html', fee=fee, student=student, now=datetime.utcnow())


@app.route('/admin/fees/upload', methods=['POST'])
@login_required
def admin_fees_upload():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))

    file = request.files.get('csv')
    notify = request.form.get('notify') == 'on'
    if not file:
        flash('CSV file is required', 'error')
        return redirect(url_for('admin_fees'))

    import csv, io
    stream = io.StringIO(file.stream.read().decode('utf-8'))
    reader = csv.DictReader(stream)
    created = 0
    errors = 0
    notified_emails = []
    for row in reader:
        try:
            email = row.get('student_email') or row.get('email')
            student = User.query.filter_by(email=email, role='student').first()
            if not student:
                errors += 1
                continue
            fee = Fee(
                student_id=student.id,
                fee_type=row.get('fee_type') or 'Tuition',
                amount=float(row.get('amount', 0)),
                due_date=datetime.strptime(row.get('due_date'), '%Y-%m-%d').date(),
                remarks=row.get('remarks')
            )
            db.session.add(fee)
            created += 1
            if notify:
                notified_emails.append(student.email)
        except Exception as e:
            app.logger.warning('CSV row error: %s -> %s', row, e)
            errors += 1
    db.session.commit()

    if notify and notified_emails:
        try:
            title = 'New Fee Assigned'
            message = 'A new fee has been assigned to your account. Please review your fees section.'
            # Create a single notification object and assign to all impacted students
            n = Notification(title=title, message=message, type='notification', priority='normal', target_role='student', created_by=current_user.id)
            db.session.add(n)
            db.session.flush()
            targets = User.query.filter(User.email.in_(notified_emails)).all()
            db.session.add_all([NotificationRecipient(notification_id=n.id, user_id=u.id) for u in targets])
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.warning('Failed to create fee notifications: %s', e)

        # Optional email
        try:
            if os.environ.get('SMTP_HOST') and os.environ.get('SMTP_FROM'):
                send_email_broadcast('New Fee Assigned', 'A new fee has been assigned to your account.', notified_emails)
        except Exception as e:
            app.logger.warning('Email broadcast failed: %s', e)

    flash(f'Uploaded: {created} fees. Errors: {errors}.', 'success' if created and errors == 0 else 'warning')
    return redirect(url_for('admin_fees'))


@app.route('/admin/fees/<int:student_id>', methods=['GET', 'POST'])
@login_required
def admin_fees_student(student_id):
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))

    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        flash('Not a student', 'error')
        return redirect(url_for('admin_fees'))

    # Handle installment plan creation
    if request.method == 'POST':
        try:
            total_amount = float(request.form['total_amount'])
            num = int(request.form['installments'])
            start_due = datetime.strptime(request.form['start_due_date'], '%Y-%m-%d').date()
            interval_months = int(request.form.get('interval_months', 1))
            fee_type = request.form.get('fee_type', 'Tuition')
            remarks = request.form.get('remarks')

            # Create N fee rows splitting total_amount
            base = round(total_amount / num, 2)
            amounts = [base] * num
            # adjust rounding difference
            diff = round(total_amount - sum(amounts), 2)
            if diff != 0:
                amounts[-1] = round(amounts[-1] + diff, 2)

            from dateutil.relativedelta import relativedelta
            due = start_due
            for amt in amounts:
                db.session.add(Fee(
                    student_id=student.id,
                    fee_type=fee_type,
                    amount=amt,
                    due_date=due,
                    remarks=remarks
                ))
                due = due + relativedelta(months=+interval_months)
            db.session.commit()
            flash('Installment plan created.', 'success')
            return redirect(url_for('admin_fees_student', student_id=student.id))
        except Exception as e:
            db.session.rollback()
            app.logger.exception('Installment creation failed: %s', e)
            flash('Failed to create installment plan', 'error')

    fees = Fee.query.filter_by(student_id=student.id).order_by(Fee.due_date.asc()).all()
    totals = {
        'total_amount': sum(f.amount for f in fees),
        'total_paid': sum(f.paid_amount or 0 for f in fees),
    }
    totals['balance'] = round(totals['total_amount'] - totals['total_paid'], 2)
    # Provide structures for the auto-assign form
    structures = FeeStructure.query.filter(
        (FeeStructure.course_id == student.course_id) | (FeeStructure.course_id.is_(None)),
        (FeeStructure.semester_id == student.semester_id) | (FeeStructure.semester_id.is_(None)),
        FeeStructure.is_active.is_(True)
    ).order_by(FeeStructure.effective_from.desc().nullslast()).all()
    return render_template('admin/fees_student.html', student=student, fees=fees, totals=totals, structures=structures)


@app.route('/admin/fees/<int:student_id>/add_fee', methods=['POST'])
@login_required
def admin_add_fee(student_id):
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    student = User.query.get_or_404(student_id)
    try:
        fee_type = request.form.get('fee_type', 'Tuition')
        amount = float(request.form.get('amount', '0'))
        due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
        remarks = request.form.get('remarks')
        f = Fee(student_id=student.id, fee_type=fee_type, amount=amount, due_date=due_date, remarks=remarks)
        db.session.add(f)
        db.session.commit()
        flash('Fee added.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.exception('Add fee failed: %s', e)
        flash('Failed to add fee', 'error')
    return redirect(url_for('admin_fees_student', student_id=student.id))


@app.route('/admin/fee/<int:fee_id>/record_payment', methods=['POST'])
@login_required
def admin_record_payment(fee_id):
    if not (current_user.is_admin() or getattr(current_user, 'role', None) == 'accountant'):
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    fee = Fee.query.get_or_404(fee_id)
    try:
        amt = float(request.form.get('paid_amount', '0'))
        method = request.form.get('payment_method') or 'Manual'
        txn = request.form.get('transaction_id') or f"TXN{uuid.uuid4().hex[:8].upper()}"
        receipt = request.form.get('receipt_number') or f"RCP{uuid.uuid4().hex[:8].upper()}"
        paid_date_str = request.form.get('paid_date')
        paid_at = datetime.strptime(paid_date_str, '%Y-%m-%dT%H:%M') if paid_date_str else datetime.utcnow()

        # Create payment record
        payment = Payment(fee_id=fee.id, amount=amt, method=method, txn_id=txn, receipt_number=receipt, status='completed', paid_at=paid_at)
        db.session.add(payment)

        # Update fee aggregates
        fee.paid_amount = (fee.paid_amount or 0) + amt
        fee.payment_method = method
        fee.transaction_id = txn
        fee.receipt_number = receipt
        fee.paid_date = paid_at
        if (fee.paid_amount or 0) >= (fee.amount or 0):
            fee.status = 'paid'
        elif fee.due_date < date.today():
            fee.status = 'overdue'
        else:
            fee.status = 'pending'

        db.session.commit()
        log_audit('record_payment', 'Payment', payment.id, {'fee_id': fee.id, 'amount': amt, 'method': method, 'txn_id': txn, 'receipt_number': receipt})
        # Notify
        notify_payment_confirmation(User.query.get(fee.student_id), fee, payment)
        flash('Payment recorded.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.exception('Record payment failed: %s', e)
        flash('Failed to record payment', 'error')
    return redirect(url_for('admin_fees_student', student_id=fee.student_id))

def log_audit(action: str, entity: str, entity_id: int, details: dict | None = None):
    """Create an AuditLog row, ignore failures."""
    try:
        d = json.dumps(details or {})
        entry = AuditLog(action=action, entity=entity, entity_id=entity_id, user_id=getattr(current_user, 'id', None), details=d)
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.warning('Audit log failed: %s', e)


@app.route('/admin/fee/<int:fee_id>/mark_paid', methods=['POST'])
@login_required
def admin_mark_paid(fee_id):
    if not (current_user.is_admin() or getattr(current_user, 'role', None) == 'accountant'):
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    fee = Fee.query.get_or_404(fee_id)
    try:
        # Create payment entry for remaining balance
        remaining = (fee.amount or 0) - (fee.paid_amount or 0)
        if remaining < 0:
            remaining = 0
        method = request.form.get('payment_method') or fee.payment_method or 'Manual'
        txn = request.form.get('transaction_id') or fee.transaction_id or f"TXN{uuid.uuid4().hex[:8].upper()}"
        receipt = request.form.get('receipt_number') or fee.receipt_number or f"RCP{uuid.uuid4().hex[:8].upper()}"
        if remaining > 0:
            p = Payment(fee_id=fee.id, amount=remaining, method=method, txn_id=txn, receipt_number=receipt, status='completed')
            db.session.add(p)
        # update fee aggregates
        fee.paid_amount = (fee.paid_amount or 0) + remaining
        fee.status = 'paid'
        fee.paid_date = datetime.utcnow()
        fee.payment_method = method
        fee.transaction_id = txn
        fee.receipt_number = receipt
        db.session.commit()
        log_audit('mark_paid', 'Fee', fee.id, {'method': method, 'txn_id': txn, 'receipt_number': receipt, 'amount': remaining})
        # Notify
        if remaining > 0:
            notify_payment_confirmation(User.query.get(fee.student_id), fee, p)
        else:
            # create a synthetic payment object for email display
            class _P: pass
            _pp = _P(); _pp.amount = 0.0; _pp.method = method; _pp.txn_id = txn; _pp.receipt_number = receipt; _pp.paid_at = datetime.utcnow()
            notify_payment_confirmation(User.query.get(fee.student_id), fee, _pp)
        flash('Marked as paid.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.exception('Mark paid failed: %s', e)
        flash('Failed to mark as paid', 'error')
    return redirect(url_for('admin_fees_student', student_id=fee.student_id))


@app.route('/admin/fee/<int:fee_id>/delete', methods=['POST'])
@login_required
def admin_delete_fee(fee_id):
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    fee = Fee.query.get_or_404(fee_id)
    sid = fee.student_id
    try:
        db.session.delete(fee)
        db.session.commit()
        flash('Fee deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.exception('Delete fee failed: %s', e)
        flash('Failed to delete fee', 'error')
    return redirect(url_for('admin_fees_student', student_id=sid))


# ============================
# Student: Fees Dashboard & Receipt
# ============================
@app.route('/student/fees')
@login_required
def student_fees():
    if not current_user.is_student():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    fees = Fee.query.filter_by(student_id=current_user.id).order_by(Fee.due_date.asc()).all()
    totals = {
        'total': sum(f.amount or 0 for f in fees),
        'paid': sum(f.paid_amount or 0 for f in fees),
    }
    totals['balance'] = round((totals['total'] or 0) - (totals['paid'] or 0), 2)
    return render_template('student/fees.html', fees=fees, totals=totals)


@app.route('/student/fees/<int:fee_id>/receipt')
@login_required
def student_fee_receipt(fee_id):
    if not current_user.is_student():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    fee = Fee.query.get_or_404(fee_id)
    if fee.student_id != current_user.id:
        flash('Not permitted', 'error')
        return redirect(url_for('student_fees'))
    last_payment = Payment.query.filter_by(fee_id=fee.id).order_by(Payment.paid_at.desc()).first()
    return render_template('student/receipt.html', fee=fee, payment=last_payment, student=current_user)


# ============================
# Admin: Audit Log UI
# ============================
@app.route('/admin/audit')
@login_required
def admin_audit():
    if not current_user.is_admin():
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    action = request.args.get('action')
    entity = request.args.get('entity')
    user_id = request.args.get('user_id', type=int)
    start = request.args.get('start')
    end = request.args.get('end')
    q = AuditLog.query.order_by(AuditLog.created_at.desc())
    if action:
        q = q.filter(AuditLog.action == action)
    if entity:
        q = q.filter(AuditLog.entity == entity)
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    if start:
        try:
            start_dt = datetime.strptime(start, '%Y-%m-%d')
            q = q.filter(AuditLog.created_at >= start_dt)
        except Exception:
            pass
    if end:
        try:
            end_dt = datetime.strptime(end, '%Y-%m-%d') + timedelta(days=1)
            q = q.filter(AuditLog.created_at < end_dt)
        except Exception:
            pass
    entries = q.limit(500).all()
    users = User.query.all()
    # Template expects 'logs'
    return render_template('admin/audit_log.html', logs=entries, users=users)


# ============================
# Admin: Fees Reports Dashboard
# ============================
@app.route('/admin/reports/fees')
@login_required
def admin_reports_fees():
    if not (current_user.is_admin() or getattr(current_user, 'role', None) == 'accountant'):
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    # Daily collection (today)
    today = date.today()
    payments_today = Payment.query.filter(func.date(Payment.paid_at) == today).all()
    daily_total = sum(p.amount or 0 for p in payments_today)
    # Outstanding dues
    fees_pending = Fee.query.filter(Fee.status.in_(['pending', 'overdue'])).all()
    outstanding_total = sum((f.amount or 0) - (f.paid_amount or 0) for f in fees_pending)
    # Breakdown by fee_type
    from collections import defaultdict
    type_breakdown = defaultdict(lambda: {'amount': 0.0, 'balance': 0.0})
    for f in Fee.query.all():
        tb = type_breakdown[f.fee_type]
        tb['amount'] += (f.amount or 0)
        tb['balance'] += max((f.amount or 0) - (f.paid_amount or 0), 0)
    # Breakdown by course
    course_breakdown = []
    for c in Course.query.all():
        fees_c = Fee.query.join(User, Fee.student_id == User.id).filter(User.course_id == c.id).all()
        if not fees_c:
            continue
        total_c = sum(f.amount or 0 for f in fees_c)
        bal_c = sum(max((f.amount or 0) - (f.paid_amount or 0), 0) for f in fees_c)
        course_breakdown.append({'course': c, 'amount': total_c, 'balance': bal_c})
    return render_template(
        'admin/reports/fees.html',
        today=today,
        payments_today=payments_today,
        daily_total=daily_total,
        outstanding_total=outstanding_total,
        type_breakdown=type_breakdown,
        course_breakdown=course_breakdown,
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
