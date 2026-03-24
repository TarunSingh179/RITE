#!/usr/bin/env python3
"""
Simple PostgreSQL Database Initialization
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_postgres():
    """Setup PostgreSQL database and user"""
    print("🚀 Setting up PostgreSQL for RITE College Management System")
    print("=" * 60)
    
    # Get postgres password
    postgres_password = input("Enter PostgreSQL 'postgres' user password: ")
    
    try:
        # Connect to PostgreSQL as postgres user
        print("🔗 Connecting to PostgreSQL...")
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            database='postgres',
            user='postgres',
            password=postgres_password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create database
        print("📊 Creating database 'rite_db'...")
        try:
            cursor.execute("CREATE DATABASE rite_db")
            print("✅ Database 'rite_db' created")
        except psycopg2.errors.DuplicateDatabase:
            print("✅ Database 'rite_db' already exists")
        
        # Create user
        print("👤 Creating user 'rite_user'...")
        try:
            cursor.execute("CREATE USER rite_user WITH PASSWORD 'rite_password'")
            print("✅ User 'rite_user' created")
        except psycopg2.errors.DuplicateObject:
            print("✅ User 'rite_user' already exists")
        
        # Grant privileges on database
        print("🔐 Granting database privileges...")
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE rite_db TO rite_user")
        
        cursor.close()
        conn.close()
        
        # Connect to rite_db to grant schema privileges
        print("🔐 Granting schema privileges...")
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            database='rite_db',
            user='postgres',
            password=postgres_password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute("GRANT ALL ON SCHEMA public TO rite_user")
        cursor.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rite_user")
        cursor.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rite_user")
        cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO rite_user")
        cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO rite_user")
        
        cursor.close()
        conn.close()
        
        print("✅ PostgreSQL setup completed successfully!")
        
        # Test application connection
        print("\n🔗 Testing application connection...")
        app_conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        app_cursor = app_conn.cursor()
        app_cursor.execute("SELECT version();")
        version = app_cursor.fetchone()[0]
        app_cursor.close()
        app_conn.close()
        
        print("✅ Application connection successful!")
        print(f"📊 PostgreSQL Version: {version}")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    if setup_postgres():
        print("\n🎉 Database setup complete!")
        print("🚀 Now run: python app.py")
    else:
        print("\n❌ Setup failed!")
