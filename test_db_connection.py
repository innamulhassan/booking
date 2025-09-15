#!/usr/bin/env python3
"""
Simple Database Connection Test
Tests database connectivity with environment variables
"""

import os
import sys
from dotenv import load_dotenv
import pymysql

def test_database_connection():
    """Test database connection with environment variables"""
    
    print("🔍 DATABASE CONNECTION TEST")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'booking'),
    }
    
    print(f"Testing connection to: {db_config['user']}@{db_config['host']}:{db_config['port']}")
    print(f"Database: {db_config['database']}")
    print(f"Password length: {len(db_config['password'])} characters")
    
    try:
        # Test connection without database first
        print("\n📡 Testing MySQL server connection...")
        conn = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password']
        )
        print("✅ MySQL server connection successful!")
        
        # Test database existence
        print(f"\n🔍 Checking if database '{db_config['database']}' exists...")
        cursor = conn.cursor()
        cursor.execute(f"SHOW DATABASES LIKE '{db_config['database']}'")
        result = cursor.fetchone()
        
        if result:
            print(f"✅ Database '{db_config['database']}' exists!")
            
            # Connect to the database
            conn.select_db(db_config['database'])
            print(f"✅ Connected to database '{db_config['database']}'")
            
            # Show tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            if tables:
                print(f"\n📋 Tables in database:")
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = cursor.fetchone()[0]
                    print(f"   - {table[0]} ({count} records)")
            else:
                print(f"\n📋 Database '{db_config['database']}' is empty (no tables)")
        else:
            print(f"❌ Database '{db_config['database']}' does not exist")
            print(f"💡 Create it with: CREATE DATABASE {db_config['database']};")
        
        cursor.close()
        conn.close()
        
        return True
        
    except pymysql.Error as e:
        print(f"❌ Database connection failed: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Check if MySQL service is running")
        print("   2. Verify username and password in .env file")
        print("   3. Ensure database exists")
        print("   4. Check firewall settings")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    print("\n" + "=" * 50)
    if success:
        print("🎉 Database connection test completed!")
    else:
        print("💥 Database connection test failed!")
        sys.exit(1)