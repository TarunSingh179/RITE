from models.user import db
from datetime import datetime

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    feedback_type = db.Column(db.String(50), nullable=False)  # general, academic, technical, complaint, suggestion
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, resolved, closed
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))  # admin/faculty assigned to handle
    response = db.Column(db.Text)
    responded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    responded_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    submitter = db.relationship('User', foreign_keys=[submitted_by], backref='submitted_feedback')
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_feedback')
    responder = db.relationship('User', foreign_keys=[responded_by], backref='responded_feedback')
    
    def __repr__(self):
        return f'<Feedback {self.subject} - {self.submitter.username}>'

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    contact_type = db.Column(db.String(50), default='general')  # general, admission, academic, technical
    status = db.Column(db.String(20), default='new')  # new, read, responded, closed
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime)
    response = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Contact {self.name} - {self.subject}>' 