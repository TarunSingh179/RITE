#!/usr/bin/env python3
"""
Performance Optimization Script for RITE College Management System
This script creates database indexes and optimizations for handling 1000+ students.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseOptimizer:
    def __init__(self, postgres_url):
        self.postgres_url = postgres_url
        self.conn = None
        
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(self.postgres_url)
            self.conn.autocommit = False
            print("✅ Connected to PostgreSQL database")
            return True
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
            return False
    
    def create_indexes(self):
        """Create performance indexes for better query performance"""
        indexes = [
            # User table indexes
            "CREATE INDEX IF NOT EXISTS idx_user_username ON \"user\"(username);",
            "CREATE INDEX IF NOT EXISTS idx_user_email ON \"user\"(email);",
            "CREATE INDEX IF NOT EXISTS idx_user_role ON \"user\"(role);",
            "CREATE INDEX IF NOT EXISTS idx_user_is_active ON \"user\"(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_user_student_id ON \"user\"(student_id);",
            "CREATE INDEX IF NOT EXISTS idx_user_faculty_id ON \"user\"(faculty_id);",
            "CREATE INDEX IF NOT EXISTS idx_user_course_id ON \"user\"(course_id);",
            "CREATE INDEX IF NOT EXISTS idx_user_semester_id ON \"user\"(semester_id);",
            
            # Course and Semester indexes
            "CREATE INDEX IF NOT EXISTS idx_course_code ON course(code);",
            "CREATE INDEX IF NOT EXISTS idx_course_is_active ON course(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_semester_course_id ON semester(course_id);",
            "CREATE INDEX IF NOT EXISTS idx_semester_number ON semester(number);",
            
            # Subject indexes
            "CREATE INDEX IF NOT EXISTS idx_subject_code ON subject(code);",
            "CREATE INDEX IF NOT EXISTS idx_subject_semester_id ON subject(semester_id);",
            "CREATE INDEX IF NOT EXISTS idx_subject_faculty_id ON subject(faculty_id);",
            
            # Attendance indexes
            "CREATE INDEX IF NOT EXISTS idx_attendance_student_id ON attendance(student_id);",
            "CREATE INDEX IF NOT EXISTS idx_attendance_subject_id ON attendance(subject_id);",
            "CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);",
            "CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance(status);",
            "CREATE INDEX IF NOT EXISTS idx_attendance_marked_by ON attendance(marked_by);",
            "CREATE INDEX IF NOT EXISTS idx_attendance_created_at ON attendance(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_attendance_student_date ON attendance(student_id, date);",
            "CREATE INDEX IF NOT EXISTS idx_attendance_subject_date ON attendance(subject_id, date);",
            
            # Exam indexes
            "CREATE INDEX IF NOT EXISTS idx_exam_subject_id ON exam(subject_id);",
            "CREATE INDEX IF NOT EXISTS idx_exam_date ON exam(date);",
            "CREATE INDEX IF NOT EXISTS idx_exam_type ON exam(exam_type);",
            "CREATE INDEX IF NOT EXISTS idx_exam_is_active ON exam(is_active);",
            
            # ExamMark indexes
            "CREATE INDEX IF NOT EXISTS idx_exam_mark_exam_id ON exam_mark(exam_id);",
            "CREATE INDEX IF NOT EXISTS idx_exam_mark_student_id ON exam_mark(student_id);",
            "CREATE INDEX IF NOT EXISTS idx_exam_mark_graded_by ON exam_mark(graded_by);",
            "CREATE INDEX IF NOT EXISTS idx_exam_mark_graded_at ON exam_mark(graded_at);",
            
            # Assignment indexes
            "CREATE INDEX IF NOT EXISTS idx_assignment_subject_id ON assignment(subject_id);",
            "CREATE INDEX IF NOT EXISTS idx_assignment_faculty_id ON assignment(faculty_id);",
            "CREATE INDEX IF NOT EXISTS idx_assignment_due_date ON assignment(due_date);",
            "CREATE INDEX IF NOT EXISTS idx_assignment_is_active ON assignment(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_assignment_created_at ON assignment(created_at);",
            
            # AssignmentSubmission indexes
            "CREATE INDEX IF NOT EXISTS idx_assignment_submission_assignment_id ON assignment_submission(assignment_id);",
            "CREATE INDEX IF NOT EXISTS idx_assignment_submission_student_id ON assignment_submission(student_id);",
            "CREATE INDEX IF NOT EXISTS idx_assignment_submission_submitted_at ON assignment_submission(submitted_at);",
            
            # Fee indexes
            "CREATE INDEX IF NOT EXISTS idx_fee_student_id ON fee(student_id);",
            "CREATE INDEX IF NOT EXISTS idx_fee_status ON fee(status);",
            "CREATE INDEX IF NOT EXISTS idx_fee_due_date ON fee(due_date);",
            "CREATE INDEX IF NOT EXISTS idx_fee_fee_type ON fee(fee_type);",
            
            # Book indexes
            "CREATE INDEX IF NOT EXISTS idx_book_isbn ON book(isbn);",
            "CREATE INDEX IF NOT EXISTS idx_book_category ON book(category);",
            "CREATE INDEX IF NOT EXISTS idx_book_is_active ON book(is_active);",
            
            # BookIssue indexes
            "CREATE INDEX IF NOT EXISTS idx_book_issue_book_id ON book_issue(book_id);",
            "CREATE INDEX IF NOT EXISTS idx_book_issue_student_id ON book_issue(student_id);",
            "CREATE INDEX IF NOT EXISTS idx_book_issue_status ON book_issue(status);",
            "CREATE INDEX IF NOT EXISTS idx_book_issue_issue_date ON book_issue(issue_date);",
            "CREATE INDEX IF NOT EXISTS idx_book_issue_due_date ON book_issue(due_date);",
            
            # Event indexes
            "CREATE INDEX IF NOT EXISTS idx_event_event_date ON event(event_date);",
            "CREATE INDEX IF NOT EXISTS idx_event_category ON event(category);",
            "CREATE INDEX IF NOT EXISTS idx_event_is_active ON event(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_event_is_featured ON event(is_featured);",
            
            # Notification indexes
            "CREATE INDEX IF NOT EXISTS idx_notification_target_role ON notification(target_role);",
            "CREATE INDEX IF NOT EXISTS idx_notification_type ON notification(type);",
            "CREATE INDEX IF NOT EXISTS idx_notification_priority ON notification(priority);",
            "CREATE INDEX IF NOT EXISTS idx_notification_is_active ON notification(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_notification_created_at ON notification(created_at);",
            
            # Feedback indexes
            "CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);",
            "CREATE INDEX IF NOT EXISTS idx_feedback_feedback_type ON feedback(feedback_type);",
            "CREATE INDEX IF NOT EXISTS idx_feedback_priority ON feedback(priority);",
            "CREATE INDEX IF NOT EXISTS idx_feedback_submitted_by ON feedback(submitted_by);",
            "CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at);",
            
            # Contact indexes
            "CREATE INDEX IF NOT EXISTS idx_contact_status ON contact(status);",
            "CREATE INDEX IF NOT EXISTS idx_contact_contact_type ON contact(contact_type);",
            "CREATE INDEX IF NOT EXISTS idx_contact_created_at ON contact(created_at);"
        ]
        
        cursor = self.conn.cursor()
        successful_indexes = 0
        
        for i, index_sql in enumerate(indexes, 1):
            try:
                cursor.execute(index_sql)
                print(f"✅ Created index {i}/{len(indexes)}")
                successful_indexes += 1
            except Exception as e:
                print(f"⚠️  Index {i} failed: {e}")
        
        self.conn.commit()
        cursor.close()
        
        print(f"\n📊 Index Creation Summary:")
        print(f"   Total indexes: {len(indexes)}")
        print(f"   Successful: {successful_indexes}")
        print(f"   Failed: {len(indexes) - successful_indexes}")
        
        return successful_indexes == len(indexes)
    
    def create_partitions(self):
        """Create table partitions for large datasets"""
        partitions = [
            # Partition attendance table by date (monthly)
            """
            CREATE TABLE IF NOT EXISTS attendance_2024_01 PARTITION OF attendance
            FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
            """,
            """
            CREATE TABLE IF NOT EXISTS attendance_2024_02 PARTITION OF attendance
            FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
            """,
            """
            CREATE TABLE IF NOT EXISTS attendance_2024_03 PARTITION OF attendance
            FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');
            """
        ]
        
        cursor = self.conn.cursor()
        successful_partitions = 0
        
        for i, partition_sql in enumerate(partitions, 1):
            try:
                cursor.execute(partition_sql)
                print(f"✅ Created partition {i}/{len(partitions)}")
                successful_partitions += 1
            except Exception as e:
                print(f"⚠️  Partition {i} failed: {e}")
        
        self.conn.commit()
        cursor.close()
        
        return successful_partitions == len(partitions)
    
    def optimize_settings(self):
        """Optimize PostgreSQL settings for better performance"""
        settings = [
            "SET work_mem = '256MB';",
            "SET shared_buffers = '256MB';",
            "SET effective_cache_size = '1GB';",
            "SET maintenance_work_mem = '256MB';",
            "SET checkpoint_completion_target = 0.9;",
            "SET wal_buffers = '16MB';",
            "SET default_statistics_target = 100;",
            "SET random_page_cost = 1.1;",
            "SET effective_io_concurrency = 200;",
            "SET max_worker_processes = 8;",
            "SET max_parallel_workers_per_gather = 4;",
            "SET max_parallel_workers = 8;",
            "SET max_parallel_maintenance_workers = 4;"
        ]
        
        cursor = self.conn.cursor()
        successful_settings = 0
        
        for i, setting in enumerate(settings, 1):
            try:
                cursor.execute(setting)
                print(f"✅ Applied setting {i}/{len(settings)}")
                successful_settings += 1
            except Exception as e:
                print(f"⚠️  Setting {i} failed: {e}")
        
        self.conn.commit()
        cursor.close()
        
        return successful_settings == len(settings)
    
    def create_views(self):
        """Create useful views for common queries"""
        views = [
            # Student attendance summary view
            """
            CREATE OR REPLACE VIEW student_attendance_summary AS
            SELECT 
                u.id as student_id,
                u.first_name,
                u.last_name,
                u.student_id as student_code,
                COUNT(a.id) as total_classes,
                COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present_classes,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_classes,
                COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent_classes,
                ROUND(
                    (COUNT(CASE WHEN a.status IN ('present', 'late') THEN 1 END) * 100.0 / COUNT(a.id)), 2
                ) as attendance_percentage
            FROM "user" u
            LEFT JOIN attendance a ON u.id = a.student_id
            WHERE u.role = 'student'
            GROUP BY u.id, u.first_name, u.last_name, u.student_id;
            """,
            
            # Faculty performance view
            """
            CREATE OR REPLACE VIEW faculty_performance AS
            SELECT 
                u.id as faculty_id,
                u.first_name,
                u.last_name,
                u.faculty_id as faculty_code,
                COUNT(DISTINCT s.id) as total_subjects,
                COUNT(DISTINCT a.id) as total_assignments,
                COUNT(DISTINCT e.id) as total_exams,
                COUNT(DISTINCT att.student_id) as total_students_taught
            FROM "user" u
            LEFT JOIN subject s ON u.id = s.faculty_id
            LEFT JOIN assignment a ON u.id = a.faculty_id
            LEFT JOIN exam e ON s.id = e.subject_id
            LEFT JOIN attendance att ON s.id = att.subject_id
            WHERE u.role = 'faculty'
            GROUP BY u.id, u.first_name, u.last_name, u.faculty_id;
            """,
            
            # Course statistics view
            """
            CREATE OR REPLACE VIEW course_statistics AS
            SELECT 
                c.id as course_id,
                c.name as course_name,
                c.code as course_code,
                COUNT(DISTINCT u.id) as total_students,
                COUNT(DISTINCT s.id) as total_subjects,
                COUNT(DISTINCT sem.id) as total_semesters,
                AVG(att_summary.attendance_percentage) as avg_attendance_percentage
            FROM course c
            LEFT JOIN semester sem ON c.id = sem.course_id
            LEFT JOIN "user" u ON sem.id = u.semester_id
            LEFT JOIN subject s ON sem.id = s.semester_id
            LEFT JOIN student_attendance_summary att_summary ON u.id = att_summary.student_id
            WHERE c.is_active = true
            GROUP BY c.id, c.name, c.code;
            """
        ]
        
        cursor = self.conn.cursor()
        successful_views = 0
        
        for i, view_sql in enumerate(views, 1):
            try:
                cursor.execute(view_sql)
                print(f"✅ Created view {i}/{len(views)}")
                successful_views += 1
            except Exception as e:
                print(f"⚠️  View {i} failed: {e}")
        
        self.conn.commit()
        cursor.close()
        
        return successful_views == len(views)
    
    def analyze_tables(self):
        """Run ANALYZE on all tables to update statistics"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("ANALYZE;")
            self.conn.commit()
            cursor.close()
            print("✅ Updated table statistics")
            return True
        except Exception as e:
            print(f"❌ Error updating statistics: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("🔌 Database connection closed")

def main():
    """Main optimization function"""
    print("🚀 RITE College Management System - Database Performance Optimization")
    print("=" * 70)
    
    # Get PostgreSQL URL from environment
    postgres_url = os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URI')
    
    if not postgres_url:
        print("❌ Error: DATABASE_URL or SQLALCHEMY_DATABASE_URI environment variable is required")
        print("Example: DATABASE_URL=postgresql://user:password@localhost:5432/rite_db")
        return False
    
    print(f"🐘 PostgreSQL URL: {postgres_url.split('@')[0]}@***")
    
    # Create optimizer and run optimizations
    optimizer = DatabaseOptimizer(postgres_url)
    
    if not optimizer.connect():
        return False
    
    try:
        print("\n🔧 Running database optimizations...")
        
        # Create indexes
        print("\n📊 Creating database indexes...")
        indexes_success = optimizer.create_indexes()
        
        # Create partitions
        print("\n📦 Creating table partitions...")
        partitions_success = optimizer.create_partitions()
        
        # Create views
        print("\n👁️  Creating database views...")
        views_success = optimizer.create_views()
        
        # Optimize settings
        print("\n⚙️  Optimizing database settings...")
        settings_success = optimizer.optimize_settings()
        
        # Analyze tables
        print("\n📈 Updating table statistics...")
        analyze_success = optimizer.analyze_tables()
        
        print(f"\n📊 Optimization Summary:")
        print(f"   Indexes: {'✅' if indexes_success else '❌'}")
        print(f"   Partitions: {'✅' if partitions_success else '❌'}")
        print(f"   Views: {'✅' if views_success else '❌'}")
        print(f"   Settings: {'✅' if settings_success else '❌'}")
        print(f"   Statistics: {'✅' if analyze_success else '❌'}")
        
        overall_success = all([indexes_success, partitions_success, views_success, settings_success, analyze_success])
        
        if overall_success:
            print("\n🎉 Database optimization completed successfully!")
            print("✅ Your database is now optimized for 1000+ students")
        else:
            print("\n⚠️  Some optimizations failed. Check the error messages above.")
        
        return overall_success
        
    finally:
        optimizer.close()

if __name__ == "__main__":
    main() 