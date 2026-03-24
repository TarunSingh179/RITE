from models.user import db
from datetime import datetime

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    max_marks = db.Column(db.Integer, default=100)
    file_path = db.Column(db.String(200))  # For assignment file attachment
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    faculty = db.relationship('User', backref='assignments_created')
    submissions = db.relationship('AssignmentSubmission', backref='assignment', lazy=True)
    
    def __repr__(self):
        return f'<Assignment {self.title}>'

class AssignmentSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    submission_file = db.Column(db.String(200))  # File path of submitted assignment
    submission_text = db.Column(db.Text)  # Text submission if any
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    marks_obtained = db.Column(db.Float)
    feedback = db.Column(db.Text)
    is_late = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='submitted')  # submitted, graded, late
    
    def __repr__(self):
        return f'<AssignmentSubmission {self.id}>' 