from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # admin, faculty, student, accountant
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    profile_picture = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Account lockout fields
    failed_login_attempts = db.Column(db.Integer, default=0)
    lockout_until = db.Column(db.DateTime, nullable=True)
    
    # Email verification fields
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(20))
    email_verification_sent_at = db.Column(db.DateTime)
    
    # Student specific fields
    student_id = db.Column(db.String(20), unique=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'))
    enrollment_date = db.Column(db.Date)
    
    # Faculty specific fields
    faculty_id = db.Column(db.String(20), unique=True)
    department = db.Column(db.String(100))
    qualification = db.Column(db.String(100))
    experience_years = db.Column(db.Integer)
    
    # Relationships
    course = db.relationship('Course', backref='students')
    semester = db.relationship('Semester', backref='students')
    assignments_submitted = db.relationship('AssignmentSubmission', backref='student', lazy=True)
    books_issued = db.relationship('BookIssue', backref='student', lazy=True)
    fees = db.relationship('Fee', backref='student', lazy=True)
    results = db.relationship('Result', backref='student', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_faculty(self):
        return self.role == 'faculty'
    
    def is_student(self):
        return self.role == 'student'
    
    def is_accountant(self):
        return self.role == 'accountant'
    
    def __repr__(self):
        return f'<User {self.username}>'