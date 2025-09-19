#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql

def get_enum_values():
    """Check actual enum values in database"""
    # Use hardcoded connection details
    user = "booking_user"
    password = "booking_pass"
    host = "localhost"
    database = "booking"
    
    connection = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    
    try:
        with connection.cursor() as cursor:
            # Get table structure
            cursor.execute("SHOW CREATE TABLE users")
            result = cursor.fetchone()
            print("Users table structure:")
            print(result[1])
            
            # Check existing data
            print("\n" + "="*50)
            cursor.execute("SELECT id, name, phone_number, role FROM users")
            results = cursor.fetchall()
            print(f"Existing users ({len(results)}):")
            for row in results:
                print(f"  ID: {row[0]}, Name: {row[1]}, Phone: {row[2]}, Role: {row[3]}")
                
    finally:
        connection.close()

if __name__ == "__main__":
    get_enum_values()