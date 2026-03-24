@echo off
echo Setting up PostgreSQL for RITE College Management System...
echo.

REM Check if PostgreSQL is installed
where psql >nul 2>nul
if %errorlevel% neq 0 (
    echo PostgreSQL is not installed or not in PATH
    echo Please install PostgreSQL first from https://www.postgresql.org/download/windows/
    pause
    exit /b 1
)

REM Create database and user
echo Creating database 'rite_db'...
psql -U postgres -c "CREATE DATABASE rite_db;"
if %errorlevel% neq 0 (
    echo Failed to create database
    pause
    exit /b 1
)

echo Creating user 'rite_user'...
psql -U postgres -c "CREATE USER rite_user WITH PASSWORD 'rite_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE rite_db TO rite_user;"

echo.
echo PostgreSQL setup completed!
echo Database: rite_db
echo User: rite_user
echo Password: rite_password
echo.
echo Update your environment variables:
echo DATABASE_URL=postgresql://rite_user:rite_password@localhost:5432/rite_db
pause
