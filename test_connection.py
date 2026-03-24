#!/usr/bin/env python3
"""
Test PostgreSQL Connection
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_postgres_connection():
    """Test connection to PostgreSQL database"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL environment variable not found")
            return False
            
        print(f"🔗 Attempting to connect to: {database_url.split('@')[0]}@***")
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Successfully connected to PostgreSQL!")
        print(f"📊 PostgreSQL Version: {version}")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        if "database" in str(e) and "does not exist" in str(e):
            print("❌ Database 'rite_db' does not exist")
            print("💡 Please create the database first:")
            print("   psql -U postgres -c \"CREATE DATABASE rite_db;\"")
        elif "authentication failed" in str(e):
            print("❌ Authentication failed")
            print("💡 Please create the user first:")
            print("   psql -U postgres -c \"CREATE USER rite_user WITH PASSWORD 'rite_password';\"")
            print("   psql -U postgres -c \"GRANT ALL PRIVILEGES ON DATABASE rite_db TO rite_user;\"")
        else:
            print(f"❌ Connection failed: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing PostgreSQL Connection...")
    print("=" * 50)
    test_postgres_connection()
