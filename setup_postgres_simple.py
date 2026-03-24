#!/usr/bin/env python3
"""
Simple PostgreSQL Database Setup for RITE College Management System
This script attempts to connect and set up the database using existing credentials.
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def load_env_vars():
    """Load environment variables from .env file"""
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def test_connection():
    """Test connection to PostgreSQL with current credentials"""
    print("🔍 Testing PostgreSQL connection...")
    
    # Load environment variables
    load_env_vars()
    
    # Get database URL from environment
    db_url = os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URI')
    
    if not db_url:
        print("❌ No DATABASE_URL found in environment variables")
        return False
    
    try:
        # Parse the database URL
        if db_url.startswith('postgresql://'):
            # Extract connection details
            import urllib.parse as urlparse
            parsed = urlparse.urlparse(db_url)
            
            conn_params = {
                'host': parsed.hostname or 'localhost',
                'port': parsed.port or 5432,
                'user': parsed.username,
                'password': parsed.password,
                'database': parsed.path[1:] if parsed.path else 'postgres'  # Remove leading slash
            }
            
            print(f"🔗 Connecting to: {conn_params['user']}@{conn_params['host']}:{conn_params['port']}/{conn_params['database']}")
            
            # Try to connect
            conn = psycopg2.connect(**conn_params)
            conn.close()
            print("✅ Connection successful!")
            return True
            
    except psycopg2.OperationalError as e:
        if "database" in str(e) and "does not exist" in str(e):
            print("⚠️  Database doesn't exist, but connection to server is working")
            print("🔧 Attempting to create database...")
            return create_database_if_needed(conn_params)
        else:
            print(f"❌ Connection failed: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def create_database_if_needed(conn_params):
    """Create database if it doesn't exist"""
    try:
        # Connect to postgres database to create our target database
        temp_params = conn_params.copy()
        target_db = temp_params['database']
        temp_params['database'] = 'postgres'
        
        print(f"🔗 Connecting to postgres database to create '{target_db}'...")
        conn = psycopg2.connect(**temp_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (target_db,))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"📝 Creating database '{target_db}'...")
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target_db)))
            print(f"✅ Database '{target_db}' created successfully!")
        else:
            print(f"ℹ️  Database '{target_db}' already exists")
        
        cursor.close()
        conn.close()
        
        # Test connection to the target database
        conn = psycopg2.connect(**conn_params)
        conn.close()
        print("✅ Connection to target database successful!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False

def setup_flask_app():
    """Initialize Flask app with database"""
    print("🏗️  Setting up Flask application...")
    
    try:
        # Import Flask app setup
        from setup_database import initialize_schema
        
        if initialize_schema():
            print("✅ Flask application and database schema initialized!")
            return True
        else:
            print("❌ Failed to initialize Flask application")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up Flask app: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 RITE College Management System - PostgreSQL Setup")
    print("=" * 60)
    
    # Step 1: Test connection
    if not test_connection():
        print("\n❌ Setup failed - could not connect to PostgreSQL")
        print("\n💡 Troubleshooting tips:")
        print("   1. Make sure PostgreSQL service is running")
        print("   2. Check your .env file has correct DATABASE_URL")
        print("   3. Verify user credentials are correct")
        return False
    
    # Step 2: Setup Flask app and schema
    if setup_flask_app():
        print("\n🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Run 'python app.py' to start the application")
        print("   2. Visit http://localhost:5000 to access the system")
        return True
    else:
        print("\n❌ Setup partially completed - database connected but schema setup failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
