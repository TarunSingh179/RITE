#!/usr/bin/env python3
"""
Script to deactivate a specific faculty user
Usage: python deactivate_user.py
"""

import os
from flask import Flask
from models.user import db, User
from config import Config, config

def deactivate_faculty_user(faculty_id):
    """Deactivate a faculty user by their faculty_id"""
    
    # Create Flask app context
    app = Flask(__name__)
    
    # Configure app
    env = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[env])
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        try:
            # Find the user by faculty_id
            user = User.query.filter_by(faculty_id=faculty_id).first()
            
            if not user:
                print(f"❌ User with faculty_id '{faculty_id}' not found.")
                return False
            
            if not user.is_active:
                print(f"ℹ️  User '{faculty_id}' is already deactivated.")
                return True
            
            print(f"📋 Found user: {user.get_full_name()} ({user.username})")
            print(f"   Role: {user.role}")
            print(f"   Email: {user.email}")
            print(f"   Faculty ID: {user.faculty_id}")
            print(f"   Current Status: {'Active' if user.is_active else 'Inactive'}")
            
            # Deactivate the user
            user.is_active = False
            db.session.commit()
            
            print(f"\n✅ User '{faculty_id}' has been successfully deactivated.")
            print("   - The user can no longer log in")
            print("   - All historical data is preserved")
            print("   - Exam marks and other records remain intact")
            print("   - The account can be reactivated later if needed")
            
            return True
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error deactivating user: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    faculty_id = "FAC2024001"
    print(f"🔄 Deactivating faculty user: {faculty_id}")
    print("=" * 50)
    
    success = deactivate_faculty_user(faculty_id)
    
    if success:
        print("\n✅ Operation completed successfully!")
        print("\nNote: This is a 'soft delete' - the user account is deactivated")
        print("but all data relationships are preserved. This is the recommended")
        print("approach when a user has associated data in the system.")
    else:
        print("\n❌ Operation failed.")
