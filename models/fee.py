from models.user import db
from datetime import datetime

class Fee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fee_type = db.Column(db.String(50), nullable=False)  # Tuition, Library, Exam, etc.
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    paid_amount = db.Column(db.Float, default=0.0)
    paid_date = db.Column(db.DateTime)
    payment_method = db.Column(db.String(50))  # Cash, Card, Online, etc.
    transaction_id = db.Column(db.String(100))
    receipt_number = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')  # pending, paid, overdue
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Fee {self.id}>'
    
    def is_paid(self):
        return self.status == 'paid'
    
    def is_overdue(self):
        if self.is_paid():
            return False
        return datetime.utcnow().date() > self.due_date
    
    def get_balance(self):
        return self.amount - self.paid_amount 