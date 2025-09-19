#!/usr/bin/env python3
"""
Fix the database role enum to include COORDINATOR and ADMIN
"""
import pymysql

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
        print("🔧 Updating role enum to include coordinator and admin...")
        
        # Update the enum to include all roles
        sql = """
        ALTER TABLE users 
        MODIFY COLUMN role ENUM('CLIENT', 'THERAPIST', 'COORDINATOR', 'ADMIN') 
        NOT NULL DEFAULT 'CLIENT'
        """
        
        cursor.execute(sql)
        connection.commit()
        
        print("✅ Successfully updated role enum!")
        
        # Verify the change
        cursor.execute("DESCRIBE users")
        for row in cursor.fetchall():
            if row[0] == 'role':
                print(f"Updated role column: {row}")
        
        # Now create the coordinator
        print("\n🔧 Creating coordinator user...")
        cursor.execute(
            "INSERT INTO users (phone_number, name, role, is_active) VALUES (%s, %s, %s, %s)",
            ("97471669569", "Coordinator", "COORDINATOR", True)
        )
        connection.commit()
        print("✅ Coordinator created successfully!")
        
        # Verify coordinator exists
        cursor.execute("SELECT phone_number, name, role FROM users WHERE phone_number = '97471669569'")
        coordinator = cursor.fetchone()
        print(f"Coordinator user: {coordinator}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    connection.rollback()
finally:
    connection.close()