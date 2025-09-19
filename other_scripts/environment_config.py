"""
Environment Configuration Loader
Loads all environment variables and system settings
"""

import os
import logging
from pathlib import Path
from typing import Optional

class EnvironmentConfig:
    """Environment configuration management"""
    
    def __init__(self):
        """Initialize environment configuration"""
        self.load_env_file()
        
        # Server Configuration - READ FROM ENVIRONMENT VARIABLES
        self.SERVER_HOST = self.get_env('SERVER_HOST')  # Required from env
        self.SERVER_PORT = int(self.get_env('SERVER_PORT'))  # Required from env
        self.DEBUG_MODE = self.get_bool('DEBUG_MODE')
        
        # Critical Phone Numbers - READ FROM ENVIRONMENT VARIABLES
        self.AGENT_PHONE_NUMBER = self.get_env('AGENT_PHONE_NUMBER')      # Required from env
        self.COORDINATOR_PHONE_NUMBER = self.get_env('COORDINATOR_PHONE_NUMBER')  # Required from env
        
        # Ultramsg Configuration - READ FROM ENVIRONMENT VARIABLES
        self.ULTRAMSG_INSTANCE_ID = self.get_env('ULTRAMSG_INSTANCE_ID')
        self.ULTRAMSG_TOKEN = self.get_env('ULTRAMSG_TOKEN')
        self.ULTRAMSG_BASE_URL = self.get_env('ULTRAMSG_BASE_URL')
        
        # Cloudflare Configuration - READ FROM ENVIRONMENT VARIABLES
        self.TUNNEL_NAME = self.get_env('TUNNEL_NAME')
        self.DOMAIN_NAME = self.get_env('DOMAIN_NAME')
        self.WEBHOOK_URL = f"https://{self.DOMAIN_NAME}/webhook" if self.DOMAIN_NAME else None
        
        # Database Configuration - READ FROM ENVIRONMENT VARIABLES
        self.DB_HOST = self.get_env('DB_HOST')
        self.DB_PORT = int(self.get_env('DB_PORT')) if self.get_env('DB_PORT') else None
        self.DB_NAME = self.get_env('DB_NAME')
        self.DB_USER = self.get_env('DB_USER')
        self.DB_PASSWORD = self.get_env('DB_PASSWORD')
        
        # ADK Configuration - READ FROM ENVIRONMENT VARIABLES
        self.ADK_PROJECT_ID = self.get_env('ADK_PROJECT_ID')
        self.ADK_MODEL_NAME = self.get_env('ADK_MODEL_NAME')
        self.ADK_SESSION_TIMEOUT = int(self.get_env('ADK_SESSION_TIMEOUT')) if self.get_env('ADK_SESSION_TIMEOUT') else None
        
        # Logging Configuration - READ FROM ENVIRONMENT VARIABLES
        self.LOG_LEVEL = self.get_env('LOG_LEVEL')
        self.LOG_DIR = self.get_env('LOG_DIR')
        self.ENABLE_FILE_LOGGING = self.get_bool('ENABLE_FILE_LOGGING')
        self.ENABLE_CONSOLE_LOGGING = self.get_bool('ENABLE_CONSOLE_LOGGING')
        
        # Webhook Configuration - READ FROM ENVIRONMENT VARIABLES
        self.WEBHOOK_TIMEOUT = int(self.get_env('WEBHOOK_TIMEOUT')) if self.get_env('WEBHOOK_TIMEOUT') else None
        self.MAX_MESSAGE_LENGTH = int(self.get_env('MAX_MESSAGE_LENGTH')) if self.get_env('MAX_MESSAGE_LENGTH') else None
        self.ENABLE_WEBHOOK_VERIFICATION = self.get_bool('ENABLE_WEBHOOK_VERIFICATION')
        
        # Business Information - READ FROM ENVIRONMENT VARIABLES
        self.BUSINESS_NAME = self.get_env('BUSINESS_NAME')
        self.BUSINESS_HOURS = self.get_env('BUSINESS_HOURS')
        self.TIMEZONE = self.get_env('TIMEZONE')
    
    def load_env_file(self):
        """Load environment variables from .env file"""
        env_file = Path(__file__).parent.parent / '.env'
        
        if env_file.exists():
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            # Remove quotes if present
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            
                            os.environ[key] = value
                            
                print(f"[SUCCESS] Loaded environment from: {env_file}")
                
            except Exception as e:
                print(f"[WARNING] Could not load .env file: {str(e)}")
        else:
            print(f"[INFO] No .env file found at: {env_file}")
    
    def get_env(self, key: str, default: str = None) -> str:
        """Get environment variable - returns None if not set and no default provided"""
        return os.getenv(key, default)
    
    def get_bool(self, key: str, default: bool = None) -> bool:
        """Get boolean environment variable - returns False if not set and no default provided"""
        value = os.getenv(key)
        if value is None:
            return default if default is not None else False
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def get_database_url(self) -> str:
        """Get complete database connection URL"""
        return f"mysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    def get_server_info(self) -> dict:
        """Get server configuration info"""
        return {
            "host": self.SERVER_HOST,
            "port": self.SERVER_PORT,
            "debug": self.DEBUG_MODE,
            "local_url": f"http://localhost:{self.SERVER_PORT}",
            "webhook_url": self.WEBHOOK_URL
        }
    
    def get_phone_numbers(self) -> dict:
        """Get all configured phone numbers"""
        return {
            "agent_number": self.AGENT_PHONE_NUMBER,
            "therapist_number": self.COORDINATOR_PHONE_NUMBER,
            "agent_formatted": self.AGENT_PHONE_NUMBER.replace("+", ""),
            "therapist_formatted": self.COORDINATOR_PHONE_NUMBER.replace("+", "")
        }
    
    def validate_configuration(self) -> bool:
        """Validate critical configuration values"""
        errors = []
        
        # Validate phone numbers
        if not self.AGENT_PHONE_NUMBER.startswith('+'):
            errors.append("Agent phone number must start with +")
            
        if not self.COORDINATOR_PHONE_NUMBER.startswith('+'):
            errors.append("Coordinator phone number must start with +")
        
        # Validate server port
        if self.SERVER_PORT != 8000:
            errors.append("Server port must be 8000 (FIXED REQUIREMENT)")
        
        # Validate required fields
        required_fields = [
            ('ULTRAMSG_INSTANCE_ID', self.ULTRAMSG_INSTANCE_ID),
            ('ULTRAMSG_TOKEN', self.ULTRAMSG_TOKEN),
            ('DB_PASSWORD', self.DB_PASSWORD)
        ]
        
        for field_name, field_value in required_fields:
            if not field_value:
                errors.append(f"{field_name} is required")
        
        if errors:
            print("❌ Configuration validation errors:")
            for error in errors:
                print(f"   • {error}")
            return False
        
        print("[SUCCESS] Configuration validation passed")
        return True
    
    def print_configuration(self):
        """Print current configuration (hiding sensitive data)"""
        print("\n" + "=" * 60)
        print("[CONFIG] THERAPY BOOKING SYSTEM CONFIGURATION")
        print("=" * 60)
        
        print(f"\n📡 SERVER CONFIGURATION:")
        print(f"   • Host: {self.SERVER_HOST}")
        print(f"   • Port: {self.SERVER_PORT} (FIXED)")
        print(f"   • Debug: {self.DEBUG_MODE}")
        print(f"   • Local URL: http://localhost:{self.SERVER_PORT}")
        
        print(f"\n📞 PHONE NUMBERS:")
        print(f"   • Agent/Bot: {self.AGENT_PHONE_NUMBER}")
        print(f"   • Coordinator: {self.COORDINATOR_PHONE_NUMBER}")
        
        print(f"\n📱 ULTRAMSG CONFIGURATION:")
        print(f"   • Instance: {self.ULTRAMSG_INSTANCE_ID}")
        print(f"   • Token: {self.ULTRAMSG_TOKEN[:10]}...{self.ULTRAMSG_TOKEN[-4:]}")
        print(f"   • Base URL: {self.ULTRAMSG_BASE_URL}")
        
        print(f"\n🌐 WEBHOOK CONFIGURATION:")
        print(f"   • Domain: {self.DOMAIN_NAME}")
        print(f"   • Webhook URL: {self.WEBHOOK_URL}")
        print(f"   • Tunnel: {self.TUNNEL_NAME}")
        
        print(f"\n🗄️  DATABASE CONFIGURATION:")
        print(f"   • Host: {self.DB_HOST}:{self.DB_PORT}")
        print(f"   • Database: {self.DB_NAME}")
        print(f"   • User: {self.DB_USER}")
        print(f"   • Password: {'*' * len(self.DB_PASSWORD)}")
        
        print(f"\n🤖 ADK AGENT CONFIGURATION:")
        print(f"   • Project: {self.ADK_PROJECT_ID}")
        print(f"   • Model: {self.ADK_MODEL_NAME}")
        print(f"   • Session Timeout: {self.ADK_SESSION_TIMEOUT}s")
        
        print(f"\n🏢 BUSINESS INFORMATION:")
        print(f"   • Name: {self.BUSINESS_NAME}")
        print(f"   • Hours: {self.BUSINESS_HOURS}")
        print(f"   • Timezone: {self.TIMEZONE}")
        
        print("=" * 60)

# Global configuration instance
config = EnvironmentConfig()

def get_config() -> EnvironmentConfig:
    """Get global configuration instance"""
    return config

if __name__ == "__main__":
    # Test configuration loading
    config = get_config()
    config.print_configuration()
    config.validate_configuration()
