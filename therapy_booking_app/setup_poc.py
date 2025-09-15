#!/usr/bin/env python3
"""
Quick POC Setup Script for Therapy Booking Bot
No business registration required!
"""

import os
import subprocess
import sys
from pathlib import Path

def print_step(step, description):
    print(f"\n🔧 Step {step}: {description}")
    print("=" * 50)

def print_success(message):
    print(f"✅ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def print_error(message):
    print(f"❌ {message}")

def run_command(command, check=True):
    """Run a shell command"""
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_python():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error("Python 3.8+ required. Please upgrade Python.")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro}")
    return True

def install_requirements():
    """Install Python requirements"""
    print_info("Installing Python packages...")
    success, stdout, stderr = run_command("pip install -r requirements.txt")
    if success:
        print_success("All packages installed")
        return True
    else:
        print_error(f"Installation failed: {stderr}")
        return False

def setup_database():
    """Setup SQLite database for POC"""
    print_info("Setting up SQLite database for POC...")
    
    # Create a simple SQLite setup for POC
    db_script = '''
import sqlite3
from pathlib import Path

# Create POC database
db_path = Path("therapy_booking_poc.db")
conn = sqlite3.connect(db_path)

# Create tables
cursor = conn.cursor()

# Users table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_number VARCHAR(20) UNIQUE NOT NULL,
        name VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    )
""")

# Appointments table  
cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        service_type VARCHAR(50) NOT NULL,
        appointment_date DATE NOT NULL,
        appointment_time TIME NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
""")

# Conversations table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        conversation_id VARCHAR(100) UNIQUE NOT NULL,
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
""")

# Messages table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER,
        sender_type VARCHAR(20) NOT NULL,
        message_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
    )
""")

conn.commit()
conn.close()

print("✅ SQLite database created successfully!")
print("📁 Database file: therapy_booking_poc.db")
'''
    
    with open('setup_db.py', 'w') as f:
        f.write(db_script)
    
    success, stdout, stderr = run_command("python setup_db.py")
    if success:
        print_success("SQLite database created")
        os.remove('setup_db.py')  # Clean up
        return True
    else:
        print_error(f"Database setup failed: {stderr}")
        return False

def create_env_file():
    """Create environment file for POC"""
    env_content = '''# POC Configuration - SQLite Mode
# Copy from .env.poc and customize

# Database (SQLite for POC)
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=therapy_booking_poc.db
DB_PORT=3306

# For SQLite mode (uncomment this line)
DATABASE_URL=sqlite:///./therapy_booking_poc.db

# Twilio (create free account at https://www.twilio.com/try-twilio)
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
WHATSAPP_SID=your_account_sid_here  
WHATSAPP_TOKEN=your_auth_token_here

# Sandbox mode (no business required)
SANDBOX_MODE=true
TWILIO_WHATSAPP_NUMBER=+14155238886

# Gemini API (free at https://aistudio.google.com/app/apikey)  
GEMINI_API_KEY=your_gemini_api_key_here

# Application
SECRET_KEY=poc-secret-2024
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Your WhatsApp for testing
THERAPIST_PHONE=+1234567890
'''
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print_success("Created .env file")
        print_info("Please edit .env file with your API keys")
    else:
        print_info(".env file already exists")

def main():
    """Main setup function"""
    print("🩺 Therapy Booking Bot - POC Setup")
    print("==================================")
    print("This will set up your bot for testing WITHOUT business registration!")
    
    # Step 1: Check Python
    print_step(1, "Checking Python version")
    if not check_python():
        return
    
    # Step 2: Install requirements
    print_step(2, "Installing requirements")
    if not install_requirements():
        print_error("Please fix package installation issues before continuing")
        return
    
    # Step 3: Setup database  
    print_step(3, "Setting up database")
    if not setup_database():
        print_error("Please fix database issues before continuing")
        return
    
    # Step 4: Create env file
    print_step(4, "Creating environment configuration")
    create_env_file()
    
    # Step 5: Instructions
    print_step(5, "Next Steps")
    print("""
🎉 POC Setup Complete!

Next steps to test your bot:

1. 📝 Edit .env file with your API keys:
   • Get Twilio account: https://www.twilio.com/try-twilio  
   • Get Gemini API key: https://aistudio.google.com/app/apikey

2. 🚀 Start the server:
   python main.py

3. 🌐 Test in browser:
   http://localhost:8000/demo

4. 📱 Test with WhatsApp (optional):
   • Install ngrok: npm install -g ngrok
   • Run: ngrok http 8000  
   • Set webhook in Twilio console

📚 For detailed WhatsApp setup, see:
   • QUICK_POC_SETUP.md
   • WHATSAPP_SETUP_GUIDE.md
    """)
    
    print_success("Setup completed! Happy testing! 🎉")

if __name__ == "__main__":
    main()
