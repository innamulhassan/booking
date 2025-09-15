#!/usr/bin/env python3
"""
Complete system cleanup: Clear database, logs, and reset everything
"""

import os
import sys
import shutil
import sqlite3
from pathlib import Path

def clear_database():
    """Clear all tables in the database"""
    try:
        # Path to database
        db_path = Path("..") / "therapy_booking_app" / "therapy_booking.db"
        
        if db_path.exists():
            print("🗄️ Clearing database tables...")
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            # Clear all tables
            for table in tables:
                table_name = table[0]
                if table_name != 'sqlite_sequence':  # Skip system table
                    print(f"   🧹 Clearing table: {table_name}")
                    cursor.execute(f"DELETE FROM {table_name}")
            
            conn.commit()
            conn.close()
            
            print("✅ Database cleared successfully!")
        else:
            print("ℹ️ Database file not found - will be created fresh")
            
    except Exception as e:
        print(f"❌ Error clearing database: {e}")

def clear_logs():
    """Clear all log files"""
    try:
        print("📋 Clearing log files...")
        
        log_dirs = [
            Path("..") / "logs",
            Path("..") / "therapy_booking_app" / "logs"
        ]
        
        for log_dir in log_dirs:
            if log_dir.exists():
                print(f"   🧹 Clearing directory: {log_dir}")
                shutil.rmtree(log_dir)
                log_dir.mkdir(exist_ok=True)  # Recreate empty directory
        
        print("✅ Log files cleared successfully!")
        
    except Exception as e:
        print(f"❌ Error clearing logs: {e}")

def clear_cache():
    """Clear Python cache files"""
    try:
        print("🔄 Clearing Python cache...")
        
        # Find and remove __pycache__ directories
        for root, dirs, files in os.walk(".."):
            for dir_name in dirs:
                if dir_name == "__pycache__":
                    cache_path = Path(root) / dir_name
                    print(f"   🧹 Removing: {cache_path}")
                    shutil.rmtree(cache_path)
        
        print("✅ Cache cleared successfully!")
        
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")

def stop_processes():
    """Stop any running Python processes"""
    try:
        print("🛑 Stopping running processes...")
        
        # Use PowerShell to stop processes
        import subprocess
        
        cmd = 'Get-Process | Where-Object {$_.ProcessName -eq "python" -and $_.Path -like "*work*play*booking*"} | Stop-Process -Force'
        subprocess.run(["powershell", "-Command", cmd], capture_output=True)
        
        print("✅ Processes stopped!")
        
    except Exception as e:
        print(f"ℹ️ Process cleanup: {e}")

def main():
    """Complete cleanup"""
    print("🧹 COMPLETE SYSTEM CLEANUP")
    print("=" * 50)
    
    # Stop processes first
    stop_processes()
    
    # Clear everything
    clear_database()
    clear_logs()
    clear_cache()
    
    print("\n" + "=" * 50)
    print("✅ CLEANUP COMPLETE!")
    print("\nNext steps:")
    print("1. Start fresh webhook server")
    print("2. Monitor logs carefully") 
    print("3. Test with single message")
    print("=" * 50)

if __name__ == "__main__":
    main()