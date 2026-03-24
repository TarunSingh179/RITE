from models.user import db
from datetime import datetime, date

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), nullable=False)  # present, absent, late
    marked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # faculty who marked
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='attendance_records')
    subject = db.relationship('Subject', backref='attendance_records')
    faculty = db.relationship('User', foreign_keys=[marked_by], backref='marked_attendance')
    
    def __repr__(self):
        return f'<Attendance {self.student.username} - {self.subject.name} - {self.date}>'

class AttendanceReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=False)
    report_date = db.Column(db.Date, nullable=False, default=date.today)
    total_students = db.Column(db.Integer, default=0)
    present_count = db.Column(db.Integer, default=0)
    absent_count = db.Column(db.Integer, default=0)
    late_count = db.Column(db.Integer, default=0)
    attendance_percentage = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    subject = db.relationship('Subject', backref='attendance_reports')
    semester = db.relationship('Semester', backref='attendance_reports')
    
    def __repr__(self):
        return f'<AttendanceReport {self.subject.name} - {self.report_date}>' 