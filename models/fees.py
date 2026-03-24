from datetime import datetime
from typing import Optional
from flask_sqlalchemy import SQLAlchemy

from .user import db  # reuse the shared SQLAlchemy instance


class LateFeeRule(db.Model):
    __tablename__ = 'late_fee_rule'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rule_type = db.Column(db.String(20), nullable=False, default='fixed_per_day')  # fixed_per_day | percent_per_day | slabbed
    grace_days = db.Column(db.Integer, default=0)
    per_day_amount = db.Column(db.Float)  # for fixed_per_day
    per_day_percent = db.Column(db.Float)  # for percent_per_day
    slabs = db.Column(db.Text)  # JSON text if needed for slabbed
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FeeStructure(db.Model):
    __tablename__ = 'fee_structure'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'))
    category = db.Column(db.String(50))  # SC/ST/OBC/General/EWS/etc
    tuition = db.Column(db.Float, default=0.0)
    hostel = db.Column(db.Float, default=0.0)
    transport = db.Column(db.Float, default=0.0)
    exam = db.Column(db.Float, default=0.0)
    misc = db.Column(db.Float, default=0.0)
    effective_from = db.Column(db.Date)
    effective_to = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    late_fee_rule_id = db.Column(db.Integer, db.ForeignKey('late_fee_rule.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ScholarshipRule(db.Model):
    __tablename__ = 'scholarship_rule'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    scope = db.Column(db.String(50), default='category')  # category | user | department | course | semester
    category = db.Column(db.String(50))  # when scope=category
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # when scope=user
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'))
    department_id = db.Column(db.Integer)  # optional if using departments later
    rule_type = db.Column(db.String(20), default='percent')  # percent | fixed
    percent = db.Column(db.Float)
    amount = db.Column(db.Float)
    is_cumulative = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ConcessionRule(db.Model):
    __tablename__ = 'concession_rule'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    scope = db.Column(db.String(50), default='category')
    category = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'))
    department_id = db.Column(db.Integer)
    rule_type = db.Column(db.String(20), default='percent')
    percent = db.Column(db.Float)
    amount = db.Column(db.Float)
    is_cumulative = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Payment(db.Model):
    __tablename__ = 'payment'
    id = db.Column(db.Integer, primary_key=True)
    fee_id = db.Column(db.Integer, db.ForeignKey('fee.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(30))  # UPI/Card/NetBanking/Wallet/Cash/Cheque
    txn_id = db.Column(db.String(100))
    receipt_number = db.Column(db.String(50))
    status = db.Column(db.String(20), default='completed')  # completed/pending/failed/refunded
    meta = db.Column(db.Text)  # JSON string if needed
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)  # e.g., create_fee, update_fee, record_payment, delete_fee
    entity = db.Column(db.String(50), nullable=False)  # Fee, Payment, FeeStructure
    entity_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    details = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
