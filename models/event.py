from models.user import db
from datetime import datetime

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    venue = db.Column(db.String(200))
    organizer = db.Column(db.String(100))
    category = db.Column(db.String(50))  # Academic, Cultural, Sports, etc.
    image_path = db.Column(db.String(200))
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Event {self.title}>' 