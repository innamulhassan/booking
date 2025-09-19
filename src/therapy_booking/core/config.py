"""
Core Configuration Management

Handles all application configuration using environment variables
"""

import os
from typing import List, Optional
from pathlib import Path
from functools import lru_cache

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Settings:
    """
    Application settings loaded from environment variables
    """
    
    def __init__(self):
        # Application settings
        self.app_name: str = os.getenv("APP_NAME", "Therapy Booking System")
        self.version: str = os.getenv("VERSION", "2.0.0")
        self.environment: str = os.getenv("ENVIRONMENT", "development")
        self.debug: bool = os.getenv("DEBUG", "True").lower() == "true"
        
        # Server settings
        self.server_host: str = os.getenv("SERVER_HOST", "localhost")
        self.server_port: int = int(os.getenv("SERVER_PORT", "8000"))
        
        # Security settings
        self.secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        
        # CORS settings
        cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")
        self.cors_origins: List[str] = [origin.strip() for origin in cors_origins_str.split(",")]
        
        # Database settings
        self.database_url: str = os.getenv("DATABASE_URL", "mysql+pymysql://user:password@localhost/therapy_booking")
        self.database_pool_size: int = int(os.getenv("DATABASE_POOL_SIZE", "5"))
        self.database_max_overflow: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
        
        # Database components (for backward compatibility)
        self.db_host: str = os.getenv("DB_HOST", "localhost")
        self.db_port: int = int(os.getenv("DB_PORT", "3306"))
        self.db_name: str = os.getenv("DB_NAME", "booking")
        self.db_user: str = os.getenv("DB_USER", "root")
        self.db_password: str = os.getenv("DB_PASSWORD", "")
        
        # Construct database URL if not provided
        if self.database_url == "mysql+pymysql://user:password@localhost/therapy_booking":
            # URL encode the password to handle special characters
            import urllib.parse
            encoded_password = urllib.parse.quote_plus(self.db_password)
            self.database_url = f"mysql+pymysql://{self.db_user}:{encoded_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        
        # Google ADK settings
        self.google_adk_project_id: str = os.getenv("GOOGLE_ADK_PROJECT_ID", "")
        self.google_adk_agent_id: str = os.getenv("GOOGLE_ADK_AGENT_ID", "")
        self.google_application_credentials: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-pro")
        self.google_genai_model: str = os.getenv("ADK_MODEL_NAME", "gemini-1.5-pro-002")
        
        # ADK settings (for compatibility)
        self.adk_project_id: str = os.getenv("ADK_PROJECT_ID", "therapy_booking_agent")
        self.adk_model_name: str = os.getenv("ADK_MODEL_NAME", "gemini-1.5-pro-002")
        self.adk_session_timeout: int = int(os.getenv("ADK_SESSION_TIMEOUT", "3600"))
        
        # WhatsApp/Messaging settings
        self.whatsapp_token: str = os.getenv("WHATSAPP_TOKEN", "")
        self.whatsapp_phone_number_id: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        self.whatsapp_verify_token: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "therapy_booking_webhook")
        
        # UltraMsg settings
        self.ultramsg_token: str = os.getenv("ULTRAMSG_TOKEN", "")
        self.ultramsg_instance_id: str = os.getenv("ULTRAMSG_INSTANCE_ID", "")
        self.ultramsg_base_url: str = os.getenv("ULTRAMSG_BASE_URL", "https://api.ultramsg.com")
        
        # Twilio settings (alternative)
        self.twilio_account_sid: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER")
        
        # Business/Coordinator settings
        self.coordinator_phone_number: str = os.getenv("COORDINATOR_PHONE_NUMBER", "+97471669569")
        self.therapist_name: str = os.getenv("THERAPIST_NAME", "Dr. Sarah Smith")
        self.clinic_name: str = os.getenv("BUSINESS_NAME", "Therapy Booking Services")
        self.clinic_address: str = os.getenv("CLINIC_ADDRESS", "Doha, Qatar")
        self.business_hours: str = os.getenv("BUSINESS_HOURS", "9:00 AM - 6:00 PM")
        self.timezone: str = os.getenv("TIMEZONE", "Asia/Qatar")
        self.emergency_contact: str = os.getenv("EMERGENCY_CONTACT", "+974-7777-7777")
        
        # Agent settings
        self.agent_phone_number: str = os.getenv("AGENT_PHONE_NUMBER", "+97451334514")
        self.testclient_phone_number: str = os.getenv("TESTCLIENT_PHONE_NUMBER", "+917401290081")
        
        # Tunnel/Webhook settings
        self.tunnel_name: str = os.getenv("TUNNEL_NAME", "therapy-booking")
        self.domain_name: str = os.getenv("DOMAIN_NAME", "webhook-booking.innamul.com")
        self.webhook_url: str = os.getenv("WEBHOOK_URL", "https://webhook-booking.innamul.com/webhook")
        self.webhook_timeout: int = int(os.getenv("WEBHOOK_TIMEOUT", "30"))
        self.enable_webhook_verification: bool = os.getenv("ENABLE_WEBHOOK_VERIFICATION", "True").lower() == "true"
        
        # Logging settings
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.log_dir: str = os.getenv("LOG_DIR", "logs")
        self.enable_file_logging: bool = os.getenv("ENABLE_FILE_LOGGING", "True").lower() == "true"
        self.enable_console_logging: bool = os.getenv("ENABLE_CONSOLE_LOGGING", "True").lower() == "true"
        self.log_file: Optional[str] = os.getenv("LOG_FILE")
        self.log_format: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        
        # File storage settings
        self.upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")
        self.max_upload_size: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB
        
        # Cache settings
        self.redis_url: Optional[str] = os.getenv("REDIS_URL")
        self.cache_ttl: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes
        
        # Rate limiting
        self.rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # 1 minute
        
        # Performance settings
        self.max_message_length: int = int(os.getenv("MAX_MESSAGE_LENGTH", "1500"))
        self.health_check_timeout: int = int(os.getenv("HEALTH_CHECK_TIMEOUT", "30"))
        self.metrics_enabled: bool = os.getenv("METRICS_ENABLED", "False").lower() == "true"
    
    # Legacy compatibility
    @property
    def therapist_phone(self) -> str:
        """Legacy compatibility property"""
        return self.coordinator_phone_number
    
    def get_database_url(self) -> str:
        """Get the complete database URL"""
        return self.database_url
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == "development"
    
    def get_log_config(self) -> dict:
        """Get logging configuration"""
        return {
            "level": self.log_level,
            "file_logging": self.enable_file_logging,
            "console_logging": self.enable_console_logging,
            "log_dir": self.log_dir
        }
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL"""
        return self.database_url.replace("mysql+pymysql://", "mysql://")
    
    @property
    def uploads_path(self) -> Path:
        """Get uploads directory path"""
        return Path(self.upload_dir)
    
    def create_directories(self):
        """Create necessary directories"""
        directories = [
            self.uploads_path,
            Path(self.log_dir),
            Path("backups"),
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    """
    return Settings()

# Global settings instance
settings = get_settings()


# Create global settings instance
settings = get_settings()