import os
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add path to environment config
sys.path.append(str(Path(__file__).parent.parent.parent / "other_scripts"))

load_dotenv()

class Config:
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'Ishak@123')
    DB_NAME = os.getenv('DB_NAME', 'booking')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    
    # Support both SQLite (POC) and MySQL (Production)
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        # Use MySQL with your provided credentials - URL encode the password
        import urllib.parse
        encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
        DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    
    # WhatsApp Business API Configuration
    WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
    WHATSAPP_SID = os.getenv('WHATSAPP_SID')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
    TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')  # For sandbox
    SANDBOX_MODE = os.getenv('SANDBOX_MODE', 'false').lower() == 'true'
    
    # ChatAPI Configuration (Production) - DEPRECATED (ChatAPI closed)
    CHATAPI_INSTANCE_ID = os.getenv('CHATAPI_INSTANCE_ID')
    CHATAPI_TOKEN = os.getenv('CHATAPI_TOKEN')
    
    # Ultramsg Configuration (ChatAPI replacement)
    ULTRAMSG_INSTANCE_ID = os.getenv('ULTRAMSG_INSTANCE_ID')
    ULTRAMSG_TOKEN = os.getenv('ULTRAMSG_TOKEN')
    ULTRAMSG_BASE_URL = os.getenv('ULTRAMSG_BASE_URL', 'https://api.ultramsg.com')
    
    WHATSAPP_PROVIDER = os.getenv('WHATSAPP_PROVIDER', 'ultramsg')  # 'twilio', 'ultramsg', or 'telegram'
    
    # Therapy Practice Configuration
    CLINIC_NAME = os.getenv('CLINIC_NAME', 'Wellness Therapy Center')
    THERAPIST_NAME = os.getenv('THERAPIST_NAME', 'Dr. Sarah Smith')
    CLINIC_ADDRESS = os.getenv('CLINIC_ADDRESS', '123 Health Street, Wellness City')
    EMERGENCY_CONTACT = os.getenv('EMERGENCY_CONTACT', '(555) 123-4567')
    CRISIS_CENTER = os.getenv('CRISIS_CENTER', 'Local Crisis Support Center')
    
    # Google Agent Development Kit (ADK) Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  # Legacy support
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-pro')  # Legacy support
    ADK_AGENT_CONFIG = os.getenv('ADK_AGENT_CONFIG', 'config/agent_config.json')
    
    # Enhanced AI Models Configuration
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    GOOGLE_GENAI_MODEL = os.getenv('GOOGLE_GENAI_MODEL', 'gemini-1.5-pro-002')
    GOOGLE_GENAI_USE_VERTEXAI = os.getenv('GOOGLE_GENAI_USE_VERTEXAI', 'FALSE').upper() == 'TRUE'
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514')
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini')
    
    # Application Configuration (FIXED VALUES)
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'  
    HOST = "0.0.0.0"  # FIXED - Always bind to all interfaces
    PORT = 8000       # FIXED - Always use port 8000 (DO NOT CHANGE)
    
    # Phone Numbers Configuration (CRITICAL - FROM ENVIRONMENT)
    AGENT_PHONE_NUMBER = "+97451334514"      # Agent/Bot WhatsApp number (FIXED)
    THERAPIST_PHONE_NUMBER = "+97471669569"  # Therapist contact number (FIXED) 
    
    # Legacy compatibility
    THERAPIST_PHONE = THERAPIST_PHONE_NUMBER
    CLIENT_WEBHOOK_URL = os.getenv('CLIENT_WEBHOOK_URL')
    THERAPIST_WEBHOOK_URL = os.getenv('THERAPIST_WEBHOOK_URL')

config = Config()

def get_settings():
    """Get configuration settings"""
    return config
