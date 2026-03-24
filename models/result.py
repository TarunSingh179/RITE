from models.user import db
from datetime import datetime

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    test_type = db.Column(db.String(50), nullable=False)  # Internal, Mid-term, Final, etc.
    test_date = db.Column(db.Date, nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    percentage = db.Column(db.Float)
    grade = db.Column(db.String(5))  # A, B, C, D, F
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Result {self.id}>'
    
    def calculate_percentage(self):
        if self.max_marks > 0:
            return (self.marks_obtained / self.max_marks) * 100
        return 0
    
    def calculate_grade(self):
        percentage = self.calculate_percentage()
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B+'
        elif percentage >= 60:
            return 'B'
        elif percentage >= 50:
            return 'C'
        elif percentage >= 40:
            return 'D'
        else:
            return 'F' 