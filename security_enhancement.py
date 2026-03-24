import secrets
import hashlib
import pyotp
import qrcode
from io import BytesIO
import base64
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from models.user import User, SecurityLog
from models import db
from datetime import datetime, timedelta

security_bp = Blueprint('security', __name__, url_prefix='/security')

class SecurityManager:
    """Enhanced security features manager"""
    
    @staticmethod
    def generate_device_fingerprint():
        """Generate unique device fingerprint"""
        user_agent = request.headers.get('User-Agent', '')
        ip_address = request.remote_addr
        accept_language = request.headers.get('Accept-Language', '')
        
        fingerprint_data = f"{user_agent}{ip_address}{accept_language}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]
    
    @staticmethod
    def detect_suspicious_activity(user_id):
        """Detect suspicious login patterns"""
        recent_logs = SecurityLog.query.filter(
            SecurityLog.user_id == user_id,
            SecurityLog.created_at >= datetime.utcnow() - timedelta(hours=1)
        ).all()
        
        # Check for multiple failed logins
        failed_logins = [log for log in recent_logs if log.event_type == 'failed_login']
        if len(failed_logins) >= 5:
            return True
        
        # Check for unusual locations
        locations = [log.ip_address for log in recent_logs if log.ip_address]
        if len(set(locations)) >= 3:
            return True
        
        return False
    
    @staticmethod
    def generate_backup_codes(user_id, count=10):
        """Generate backup 2FA codes"""
        codes = []
        for _ in range(count):
            code = ''.join([str(secrets.randbelow(10)) for _ in range(8)])
            codes.append(code)
        
        # Store hashed codes in database
        hashed_codes = [hashlib.sha256(code.encode()).hexdigest() for code in codes]
        user = User.query.get(user_id)
        user.backup_codes = ','.join(hashed_codes)
        db.session.commit()
        
        return codes

@security_bp.route('/2fa/setup', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    """Setup two-factor authentication"""
    if request.method == 'POST':
        # Generate TOTP secret
        secret = pyotp.random_base32()
        current_user.totp_secret = secret
        
        # Generate QR code
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=current_user.email,
            issuer_name='College Management System'
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({
            'secret': secret,
            'qr_code': img_str,
            'backup_codes': SecurityManager.generate_backup_codes(current_user.id)
        })
    
    return render_template('security/setup_2fa.html')

@security_bp.route('/2fa/verify', methods=['POST'])
@login_required
def verify_2fa():
    """Verify 2FA code"""
    code = request.json.get('code')
    secret = current_user.totp_secret
    
    if not secret:
        return jsonify({'error': '2FA not setup'}), 400
    
    totp = pyotp.TOTP(secret)
    
    if totp.verify(code):
        # Log successful 2FA verification
        log = SecurityLog(
            user_id=current_user.id,
            event_type='2fa_verified',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'status': 'success'})
    
    # Check backup codes
    backup_codes = current_user.backup_codes.split(',') if current_user.backup_codes else []
    hashed_code = hashlib.sha256(code.encode()).hexdigest()
    
    if hashed_code in backup_codes:
        # Remove used backup code
        backup_codes.remove(hashed_code)
        current_user.backup_codes = ','.join(backup_codes)
        
        log = SecurityLog(
            user_id=current_user.id,
            event_type='backup_code_used',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'status': 'success'})
    
    return jsonify({'error': 'Invalid code'}), 400

@security_bp.route('/sessions', methods=['GET'])
@login_required
def active_sessions():
    """Get active user sessions"""
    from models.user import UserSession
    
    sessions = UserSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(UserSession.last_activity.desc()).all()
    
    return jsonify([{
        'id': s.id,
        'device': s.device_info,
        'ip_address': s.ip_address,
        'last_activity': s.last_activity.isoformat(),
        'is_current': s.session_id == request.cookies.get('session_id')
    } for s in sessions])

@security_bp.route('/sessions/<int:session_id>/revoke', methods=['POST'])
@login_required
def revoke_session(session_id):
    """Revoke specific session"""
    from models.user import UserSession
    
    session = UserSession.query.get_or_404(session_id)
    if session.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    session.is_active = False
    db.session.commit()
    
    return jsonify({'status': 'success'})

@security_bp.route('/audit-log', methods=['GET'])
@login_required
def audit_log():
    """Get security audit log"""
    logs = SecurityLog.query.filter_by(user_id=current_user.id)\
        .order_by(SecurityLog.created_at.desc()).limit(100).all()
    
    return jsonify([{
        'id': log.id,
        'event_type': log.event_type,
        'ip_address': log.ip_address,
        'user_agent': log.user_agent,
        'created_at': log.created_at.isoformat()
    } for log in logs])

@security_bp.route('/password-strength', methods=['POST'])
def check_password_strength():
    """Check password strength"""
    password = request.json.get('password')
    
    if not password:
        return jsonify({'error': 'Password required'}), 400
    
    strength = {
        'score': 0,
        'feedback': []
    }
    
    # Length check
    if len(password) >= 8:
        strength['score'] += 1
    else:
        strength['feedback'].append('Password should be at least 8 characters')
    
    # Uppercase check
    if any(c.isupper() for c in password):
        strength['score'] += 1
    else:
        strength['feedback'].append('Include at least one uppercase letter')
    
    # Lowercase check
    if any(c.islower() for c in password):
        strength['score'] += 1
    else:
        strength['feedback'].append('Include at least one lowercase letter')
    
    # Number check
    if any(c.isdigit() for c in password):
        strength['score'] += 1
    else:
        strength['feedback'].append('Include at least one number')
    
    # Special character check
    if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        strength['score'] += 1
    else:
        strength['feedback'].append('Include at least one special character')
    
    # Common password check
    common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
    if password.lower() in common_passwords:
        strength['score'] = 0
        strength['feedback'] = ['This is a common password']
    
    strength['is_strong'] = strength['score'] >= 4
    
    return jsonify(strength)

@security_bp.route('/device-management', methods=['GET', 'POST'])
@login_required
def device_management():
    """Manage trusted devices"""
    if request.method == 'POST':
        device_name = request.json.get('device_name')
        device_fingerprint = SecurityManager.generate_device_fingerprint()
        
        from models.user import TrustedDevice
        
        device = TrustedDevice(
            user_id=current_user.id,
            device_name=device_name,
            device_fingerprint=device_fingerprint,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        db.session.add(device)
        db.session.commit()
        
        return jsonify({'status': 'success'})
    
    # Get trusted devices
    from models.user import TrustedDevice
    
    devices = TrustedDevice.query.filter_by(user_id=current_user.id).all()
    
    return jsonify([{
        'id': d.id,
        'device_name': d.device_name,
        'last_used': d.last_used.isoformat(),
        'is_trusted': d.is_trusted
    } for d in devices])
