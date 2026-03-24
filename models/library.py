from models.user import db
from datetime import datetime, timedelta

class Book(db.Model):
    """Model representing a book in the library."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(20), unique=True)
    publisher = db.Column(db.String(100))
    publication_year = db.Column(db.Integer)
    category = db.Column(db.String(50))  # Fiction, Non-fiction, Academic, etc.
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    location = db.Column(db.String(50))  # Shelf location
    description = db.Column(db.Text)
    cover_image = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    issues = db.relationship('BookIssue', backref='book', lazy=True)
    
    def __repr__(self) -> str:
        """String representation of the Book object."""
        return f'<Book {self.title}>'

class BookIssue(db.Model):
    """Model representing a book issue transaction."""
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='issued')  # issued, returned, overdue
    fine_amount = db.Column(db.Float, default=0.0)
    remarks = db.Column(db.Text)
    
    def __repr__(self) -> str:
        """String representation of the BookIssue object."""
        return f'<BookIssue {self.id}>'
    
    def is_overdue(self) -> bool:
        """Check if the book issue is overdue."""
        if self.status == 'returned':
            return False
        return datetime.utcnow() > self.due_date
    
    def calculate_fine(self) -> float:
        """
        Calculate the fine for overdue books.
        Returns the fine amount in ₹ (1 per day overdue).
        """
        if self.status == 'returned' or not self.is_overdue():
            return 0.0
        days_overdue = (datetime.utcnow() - self.due_date).days
        return max(0.0, days_overdue * 1.0)  # ₹1 per day fine