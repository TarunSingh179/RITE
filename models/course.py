from models.user import db
from datetime import datetime

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    duration = db.Column(db.String(20))  # e.g., "4 years", "2 years"
    description = db.Column(db.Text)
    total_semesters = db.Column(db.Integer, default=8)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    semesters = db.relationship('Semester', backref='course', lazy=True)
    
    def __repr__(self):
        return f'<Course {self.name}>'

class Semester(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # e.g., "1st Semester", "2nd Semester"
    number = db.Column(db.Integer, nullable=False)  # 1, 2, 3, etc.
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    subjects = db.relationship('Subject', backref='semester', lazy=True)
    
    def __repr__(self):
        return f'<Semester {self.name}>'

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    credits = db.Column(db.Integer, default=3)
    description = db.Column(db.Text)
    syllabus = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    faculty = db.relationship('User', backref='subjects_teaching')
    assignments = db.relationship('Assignment', backref='subject', lazy=True)
    results = db.relationship('Result', backref='subject', lazy=True)
    
    def __repr__(self):
        return f'<Subject {self.name}>' 