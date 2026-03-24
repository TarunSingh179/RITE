# RITE College Management System - PostgreSQL Migration Guide

## Overview
This guide will help you migrate your SQLite database to PostgreSQL for the RITE College Management System.

## Prerequisites
- PostgreSQL 12+ installed on your system
- Python 3.8+ with virtual environment
- Access to your current SQLite database (`instance/college.db`)

## Step 1: Install PostgreSQL

### Option A: Using PostgreSQL Installer (Recommended)
1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Run the installer with these settings:
   - Port: 5432
   - Superuser: postgres
   - Password: postgres
   - Default database: postgres

### Option B: Using Chocolatey (if installed)
```bash
choco install postgresql
```

## Step 2: Create Database and User

After installation, open **pgAdmin** or **Command Prompt** and run:

```sql
-- Create database
CREATE DATABASE rite_db;

-- Create user
CREATE USER rite_user WITH PASSWORD 'rite_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE rite_db TO rite_user;
```

## Step 3: Configure Environment Variables

Create a `.env` file in your project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://rite_user:rite_password@localhost:5432/rite_db
SQLALCHEMY_DATABASE_URI=postgresql://rite_user:rite_password@localhost:5432/rite_db

# Optional: For development
DEV_DATABASE_URL=postgresql://rite_user:rite_password@localhost:5432/rite_db
```

## Step 4: Install Required Python Packages

```bash
pip install psycopg2-binary
```

## Step 5: Test PostgreSQL Connection

Run this test script:

```python
import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="rite_db",
        user="rite_user",
        password="rite_password"
    )
    print("✅ PostgreSQL connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

## Step 6: Run Migration

```bash
# Set environment variable
set DATABASE_URL=postgresql://rite_user:rite_password@localhost:5432/rite_db

# Run migration
python migrate_to_postgresql.py
```

## Step 7: Update Application Configuration

Update your `config.py` or environment variables to use PostgreSQL:

```python
# In config.py
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://rite_user:rite_password@localhost:5432/rite_db'
```

## Step 8: Verify Migration

1. Check if all tables were created in PostgreSQL
2. Verify data integrity
3. Test application functionality

## Troubleshooting

### Common Issues and Solutions

1. **Connection refused**
   - Ensure PostgreSQL service is running
   - Check firewall settings
   - Verify port 5432 is open

2. **Authentication failed**
   - Check username and password
   - Ensure user has proper privileges

3. **Database not found**
   - Create the database manually
   - Verify database name spelling

4. **psycopg2 not found**
   - Install with: `pip install psycopg2-binary`

### Testing Commands

```bash
# Check PostgreSQL service status
net start postgresql-x64-13

# Connect to database
psql -U rite_user -d rite_db -h localhost -p 5432

# List tables
\dt

# Count rows in a table
SELECT COUNT(*) FROM users;
```

## Rollback Plan

If migration fails, you can always revert to SQLite by:
1. Changing `SQLALCHEMY_DATABASE_URI` back to SQLite
2. Restoring from backup if needed
3. Your original SQLite database remains untouched

## Support

If you encounter issues:
1. Check PostgreSQL logs: `C:\Program Files\PostgreSQL\13\data\log\`
2. Verify connection with test script
3. Ensure all environment variables are set correctly
