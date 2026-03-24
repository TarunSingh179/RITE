from models.user import db
from datetime import datetime

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)  # mid-term, final, quiz, assignment
    total_marks = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    duration = db.Column(db.Integer)  # in minutes
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    subject = db.relationship('Subject', backref='exams')
    marks = db.relationship('ExamMark', backref='exam', lazy=True)
    
    def __repr__(self):
        return f'<Exam {self.name} - {self.subject.name}>'

class ExamMark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.Text)
    graded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # faculty who graded
    graded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='exam_marks')
    faculty = db.relationship('User', foreign_keys=[graded_by], backref='graded_marks')
    
    def get_percentage(self):
        if self.exam.total_marks > 0:
            return (self.marks_obtained / self.exam.total_marks) * 100
        return 0
    
    def get_grade(self):
        percentage = self.get_percentage()
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B+'
        elif percentage >= 60:
            return 'B'
        elif percentage >= 50:
            return 'C+'
        elif percentage >= 40:
            return 'C'
        else:
            return 'F'
    
    def __repr__(self):
        return f'<ExamMark {self.student.username} - {self.exam.name} - {self.marks_obtained}>' 