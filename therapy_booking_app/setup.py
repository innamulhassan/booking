#!/usr/bin/env python3
"""
Setup script for Therapy Booking WhatsApp Bot
Helps with initial environment setup and database creation
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, check=True):
    """Run a shell command and return the result"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"Error output: {result.stderr}")
        sys.exit(1)
    
    return result

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python version: {sys.version}")

def check_mysql():
    """Check if MySQL is installed and running"""
    try:
        result = run_command("mysql --version", check=False)
        if result.returncode == 0:
            print("✓ MySQL is installed")
            return True
        else:
            print("⚠ MySQL not found in PATH")
            return False
    except Exception:
        print("⚠ MySQL not found")
        return False

def create_virtual_environment():
    """Create and activate virtual environment"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✓ Virtual environment already exists")
    else:
        print("Creating virtual environment...")
        run_command(f"{sys.executable} -m venv venv")
        print("✓ Virtual environment created")
    
    # Get activation command based on OS
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/Mac
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    return activate_cmd, pip_cmd

def install_dependencies(pip_cmd):
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    run_command(f"{pip_cmd} install --upgrade pip")
    run_command(f"{pip_cmd} install -r requirements.txt")
    print("✓ Dependencies installed")

def create_env_file():
    """Create .env file from template"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✓ .env file already exists")
    elif env_example.exists():
        shutil.copy(env_example, env_file)
        print("✓ Created .env file from template")
        print("⚠ Please edit .env file with your actual configuration values")
    else:
        print("⚠ .env.example file not found")

def create_database():
    """Create MySQL database"""
    print("\\nDatabase Setup:")
    print("Please run the following commands in your MySQL client:")
    print("----")
    print("CREATE DATABASE therapy_booking;")
    print("CREATE USER 'therapy_user'@'localhost' IDENTIFIED BY 'your_password';")
    print("GRANT ALL PRIVILEGES ON therapy_booking.* TO 'therapy_user'@'localhost';")
    print("FLUSH PRIVILEGES;")
    print("----")
    print("Update your .env file with the correct database credentials")

def setup_directories():
    """Create necessary directories"""
    directories = [
        "logs",
        "uploads",
        "backups"
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True)
            print(f"✓ Created directory: {directory}")

def main():
    """Main setup function"""
    print("=== Therapy Booking WhatsApp Bot Setup ===\\n")
    
    # Check Python version
    check_python_version()
    
    # Check MySQL
    mysql_available = check_mysql()
    
    # Create virtual environment
    activate_cmd, pip_cmd = create_virtual_environment()
    
    # Install dependencies
    install_dependencies(pip_cmd)
    
    # Create .env file
    create_env_file()
    
    # Setup directories
    setup_directories()
    
    # Database setup instructions
    if mysql_available:
        create_database()
    else:
        print("⚠ Please install MySQL and then run the database setup commands")
    
    print("\\n=== Setup Complete ===")
    print("\\nNext steps:")
    print("1. Activate virtual environment:")
    print(f"   {activate_cmd}")
    print("\\n2. Configure your .env file with:")
    print("   - Database credentials")
    print("   - Twilio WhatsApp credentials") 
    print("   - Google Cloud service account")
    print("\\n3. Set up MySQL database (see instructions above)")
    print("\\n4. Follow the WHATSAPP_SETUP_GUIDE.md for WhatsApp Business setup")
    print("\\n5. Run the application:")
    print("   python main.py")
    print("\\n6. Test your webhooks:")
    print("   - Client webhook: http://localhost:8000/webhook/client")
    print("   - Therapist webhook: http://localhost:8000/webhook/therapist")

if __name__ == "__main__":
    main()
