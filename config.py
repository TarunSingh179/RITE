import os
from datetime import timedelta

class Config:
    # Basic Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Database Configuration
    # PostgreSQL Configuration with fallback to SQLite for development
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        # Heroku style URL - convert to postgresql://
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///college.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PostgreSQL specific settings for performance
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 20)),
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),
        'echo': os.environ.get('DB_ECHO', 'false').lower() == 'true'
    }
    
    # File upload settings
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Pagination
    POSTS_PER_PAGE = int(os.environ.get('POSTS_PER_PAGE', 10))
    
    # Security settings
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Performance settings
    COMPRESS_MIMETYPES = ['text/html', 'text/css', 'text/xml', 'application/json', 'application/javascript']
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500

class DevelopmentConfig(Config):
    DEBUG = True
    # Use PostgreSQL for development, fallback to SQLite only if PostgreSQL is not available
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DEV_DATABASE_URL') or 
        os.environ.get('DATABASE_URL') or 
        os.environ.get('SQLALCHEMY_DATABASE_URI') or 
        'postgresql://rite_user:rite_password@localhost:5432/rite_db'
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        'echo': True,
        'pool_size': 5,
        'pool_timeout': 10,
        'pool_recycle': 300
    }

class ProductionConfig(Config):
    DEBUG = False
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Production performance settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 20)),
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 1800)),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 30)),
        'echo': False
    }
    
    def __init__(self):
        super().__init__()
        # Check for required environment variables at runtime
        if not self.SQLALCHEMY_DATABASE_URI:
            raise ValueError("DATABASE_URL environment variable is required for production")

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 