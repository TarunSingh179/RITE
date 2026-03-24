from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
import uuid
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

mobile_api = Blueprint('mobile_api', __name__, url_prefix='/api/v1')

def mobile_token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Verify token logic here
            user = verify_mobile_token(token)
            if not user:
                return jsonify({'error': 'Invalid token'}), 401
            request.current_user = user
        except:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

@mobile_api.route('/login', methods=['POST'])
def mobile_login():
    """Mobile authentication endpoint"""
    data = request.json
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    from models.user import User
    user = User.query.filter_by(username=data['username']).first()
    
    if user and user.check_password(data['password']) and user.is_active:
        token = str(uuid.uuid4())
        # Store token in database with expiration
        from models.user import MobileToken
        mobile_token = MobileToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(mobile_token)
        db.session.commit()
        
        return jsonify({
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@mobile_api.route('/notifications', methods=['GET'])
@mobile_token_required
def mobile_notifications():
    """Get user notifications"""
    from models.notification import Notification
    notifications = Notification.query.filter_by(
        target_role=current_user.role,
        is_active=True
    ).order_by(Notification.created_at.desc()).limit(20).all()
    
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.type,
        'priority': n.priority,
        'created_at': n.created_at.isoformat()
    } for n in notifications])

@mobile_api.route('/dashboard', methods=['GET'])
@mobile_token_required
def mobile_dashboard():
    """Mobile dashboard data"""
    from models.user import User
    from models.assignment import Assignment
    from models.fee import Fee
    
    if current_user.role == 'student':
        assignments = Assignment.query.join(Subject).filter(
            Subject.semester_id == current_user.semester_id
        ).all()
        
        fees = Fee.query.filter_by(student_id=current_user.id).all()
        
        return jsonify({
            'assignments': [{
                'id': a.id,
                'title': a.title,
                'due_date': a.due_date.isoformat(),
                'max_marks': a.max_marks,
                'subject': a.subject.name
            } for a in assignments],
            'fees': [{
                'id': f.id,
                'fee_type': f.fee_type,
                'amount': f.amount,
                'due_date': f.due_date.isoformat(),
                'status': f.status
            } for f in fees]
        })
    
    return jsonify({'error': 'Unauthorized'}), 403
