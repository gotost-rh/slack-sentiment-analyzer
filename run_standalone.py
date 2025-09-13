#!/usr/bin/env python3
"""
Startup script for the standalone sentiment analyzer.
Handles environment setup, configuration validation, and service startup.
"""

import sys
import os
import argparse
from pathlib import Path

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Import and check configuration
try:
    from config import get_config
    config = get_config()
    validation = config.validate()
except Exception as e:
    print(f"❌ Configuration Error: {e}")
    sys.exit(1)


def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        'flask',
        'flask_cors', 
        'requests',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required dependencies:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall missing dependencies with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True


def setup_environment():
    """Setup environment and check for required files."""
    # Check if .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        env_standalone = Path('env.standalone')
        if env_standalone.exists():
            print("📋 No .env file found. Creating from template...")
            env_standalone.rename('.env')
            print("✅ Created .env file from env.standalone")
            print("🔧 Please edit .env and set your GEMINI_API_KEY")
            return False
        else:
            print("❌ No .env file found and no env.standalone template available")
            print("Please create a .env file with your configuration")
            return False
    
    return True


def print_startup_banner():
    """Print the startup banner."""
    print("🎭 Standalone Sentiment Analyzer")
    print("=" * 40)
    print("✅ All required dependencies found")
    
    if Path('.env').exists():
        print("✅ Found existing .env file")
    
    print("\n📊 Configuration Status:")
    summary = config.config_summary()
    for key, value in summary.items():
        formatted_key = key.replace('_', ' ').title()
        print(f"  {formatted_key}: {value}")
    
    if validation['valid']:
        print("✅ Configuration is valid!")
    else:
        print("❌ Configuration has errors:")
        for error in validation['errors']:
            print(f"  - {error}")
        return False
    
    if validation['warnings']:
        print("⚠️  Configuration warnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    return True


def start_service():
    """Start the Flask service."""
    print(f"🚀 Starting service on http://{config.server.host}:{config.server.port}")
    print(f"📍 Web interface: http://{config.server.host}:{config.server.port}")
    print(f"🔗 API endpoint: http://{config.server.host}:{config.server.port}/api/analyze")
    print(f"📊 Health check: http://{config.server.host}:{config.server.port}/health")
    print("✨ Press Ctrl+C to stop the service")
    print("-" * 40)
    
    # Import and create the Flask app
    from standalone_app import create_app
    app = create_app()
    
    # Start the server
    app.run(
        host=config.server.host,
        port=config.server.port,
        debug=config.server.debug
    )


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Standalone Sentiment Analyzer')
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check configuration and dependencies, do not start service'
    )
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Run setup wizard to create configuration'
    )
    
    args = parser.parse_args()
    
    try:
        # Check dependencies
        if not check_dependencies():
            sys.exit(1)
        
        # Setup environment
        if not setup_environment():
            sys.exit(1)
        
        # Print startup information
        if not print_startup_banner():
            sys.exit(1)
        
        # If check-only mode, exit here
        if args.check_only:
            print("\n🔍 Configuration check complete!")
            return
        
        # Start the service
        start_service()
        
    except KeyboardInterrupt:
        print("\n\n👋 Service stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()