import razorpay
import uuid
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models.fee import Fee, PaymentTransaction
from models import db

payment_bp = Blueprint('payment', __name__, url_prefix='/payment')

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(os.getenv('RAZORPAY_KEY_ID'), os.getenv('RAZORPAY_KEY_SECRET')))

@payment_bp.route('/initiate', methods=['POST'])
@login_required
def initiate_payment():
    """Initiate payment for a fee"""
    fee_id = request.json.get('fee_id')
    amount = request.json.get('amount')
    
    if not fee_id or not amount:
        return jsonify({'error': 'Fee ID and amount required'}), 400
    
    fee = Fee.query.get_or_404(fee_id)
    
    if fee.student_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Create Razorpay order
    order_data = {
        'amount': int(amount * 100),  # Convert to paise
        'currency': 'INR',
        'receipt': f"fee_{fee_id}_{uuid.uuid4().hex[:8]}",
        'payment_capture': 1
    }
    
    try:
        order = razorpay_client.order.create(order_data)
        
        # Create payment transaction record
        transaction = PaymentTransaction(
            fee_id=fee_id,
            amount=amount,
            order_id=order['id'],
            status='pending',
            payment_method='razorpay',
            created_at=datetime.utcnow()
        )
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'order_id': order['id'],
            'amount': amount,
            'key': os.getenv('RAZORPAY_KEY_ID'),
            'name': f"{current_user.first_name} {current_user.last_name}",
            'email': current_user.email,
            'contact': current_user.phone or ''
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/verify', methods=['POST'])
@login_required
def verify_payment():
    """Verify payment after successful transaction"""
    payment_id = request.json.get('payment_id')
    order_id = request.json.get('order_id')
    signature = request.json.get('signature')
    
    try:
        # Verify payment signature
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })
        
        # Update transaction
        transaction = PaymentTransaction.query.filter_by(order_id=order_id).first()
        if transaction:
            transaction.payment_id = payment_id
            transaction.status = 'completed'
            transaction.completed_at = datetime.utcnow()
            
            # Update fee status
            fee = Fee.query.get(transaction.fee_id)
            fee.paid_amount += transaction.amount
            fee.status = 'paid'
            fee.paid_date = datetime.utcnow()
            fee.transaction_id = transaction.order_id
            
            db.session.commit()
            
            return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid payment'}), 400

@payment_bp.route('/refund', methods=['POST'])
@login_required
def refund_payment():
    """Process refund for a payment"""
    transaction_id = request.json.get('transaction_id')
    amount = request.json.get('amount')
    
    transaction = PaymentTransaction.query.get_or_404(transaction_id)
    
    if transaction.fee.student_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        refund = razorpay_client.payment.refund(
            transaction.payment_id,
            {'amount': int(amount * 100)}
        )
        
        # Update transaction
        transaction.status = 'refunded'
        transaction.refund_id = refund['id']
        transaction.refunded_at = datetime.utcnow()
        
        # Update fee
        fee = Fee.query.get(transaction.fee_id)
        fee.paid_amount -= amount
        
        db.session.commit()
        
        return jsonify({'status': 'refunded', 'refund_id': refund['id']})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/history', methods=['GET'])
@login_required
def payment_history():
    """Get payment history for current user"""
    transactions = PaymentTransaction.query.join(Fee).filter(
        Fee.student_id == current_user.id
    ).order_by(PaymentTransaction.created_at.desc()).all()
    
    return jsonify([{
        'id': t.id,
        'amount': t.amount,
        'status': t.status,
        'payment_method': t.payment_method,
        'created_at': t.created_at.isoformat(),
        'fee_type': t.fee.fee_type
    } for t in transactions])
