#!/usr/bin/env python3
"""
Data Migration Script: SQLite to PostgreSQL
This script migrates data from SQLite to PostgreSQL for the RITE College Management System.
"""

import os
import sys
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DataMigrator:
    def __init__(self, sqlite_path, postgres_url):
        self.sqlite_path = sqlite_path
        self.postgres_url = postgres_url
        self.sqlite_conn = None
        self.postgres_conn = None
        
    def connect_databases(self):
        """Connect to both SQLite and PostgreSQL databases"""
        try:
            # Connect to SQLite
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            
            # Connect to PostgreSQL
            self.postgres_conn = psycopg2.connect(self.postgres_url)
            self.postgres_conn.autocommit = False
            
            print("✅ Successfully connected to both databases")
            return True
            
        except Exception as e:
            print(f"❌ Error connecting to databases: {e}")
            return False
    
    def get_sqlite_tables(self):
        """Get list of tables from SQLite database"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables
    
    def get_table_schema(self, table_name):
        """Get schema information for a table"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        cursor.close()
        return columns
    
    def migrate_table(self, table_name):
        """Migrate data from SQLite table to PostgreSQL"""
        try:
            # Get data from SQLite
            sqlite_cursor = self.sqlite_conn.cursor()
            sqlite_cursor.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"⚠️  Table {table_name} is empty, skipping...")
                return True
            
            # Get column names
            columns = [description[0] for description in sqlite_cursor.description]
            
            # Prepare PostgreSQL cursor
            postgres_cursor = self.postgres_conn.cursor()
            
            # Create placeholders for INSERT statement
            placeholders = ', '.join(['%s'] * len(columns))
            column_names = ', '.join(columns)
            
            # Insert data
            for row in rows:
                values = list(row)
                # Handle datetime objects
                for i, value in enumerate(values):
                    if isinstance(value, datetime):
                        values[i] = value.isoformat()
                    elif isinstance(value, dict):
                        values[i] = json.dumps(value)
                
                query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
                postgres_cursor.execute(query, values)
            
            # Commit the transaction
            self.postgres_conn.commit()
            print(f"✅ Migrated {len(rows)} rows from table '{table_name}'")
            return True
            
        except Exception as e:
            self.postgres_conn.rollback()
            print(f"❌ Error migrating table {table_name}: {e}")
            return False
        finally:
            sqlite_cursor.close()
    
    def verify_migration(self, table_name):
        """Verify that data was migrated correctly"""
        try:
            # Count rows in SQLite
            sqlite_cursor = self.sqlite_conn.cursor()
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            sqlite_count = sqlite_cursor.fetchone()[0]
            sqlite_cursor.close()
            
            # Count rows in PostgreSQL
            postgres_cursor = self.postgres_conn.cursor()
            postgres_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            postgres_count = postgres_cursor.fetchone()[0]
            postgres_cursor.close()
            
            if sqlite_count == postgres_count:
                print(f"✅ Verification passed for {table_name}: {sqlite_count} rows")
                return True
            else:
                print(f"❌ Verification failed for {table_name}: SQLite={sqlite_count}, PostgreSQL={postgres_count}")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying table {table_name}: {e}")
            return False
    
    def migrate_all_data(self):
        """Migrate all data from SQLite to PostgreSQL"""
        if not self.connect_databases():
            return False
        
        try:
            tables = self.get_sqlite_tables()
            print(f"📋 Found {len(tables)} tables to migrate: {', '.join(tables)}")
            
            successful_migrations = 0
            total_tables = len(tables)
            
            for table_name in tables:
                print(f"\n🔄 Migrating table: {table_name}")
                
                if self.migrate_table(table_name):
                    if self.verify_migration(table_name):
                        successful_migrations += 1
                    else:
                        print(f"⚠️  Migration verification failed for {table_name}")
                else:
                    print(f"❌ Migration failed for {table_name}")
            
            print(f"\n📊 Migration Summary:")
            print(f"   Total tables: {total_tables}")
            print(f"   Successful migrations: {successful_migrations}")
            print(f"   Failed migrations: {total_tables - successful_migrations}")
            
            return successful_migrations == total_tables
            
        finally:
            self.close_connections()
    
    def close_connections(self):
        """Close database connections"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.postgres_conn:
            self.postgres_conn.close()
        print("🔌 Database connections closed")

def main():
    """Main migration function"""
    print("🚀 RITE College Management System - SQLite to PostgreSQL Migration")
    print("=" * 70)
    
    # Configuration
    sqlite_path = os.environ.get('SQLITE_DB_PATH', 'college.db')
    postgres_url = os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URI')
    
    if not postgres_url:
        print("❌ Error: DATABASE_URL or SQLALCHEMY_DATABASE_URI environment variable is required")
        print("Example: DATABASE_URL=postgresql://user:password@localhost:5432/rite_db")
        sys.exit(1)
    
    if not os.path.exists(sqlite_path):
        print(f"❌ Error: SQLite database file not found: {sqlite_path}")
        sys.exit(1)
    
    print(f"📁 SQLite database: {sqlite_path}")
    print(f"🐘 PostgreSQL URL: {postgres_url.split('@')[0]}@***")
    
    # Confirm migration
    response = input("\n⚠️  This will migrate all data from SQLite to PostgreSQL. Continue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Migration cancelled")
        sys.exit(0)
    
    # Create migrator and run migration
    migrator = DataMigrator(sqlite_path, postgres_url)
    
    if migrator.migrate_all_data():
        print("\n🎉 Migration completed successfully!")
        print("✅ All data has been transferred to PostgreSQL")
        print("✅ You can now update your application to use PostgreSQL")
    else:
        print("\n❌ Migration failed!")
        print("⚠️  Please check the error messages above and try again")
        sys.exit(1)

if __name__ == "__main__":
    main()
