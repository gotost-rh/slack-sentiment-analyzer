#!/usr/bin/env python3
"""
Configuration management for the Slack Sentiment Analyzer.
Handles environment variables, validation, and feature flags.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


@dataclass
class SlackConfig:
    """Slack API configuration."""
    bot_token: str
    signing_secret: str
    app_token: Optional[str] = None


@dataclass
class GeminiConfig:
    """Gemini AI API configuration."""
    api_key: str
    model_name: str = "gemini-1.5-flash-latest"
    timeout: int = 30
    max_retries: int = 3


@dataclass
class ServerConfig:
    """Flask server configuration."""
    host: str = "0.0.0.0"
    port: int = 3000
    debug: bool = False


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: Optional[str] = None
    pool_size: int = 10
    max_overflow: int = 20


@dataclass
class SecurityConfig:
    """Security and encryption configuration."""
    secret_key: str
    encryption_key: Optional[str] = None


@dataclass
class FeatureConfig:
    """Feature flags configuration."""
    enable_japanese_support: bool = True
    enable_data_storage: bool = True
    enable_async_processing: bool = True
    default_retention_days: int = 30
    max_retention_days: int = 365


class Config:
    """Main configuration class."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load environment variables
        load_dotenv()
        
        # Load all configuration sections
        self.slack = self._load_slack_config()
        self.gemini = self._load_gemini_config()
        self.server = self._load_server_config()
        self.database = self._load_database_config()
        self.security = self._load_security_config()
        self.features = self._load_feature_config()
        
        # Setup logging
        self._setup_logging()
    
    def _load_slack_config(self) -> Optional[SlackConfig]:
        """Load Slack configuration from environment variables."""
        bot_token = os.getenv('SLACK_BOT_TOKEN')
        signing_secret = os.getenv('SLACK_SIGNING_SECRET')
        
        # For standalone mode, Slack config is optional
        if not bot_token and not signing_secret:
            return None
            
        if not bot_token or not signing_secret:
            raise ConfigurationError(
                "Both SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET are required for Slack integration"
            )
        
        return SlackConfig(
            bot_token=bot_token,
            signing_secret=signing_secret,
            app_token=os.getenv('SLACK_APP_TOKEN')
        )
    
    def _load_gemini_config(self) -> GeminiConfig:
        """Load Gemini AI configuration from environment variables."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ConfigurationError("GEMINI_API_KEY environment variable is required")
        
        return GeminiConfig(
            api_key=api_key,
            model_name=os.getenv('GEMINI_MODEL', 'gemini-1.5-flash-latest'),
            timeout=int(os.getenv('GEMINI_TIMEOUT', '30')),
            max_retries=int(os.getenv('GEMINI_MAX_RETRIES', '3'))
        )
    
    def _load_server_config(self) -> ServerConfig:
        """Load Flask server configuration from environment variables."""
        return ServerConfig(
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', '3000')),
            debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
        )
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration from environment variables."""
        return DatabaseConfig(
            url=os.getenv('DATABASE_URL'),
            pool_size=int(os.getenv('DB_POOL_SIZE', '10')),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '20'))
        )
    
    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration from environment variables."""
        secret_key = os.getenv('SECRET_KEY')
        if not secret_key:
            # Generate a default secret key for development
            import secrets
            secret_key = secrets.token_hex(32)
        
        return SecurityConfig(
            secret_key=secret_key,
            encryption_key=os.getenv('ENCRYPTION_KEY')
        )
    
    def _load_feature_config(self) -> FeatureConfig:
        """Load feature flags from environment variables."""
        return FeatureConfig(
            enable_japanese_support=os.getenv('ENABLE_JAPANESE_SUPPORT', 'true').lower() == 'true',
            enable_data_storage=os.getenv('ENABLE_DATA_STORAGE', 'false').lower() == 'true',
            enable_async_processing=os.getenv('ENABLE_ASYNC_PROCESSING', 'false').lower() == 'true',
            default_retention_days=int(os.getenv('DEFAULT_RETENTION_DAYS', '30')),
            max_retention_days=int(os.getenv('MAX_RETENTION_DAYS', '365'))
        )
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_format = os.getenv('LOG_FORMAT', 'standard')
        
        if log_format == 'json':
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Set up console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Configure specific loggers
        loggers = ['standalone_app', 'gemini_client', 'slack_handler']
        for logger_name in loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    def validate(self) -> Dict[str, Any]:
        """Validate the configuration and return validation results."""
        errors = []
        warnings = []
        
        # Validate Gemini configuration
        if not self.gemini.api_key:
            errors.append("GEMINI_API_KEY is required")
        
        if self.gemini.timeout < 1 or self.gemini.timeout > 300:
            warnings.append("GEMINI_TIMEOUT should be between 1 and 300 seconds")
        
        if self.gemini.max_retries < 1 or self.gemini.max_retries > 10:
            warnings.append("GEMINI_MAX_RETRIES should be between 1 and 10")
        
        # Validate server configuration
        if self.server.port < 1 or self.server.port > 65535:
            errors.append("PORT must be between 1 and 65535")
        
        # Validate feature configuration
        if self.features.default_retention_days < 1:
            errors.append("DEFAULT_RETENTION_DAYS must be at least 1")
        
        if self.features.default_retention_days > self.features.max_retention_days:
            errors.append("DEFAULT_RETENTION_DAYS cannot exceed MAX_RETENTION_DAYS")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def config_summary(self) -> Dict[str, Any]:
        """Return a summary of the current configuration."""
        return {
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'debug_mode': self.server.debug,
            'slack_enabled': self.slack is not None,
            'japanese_support': self.features.enable_japanese_support,
            'data_storage': self.features.enable_data_storage,
            'async_processing': self.features.enable_async_processing,
            'retention_days': self.features.default_retention_days
        }


# Global configuration instance
_config = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """Reload the configuration from environment variables."""
    global _config
    _config = Config()
    return _config


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = get_config()
        validation = config.validate()
        
        print("Configuration Summary:")
        print("=" * 40)
        for key, value in config.config_summary().items():
            print(f"{key}: {value}")
        
        print("\nValidation Results:")
        print("=" * 40)
        print(f"Valid: {validation['valid']}")
        
        if validation['errors']:
            print("Errors:")
            for error in validation['errors']:
                print(f"  - {error}")
        
        if validation['warnings']:
            print("Warnings:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
                
    except ConfigurationError as e:
        print(f"Configuration Error: {e}")
        exit(1)