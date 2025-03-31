#!/usr/bin/env python3
"""
Setup script for the AI-Powered Freshdesk Ticket Assistant.
This script helps with initial setup and configuration.
"""

import os
import sys
import json
import secrets
import subprocess
from pathlib import Path

def check_python_version():
    """Check if the Python version is compatible."""
    if sys.version_info < (3, 9):
        print("Error: Python 3.9 or higher is required.")
        sys.exit(1)
    
    if sys.version_info >= (3, 13):
        print("Error: Python 3.13 is not currently supported due to compatibility issues with SQLAlchemy.")
        print("Please use Python 3.9 to 3.12 for this application.")
        sys.exit(1)
    
    print("✓ Python version check passed")

def create_virtual_environment():
    """Create a virtual environment if it doesn't exist."""
    venv_path = Path("venv")
    if venv_path.exists():
        print("✓ Virtual environment already exists")
        return
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✓ Virtual environment created successfully")
    except subprocess.CalledProcessError:
        print("Error: Failed to create virtual environment.")
        sys.exit(1)

def install_dependencies():
    """Install dependencies from requirements.txt."""
    pip_cmd = "venv/bin/pip" if os.name != "nt" else r"venv\Scripts\pip"
    
    try:
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("Error: Failed to install dependencies.")
        sys.exit(1)

def update_config():
    """Update the configuration file with user input."""
    config_path = Path("config.json")
    
    if not config_path.exists():
        print("Error: config.json not found.")
        sys.exit(1)
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Generate a secure secret key
    config["app"]["secret_key"] = secrets.token_hex(16)
    
    # Get Freshdesk configuration
    print("\nFreshdesk Configuration:")
    config["freshdesk"]["domain"] = input("Enter your Freshdesk domain (e.g., yourcompany.freshdesk.com): ")
    config["freshdesk"]["api_key"] = input("Enter your Freshdesk API key: ")
    
    # Get OpenAI configuration
    print("\nOpenAI Configuration:")
    config["openai"]["api_key"] = input("Enter your OpenAI API key: ")
    config["openai"]["model"] = input("Enter the OpenAI model to use (default: gpt-3.5-turbo): ") or "gpt-3.5-turbo"
    
    # Get application configuration
    print("\nApplication Configuration:")
    poll_interval = input("Enter the polling interval in seconds (default: 300): ")
    if poll_interval and poll_interval.isdigit():
        config["app"]["poll_interval_seconds"] = int(poll_interval)
    
    # Save the updated configuration
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    print("✓ Configuration updated successfully")

def initialize_database():
    """Initialize the database."""
    try:
        from database.models import init_db
        init_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"Error: Failed to initialize database: {str(e)}")
        sys.exit(1)

def main():
    """Main setup function."""
    print("Setting up AI-Powered Freshdesk Ticket Assistant...\n")
    
    check_python_version()
    create_virtual_environment()
    install_dependencies()
    update_config()
    initialize_database()
    
    print("\nSetup completed successfully!")
    print("\nTo run the application:")
    if os.name != "nt":
        print("  source venv/bin/activate")
    else:
        print("  venv\\Scripts\\activate")
    print("  python app.py")
    print("\nThe application will be available at http://localhost:8001")

if __name__ == "__main__":
    main()
