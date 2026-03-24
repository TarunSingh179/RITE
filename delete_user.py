#!/usr/bin/env python3
"""
Script to delete a specific user from the database
Usage: python delete_user.py
"""

import os
import sys
from flask import Flask
from models.user import db, User
from models.exam import ExamMark
from config import Config, config

def delete_user_by_faculty_id(faculty_id):
    """Delete a user by their faculty_id"""
    
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
            
            print(f"📋 Found user: {user.get_full_name()} ({user.username})")
            print(f"   Role: {user.role}")
            print(f"   Email: {user.email}")
            print(f"   Faculty ID: {user.faculty_id}")
            
            # Check for related data that might prevent deletion
            related_data = []
            
            # Check exam marks graded by this faculty
            graded_marks = ExamMark.query.filter_by(graded_by=user.id).all()
            if graded_marks:
                related_data.append(f"Exam marks graded: {len(graded_marks)}")
            
            # Check assignments submitted (if student)
            if hasattr(user, 'assignments_submitted') and user.assignments_submitted:
                related_data.append(f"Assignment submissions: {len(user.assignments_submitted)}")
            
            # Check books issued
            if hasattr(user, 'books_issued') and user.books_issued:
                related_data.append(f"Books issued: {len(user.books_issued)}")
            
            # Check fees
            if hasattr(user, 'fees') and user.fees:
                related_data.append(f"Fee records: {len(user.fees)}")
            
            # Check results
            if hasattr(user, 'results') and user.results:
                related_data.append(f"Result records: {len(user.results)}")
            
            print(f"\n⚠️  User has related data:")
            for data in related_data:
                print(f"   - {data}")
            
            # Confirm deletion
            confirm = input(f"\n⚠️  Are you sure you want to delete this user? (yes/no): ").lower().strip()
            
            if confirm in ['yes', 'y']:
                if related_data:
                    choice = input("\nChoose action:\n1. Soft delete (deactivate user - RECOMMENDED)\n2. Transfer data and delete\n3. Cancel\nEnter choice (1/2/3): ").strip()
                    
                    if choice == '1':
                        # Soft delete - just deactivate
                        user.is_active = False
                        db.session.commit()
                        print(f"✅ User '{faculty_id}' has been deactivated (soft delete).")
                        print("   The user account is now inactive but all data is preserved.")
                        return True
                        
                    elif choice == '2':
                        # Transfer graded marks to admin or another faculty
                        if graded_marks:
                            print(f"\n📝 Found {len(graded_marks)} exam marks graded by this faculty.")
                            
                            # Find an admin user to transfer ownership to
                            admin_user = User.query.filter_by(role='admin', is_active=True).first()
                            if admin_user:
                                print(f"   Transferring graded marks to admin: {admin_user.get_full_name()}")
                                for mark in graded_marks:
                                    mark.graded_by = admin_user.id
                                    mark.remarks = f"[Transferred from {user.get_full_name()}] " + (mark.remarks or "")
                                
                                db.session.commit()
                                print(f"   ✅ Transferred {len(graded_marks)} exam marks to admin.")
                            else:
                                print("   ❌ No admin user found to transfer data to. Cannot proceed with deletion.")
                                return False
                        
                        # Now try to delete the user
                        db.session.delete(user)
                        db.session.commit()
                        print(f"✅ User '{faculty_id}' has been permanently deleted.")
                        print("   All graded exam marks have been transferred to admin.")
                        return True
                    else:
                        print("❌ Deletion cancelled.")
                        return False
                else:
                    # No related data, safe to delete
                    db.session.delete(user)
                    db.session.commit()
                    print(f"✅ User '{faculty_id}' has been successfully deleted.")
                    return True
            else:
                print("❌ Deletion cancelled.")
                return False
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error deleting user: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    faculty_id = "FAC2024001"
    print(f"🔍 Attempting to delete user with faculty_id: {faculty_id}")
    print("=" * 50)
    
    success = delete_user_by_faculty_id(faculty_id)
    
    if success:
        print("\n✅ Operation completed successfully!")
    else:
        print("\n❌ Operation failed or was cancelled.")
