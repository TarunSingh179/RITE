#!/usr/bin/env python3
"""
Script to delete a specific student from the database
Usage: python delete_student.py
"""

import os
from flask import Flask
from models.user import db, User
from models.exam import ExamMark
from models.attendance import Attendance
from config import Config, config

def delete_student_by_id(student_id):
    """Delete a student by their student_id"""
    
    # Create Flask app context
    app = Flask(__name__)
    
    # Configure app
    env = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[env])
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        try:
            # Find the user by student_id
            user = User.query.filter_by(student_id=student_id).first()
            
            if not user:
                print(f"❌ Student with student_id '{student_id}' not found.")
                return False
            
            print(f"📋 Found student: {user.get_full_name()} ({user.username})")
            print(f"   Role: {user.role}")
            print(f"   Email: {user.email}")
            print(f"   Student ID: {user.student_id}")
            print(f"   Course: {user.course.name if user.course else 'Not assigned'}")
            
            # Check for related data
            related_data = []
            
            # Check attendance records for this student
            attendance_records = Attendance.query.filter_by(student_id=user.id).all()
            if attendance_records:
                related_data.append(f"Attendance records: {len(attendance_records)}")
            
            # Check exam marks for this student
            exam_marks = ExamMark.query.filter_by(student_id=user.id).all()
            if exam_marks:
                related_data.append(f"Exam marks: {len(exam_marks)}")
            
            # Check assignments submitted
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
            
            if related_data:
                print(f"\n⚠️  Student has related data:")
                for data in related_data:
                    print(f"   - {data}")
                
                print(f"\nChoose deletion method:")
                print("1. Soft delete (deactivate student - preserves all academic records)")
                print("2. Hard delete (permanently remove student and all related data)")
                print("3. Cancel")
                
                choice = input("Enter choice (1/2/3): ").strip()
                
                if choice == '1':
                    # Soft delete - deactivate
                    user.is_active = False
                    db.session.commit()
                    print(f"✅ Student '{student_id}' has been deactivated (soft delete).")
                    print("   All academic records are preserved.")
                    return True
                    
                elif choice == '2':
                    # Hard delete - remove all related data first
                    print(f"\n🗑️  Performing hard delete for student '{student_id}'...")
                    
                    # Delete attendance records first (most critical)
                    if attendance_records:
                        for record in attendance_records:
                            db.session.delete(record)
                        print(f"   Deleted {len(attendance_records)} attendance records")
                    
                    # Delete exam marks
                    if exam_marks:
                        for mark in exam_marks:
                            db.session.delete(mark)
                        print(f"   Deleted {len(exam_marks)} exam marks")
                    
                    # Delete assignment submissions
                    if hasattr(user, 'assignments_submitted') and user.assignments_submitted:
                        submissions_count = len(user.assignments_submitted)
                        for submission in user.assignments_submitted:
                            db.session.delete(submission)
                        print(f"   Deleted {submissions_count} assignment submissions")
                    
                    # Delete book issues
                    if hasattr(user, 'books_issued') and user.books_issued:
                        books_count = len(user.books_issued)
                        for book_issue in user.books_issued:
                            db.session.delete(book_issue)
                        print(f"   Deleted {books_count} book issue records")
                    
                    # Delete fees
                    if hasattr(user, 'fees') and user.fees:
                        fees_count = len(user.fees)
                        for fee in user.fees:
                            db.session.delete(fee)
                        print(f"   Deleted {fees_count} fee records")
                    
                    # Delete results
                    if hasattr(user, 'results') and user.results:
                        results_count = len(user.results)
                        for result in user.results:
                            db.session.delete(result)
                        print(f"   Deleted {results_count} result records")
                    
                    # Finally delete the user
                    db.session.delete(user)
                    db.session.commit()
                    
                    print(f"✅ Student '{student_id}' has been permanently deleted from the database.")
                    print("   All related academic data has been removed.")
                    return True
                    
                elif choice == '3':
                    print("❌ Deletion cancelled.")
                    return False
                else:
                    print("❌ Invalid choice. Deletion cancelled.")
                    return False
            else:
                # No related data, safe to delete directly
                print(f"\n✅ No related data found. Safe to delete student '{student_id}'.")
                confirm = input("Proceed with deletion? (yes/no): ").lower().strip()
                
                if confirm in ['yes', 'y']:
                    db.session.delete(user)
                    db.session.commit()
                    print(f"✅ Student '{student_id}' has been successfully deleted.")
                    return True
                else:
                    print("❌ Deletion cancelled.")
                    return False
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error deleting student: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    student_id = "STU2024001"
    print(f"🗑️  Attempting to delete student: {student_id}")
    print("=" * 50)
    
    success = delete_student_by_id(student_id)
    
    if success:
        print("\n✅ Operation completed successfully!")
    else:
        print("\n❌ Operation failed or was cancelled.")
