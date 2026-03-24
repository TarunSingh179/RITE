#!/usr/bin/env python3
"""
Database Setup Script for RITE College Management System
This script sets up PostgreSQL database and initializes the schema.
"""

import os
import sys
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
from flask import Flask
from config import config

# Load environment variables
load_dotenv()

def check_postgres_service():
    """Check if PostgreSQL service is running"""
    try:
        result = subprocess.run(['sc', 'query', 'postgresql-x64-17'], 
                              capture_output=True, text=True, shell=True)
        if 'RUNNING' in result.stdout:
            print("✅ PostgreSQL service is running")
            return True
        else:
            print("❌ PostgreSQL service is not running")
            print("💡 Start PostgreSQL service with: net start postgresql-x64-17")
            return False
    except Exception as e:
        print(f"⚠️  Could not check PostgreSQL service status: {e}")
        return True  # Assume it's running and let connection test handle it

def create_database_and_user():
    """Create database and user if they don't exist"""
    try:
        # Connect to PostgreSQL as postgres user (default database)
        print("🔗 Connecting to PostgreSQL as postgres user...")
        
        # Try connecting to postgres database first
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            database='postgres',
            user='postgres',
            password=input("Enter PostgreSQL postgres user password: ")
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='rite_db'")
        if not cursor.fetchone():
            print("📊 Creating database 'rite_db'...")
            cursor.execute("CREATE DATABASE rite_db")
            print("✅ Database 'rite_db' created successfully")
        else:
            print("✅ Database 'rite_db' already exists")
        
        # Check if user exists
        cursor.execute("SELECT 1 FROM pg_user WHERE usename='rite_user'")
        if not cursor.fetchone():
            print("👤 Creating user 'rite_user'...")
            cursor.execute("CREATE USER rite_user WITH PASSWORD 'rite_password'")
            print("✅ User 'rite_user' created successfully")
        else:
            print("✅ User 'rite_user' already exists")
        
        # Grant privileges
        print("🔐 Granting privileges...")
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE rite_db TO rite_user")
        
        # Connect to the new database to grant schema privileges
        cursor.close()
        conn.close()
        
        # Connect to rite_db to grant schema privileges
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            database='rite_db',
            user='postgres',
            password=input("Enter PostgreSQL postgres user password again: ")
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute("GRANT ALL ON SCHEMA public TO rite_user")
        cursor.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rite_user")
        cursor.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rite_user")
        
        cursor.close()
        conn.close()
        
        print("✅ All privileges granted successfully")
        return True
        
    except psycopg2.OperationalError as e:
        if "authentication failed" in str(e):
            print("❌ Authentication failed for postgres user")
            print("💡 Make sure you have the correct password for postgres user")
        else:
            print(f"❌ Database setup failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during database setup: {e}")
        return False

def test_app_connection():
    """Test connection with application credentials"""
    try:
        database_url = os.getenv('DATABASE_URL')
        print(f"🔗 Testing application connection...")
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print("✅ Application can connect to PostgreSQL successfully!")
        print(f"📊 PostgreSQL Version: {version}")
        return True
        
    except Exception as e:
        print(f"❌ Application connection failed: {e}")
        return False

def initialize_schema():
    """Initialize database schema using Flask-SQLAlchemy"""
    try:
        print("🏗️  Initializing database schema...")
        
        # Create Flask app
        app = Flask(__name__)
        env = os.environ.get('FLASK_ENV', 'development')
        app.config.from_object(config[env])
        
        # Import all models
        from models.user import db
        from models import (
            User, Course, Semester, Subject, Assignment, AssignmentSubmission,
            Book, BookIssue, Event, Fee, Result, Attendance, AttendanceReport,
            Exam, ExamMark, Notification, NotificationRecipient, Feedback, Contact
        )
        
        # Initialize database
        db.init_app(app)
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database schema initialized successfully!")
            
            # Print created tables
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Created {len(tables)} tables: {', '.join(tables)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Schema initialization failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 RITE College Management System - PostgreSQL Database Setup")
    print("=" * 70)
    
    # Step 1: Check PostgreSQL service
    if not check_postgres_service():
        print("\n❌ Please start PostgreSQL service and try again")
        return False
    
    # Step 2: Create database and user
    print("\n📊 Setting up database and user...")
    if not create_database_and_user():
        print("\n❌ Database setup failed")
        return False
    
    # Step 3: Test application connection
    print("\n🔗 Testing application connection...")
    if not test_app_connection():
        print("\n❌ Application connection test failed")
        return False
    
    # Step 4: Initialize schema
    print("\n🏗️  Initializing database schema...")
    if not initialize_schema():
        print("\n❌ Schema initialization failed")
        return False
    
    print("\n🎉 Database setup completed successfully!")
    print("✅ PostgreSQL database is ready for use")
    print("✅ You can now run your Flask application")
    
    return True

if __name__ == "__main__":
    if main():
        print("\n🚀 Ready to start your application with: python app.py")
    else:
        print("\n❌ Setup failed. Please check the errors above and try again.")
        sys.exit(1)
