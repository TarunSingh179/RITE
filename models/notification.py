from models.user import db
from datetime import datetime

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # announcement, notification, alert
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    target_role = db.Column(db.String(20))  # admin, faculty, student, all
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='created_notifications')
    recipients = db.relationship('NotificationRecipient', backref='notification', lazy=True)
    
    def __repr__(self):
        return f'<Notification {self.title}>'

class NotificationRecipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey('notification.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref='received_notifications')
    
    def __repr__(self):
        return f'<NotificationRecipient {self.user.username} - {self.notification.title}>' 