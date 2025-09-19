#!/usr/bin/env python3
"""
Simple test to manually create coordinator user in database
"""
import pymysql
import json

# Database connection
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Ishaq@123',
    database='booking',
    charset='utf8mb4'
)

try:
    with connection.cursor() as cursor:
        # Check current table structure
        cursor.execute("DESCRIBE users")
        print("📋 Users table structure:")
        for row in cursor.fetchall():
            print(f"  {row}")
        
        # Check existing users
        cursor.execute("SELECT phone_number, name, role FROM users")
        users = cursor.fetchall()
        print(f"\n👥 Existing users ({len(users)}):")
        for user in users:
            print(f"  {user}")
        
        # Check if coordinator exists
        cursor.execute("SELECT * FROM users WHERE phone_number = '97471669569'")
        coordinator = cursor.fetchone()
        
        if coordinator:
            print(f"\n✅ Coordinator already exists: {coordinator}")
        else:
            print(f"\n🔧 Creating coordinator user...")
            try:
                cursor.execute(
                    "INSERT INTO users (phone_number, name, role, is_active) VALUES (%s, %s, %s, %s)",
                    ("97471669569", "Coordinator", "coordinator", True)
                )
                connection.commit()
                print("✅ Coordinator created successfully!")
            except Exception as e:
                print(f"❌ Error creating coordinator: {e}")
                
finally:
    connection.close()