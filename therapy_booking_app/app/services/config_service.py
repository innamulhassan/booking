"""
Centralized configuration management service.
Handles environment variables, settings validation, and configuration updates.
"""
import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import json


logger = logging.getLogger(__name__)


@dataclass
class ConfigSection:
    """Configuration section with validation."""
    name: str
    required_keys: List[str]
    optional_keys: List[str] = None
    description: str = ""
    
    def __post_init__(self):
        if self.optional_keys is None:
            self.optional_keys = []


class ConfigurationService:
    """Service for managing application configuration."""
    
    def __init__(self):
        self._config = {}
        self._sections = self._define_config_sections()
        self._validation_errors = []
        self.load_configuration()
    
    def _define_config_sections(self) -> Dict[str, ConfigSection]:
        """Define configuration sections and their requirements."""
        return {
            'database': ConfigSection(
                name='database',
                required_keys=['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD'],
                optional_keys=[],
                description='MySQL database connection settings'
            ),
            'ultramsg': ConfigSection(
                name='ultramsg',
                required_keys=['ULTRAMSG_TOKEN', 'ULTRAMSG_INSTANCE_ID'],
                optional_keys=['ULTRAMSG_BASE_URL'],
                description='UltraMsg WhatsApp API configuration'
            ),
            'webhook': ConfigSection(
                name='webhook',
                required_keys=['WEBHOOK_URL'],
                optional_keys=['WEBHOOK_TIMEOUT', 'MAX_MESSAGE_LENGTH', 'ENABLE_WEBHOOK_VERIFICATION'],
                description='Webhook configuration and security'
            ),
            'coordinator': ConfigSection(
                name='coordinator',
                required_keys=['COORDINATOR_PHONE_NUMBER'],
                optional_keys=['TESTCLIENT_PHONE_NUMBER'],
                description='Coordinator contact information'
            ),
            'business': ConfigSection(
                name='business',
                required_keys=['BUSINESS_NAME'],
                optional_keys=['BUSINESS_HOURS', 'TIMEZONE'],
                description='Business information and contact details'
            ),
            'logging': ConfigSection(
                name='logging',
                required_keys=[],
                optional_keys=['LOG_LEVEL', 'LOG_DIR', 'ENABLE_FILE_LOGGING', 'ENABLE_CONSOLE_LOGGING'],
                description='Logging configuration'
            ),
            'agent': ConfigSection(
                name='agent',
                required_keys=['ADK_PROJECT_ID'],
                optional_keys=['ADK_MODEL_NAME', 'ADK_SESSION_TIMEOUT', 'AGENT_PHONE_NUMBER'],
                description='ADK agent configuration'
            ),
            'server': ConfigSection(
                name='server',
                required_keys=[],
                optional_keys=['SERVER_HOST', 'SERVER_PORT', 'DEBUG_MODE'],
                description='Server configuration'
            )
        }
    
    def load_configuration(self):
        """Load configuration from environment variables."""
        try:
            self._config = {}
            
            for section_name, section in self._sections.items():
                section_config = {}
                
                # Load required keys
                for key in section.required_keys:
                    value = os.getenv(key)
                    if value is None:
                        self._validation_errors.append(f"Missing required config: {key} in section '{section_name}'")
                    else:
                        section_config[key] = value
                
                # Load optional keys
                for key in section.optional_keys:
                    value = os.getenv(key)
                    if value is not None:
                        section_config[key] = value
                
                self._config[section_name] = section_config
            
            # Apply defaults
            self._apply_defaults()
            
            # Validate configuration
            self._validate_config()
            
            logger.info("Configuration loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self._validation_errors.append(f"Configuration loading error: {e}")
    
    def _apply_defaults(self):
        """Apply default values for optional configuration."""
        defaults = {
            'database': {
                'DB_CHARSET': 'utf8mb4',
                'DB_POOL_SIZE': '10'
            },
            'ultramsg': {
                'ULTRAMSG_BASE_URL': 'https://api.ultramsg.com'
            },
            'webhook': {
                'WEBHOOK_TIMEOUT': '30'
            },
            'logging': {
                'LOG_LEVEL': 'INFO',
                'LOG_FILE_PATH': 'logs/app.log',
                'LOG_MAX_SIZE': '10485760',  # 10MB
                'LOG_BACKUP_COUNT': '5'
            },
            'agent': {
                'ADK_API_BASE_URL': 'https://api.googleadkagent.com',
                'ADK_TIMEOUT': '30'
            }
        }
        
        for section_name, section_defaults in defaults.items():
            if section_name in self._config:
                for key, default_value in section_defaults.items():
                    if key not in self._config[section_name]:
                        self._config[section_name][key] = default_value
    
    def _validate_config(self):
        """Validate configuration values."""
        validators = {
            'DB_PORT': self._validate_port,
            'DB_POOL_SIZE': self._validate_positive_int,
            'WEBHOOK_TIMEOUT': self._validate_positive_int,
            'LOG_MAX_SIZE': self._validate_positive_int,
            'LOG_BACKUP_COUNT': self._validate_positive_int,
            'ADK_TIMEOUT': self._validate_positive_int,
            'COORDINATOR_PHONE': self._validate_phone,
            'COORDINATOR_BACKUP_PHONE': self._validate_phone,
            'BUSINESS_PHONE': self._validate_phone
        }
        
        for section_config in self._config.values():
            for key, value in section_config.items():
                if key in validators:
                    try:
                        validators[key](value)
                    except ValueError as e:
                        self._validation_errors.append(f"Invalid {key}: {e}")
    
    def _validate_port(self, value: str):
        """Validate port number."""
        try:
            port = int(value)
            if not (1 <= port <= 65535):
                raise ValueError("Port must be between 1 and 65535")
        except ValueError:
            raise ValueError("Port must be a valid integer")
    
    def _validate_positive_int(self, value: str):
        """Validate positive integer."""
        try:
            num = int(value)
            if num <= 0:
                raise ValueError("Must be a positive integer")
        except ValueError:
            raise ValueError("Must be a valid positive integer")
    
    def _validate_phone(self, value: str):
        """Validate phone number format."""
        if not value:
            return  # Optional field
        
        # Remove common phone number characters
        cleaned = ''.join(c for c in value if c.isdigit() or c in '+')
        
        if not cleaned.startswith('+'):
            raise ValueError("Phone number should start with country code (+)")
        
        if len(cleaned) < 10 or len(cleaned) > 15:
            raise ValueError("Phone number should be between 10-15 digits")
    
    def get_config(self, section: str, key: Optional[str] = None) -> Any:
        """
        Get configuration value(s).
        
        Args:
            section: Configuration section name
            key: Optional specific key within section
            
        Returns:
            Configuration value or section dict
        """
        if section not in self._config:
            return None
        
        if key is None:
            return self._config[section].copy()
        
        return self._config[section].get(key)
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration."""
        return self.get_config('database') or {}
    
    def get_ultramsg_config(self) -> Dict[str, str]:
        """Get UltraMsg configuration."""
        return self.get_config('ultramsg') or {}
    
    def get_webhook_config(self) -> Dict[str, str]:
        """Get webhook configuration."""
        return self.get_config('webhook') or {}
    
    def get_coordinator_phone(self) -> Optional[str]:
        """Get coordinator phone number."""
        return self.get_config('coordinator', 'COORDINATOR_PHONE_NUMBER')
    
    def get_business_config(self) -> Dict[str, str]:
        """Get business configuration."""
        return self.get_config('business') or {}
    
    def get_agent_config(self) -> Dict[str, str]:
        """Get ADK agent configuration."""
        return self.get_config('agent') or {}
    
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self._validation_errors) == 0
    
    def get_validation_errors(self) -> List[str]:
        """Get list of configuration validation errors."""
        return self._validation_errors.copy()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary (without sensitive values)."""
        summary = {}
        sensitive_keys = {'DB_PASSWORD', 'ULTRAMSG_TOKEN', 'WEBHOOK_SECRET'}
        
        for section_name, section_config in self._config.items():
            summary[section_name] = {}
            for key, value in section_config.items():
                if key in sensitive_keys:
                    summary[section_name][key] = "***" if value else "Not set"
                else:
                    summary[section_name][key] = value
        
        return summary
    
    def validate_required_config(self) -> Dict[str, Any]:
        """
        Validate that all required configuration is present.
        
        Returns:
            Dict with validation results
        """
        missing_config = []
        invalid_config = []
        
        for section_name, section in self._sections.items():
            for required_key in section.required_keys:
                if not self.get_config(section_name, required_key):
                    missing_config.append(f"{section_name}.{required_key}")
        
        return {
            'is_valid': len(missing_config) == 0 and len(self._validation_errors) == 0,
            'missing_config': missing_config,
            'validation_errors': self._validation_errors,
            'total_sections': len(self._sections),
            'configured_sections': len([s for s in self._config.values() if s])
        }
    
    def export_config_template(self, file_path: Optional[str] = None) -> str:
        """
        Export configuration template with all required and optional keys.
        
        Args:
            file_path: Optional file path to save template
            
        Returns:
            Template content as string
        """
        template_lines = [
            "# Therapy Booking System Configuration Template",
            "# Copy this file to .env and fill in the values",
            "",
            "# IMPORTANT: Never commit .env files to version control!",
            ""
        ]
        
        for section_name, section in self._sections.items():
            template_lines.extend([
                f"# {section.description}",
                f"# Section: {section_name.upper()}",
            ])
            
            # Required keys
            if section.required_keys:
                template_lines.append("# Required:")
                for key in section.required_keys:
                    template_lines.append(f"{key}=")
            
            # Optional keys
            if section.optional_keys:
                template_lines.append("# Optional:")
                for key in section.optional_keys:
                    current_value = self.get_config(section_name, key)
                    template_lines.append(f"#{key}={current_value or ''}")
            
            template_lines.append("")
        
        template_content = "\n".join(template_lines)
        
        if file_path:
            try:
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(template_content)
                logger.info(f"Configuration template exported to {file_path}")
            except Exception as e:
                logger.error(f"Error exporting template: {e}")
        
        return template_content


# Global instance
config_service = ConfigurationService()