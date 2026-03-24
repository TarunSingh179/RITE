# PostgreSQL Setup Script for PowerShell
Write-Host "Setting up PostgreSQL for RITE College Management System..." -ForegroundColor Green

# Check if PostgreSQL is installed
try {
    $psqlPath = Get-Command psql -ErrorAction Stop
    Write-Host "✅ PostgreSQL found at: $($psqlPath.Source)" -ForegroundColor Green
} catch {
    Write-Host "❌ PostgreSQL not found. Please install PostgreSQL first:" -ForegroundColor Red
    Write-Host "   https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
    exit 1
}

# Set environment variables
$env:SQLITE_DB_PATH = "instance/college.db"
$env:DATABASE_URL = "postgresql://rite_user:rite_password@localhost:5432/rite_db"

# Create .env file
@"
# Database Configuration
DATABASE_URL=postgresql://rite_user:rite_password@localhost:5432/rite_db
SQLALCHEMY_DATABASE_URI=postgresql://rite_user:rite_password@localhost:5432/rite_db
"@ | Out-File -FilePath ".env" -Encoding UTF8

Write-Host "✅ Environment variables configured" -ForegroundColor Green

# Test connection
Write-Host "`nTesting PostgreSQL connection..." -ForegroundColor Yellow
python test_postgresql_connection.py

Write-Host "`nSetup complete! Run 'python migrate_to_postgresql.py' to start migration" -ForegroundColor Green
