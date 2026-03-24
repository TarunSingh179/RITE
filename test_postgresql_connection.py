#!/usr/bin/env python3
"""
Test script to verify PostgreSQL connection before migration
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_postgresql_connection():
    """Test PostgreSQL connection with various configurations"""
    
    # Test configurations
    test_configs = [
        {
            'host': 'localhost',
            'port': 5432,
            'database': 'rite_db',
            'user': 'rite_user',
            'password': 'rite_password'
        },
        {
            'host': 'localhost',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': 'postgres'
        }
    ]
    
    # Also test from environment variable
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        test_configs.append({'url': database_url})
    
    print("🔍 Testing PostgreSQL connections...")
    
    for i, config in enumerate(test_configs, 1):
        try:
            if 'url' in config:
                # Test with URL
                conn = psycopg2.connect(config['url'])
                print(f"✅ Test {i}: Connection successful with URL")
            else:
                # Test with individual parameters
                conn = psycopg2.connect(**config)
                print(f"✅ Test {i}: Connection successful with {config['user']}@{config['host']}:{config['port']}/{config['database']}")
            
            # Test basic query
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"   PostgreSQL Version: {version.split()[1]}")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Test {i}: Connection failed - {e}")
    
    return False

if __name__ == "__main__":
    test_postgresql_connection()
