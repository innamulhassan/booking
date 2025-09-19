#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from src.therapy_booking.models.database import engine
from src.therapy_booking.models.models import User, UserRole

def test_roles():
    """Test what role values work"""
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Check existing users and what roles work
        print("Checking existing users...")
        users = db.query(User).all()
        print(f"Found {len(users)} existing users:")
        for user in users:
            print(f"  - {user.name} ({user.phone_number}) - Role: {user.role}")
        
        # Test different role values to see what's accepted
        print("\nTesting role values...")
        test_roles = ["client", "coordinator", "therapist"]
        
        for role in test_roles:
            try:
                # Use a unique phone number for each test
                phone = f"+123000{hash(role) % 10000}"
                test_user = User(
                    phone_number=phone,
                    name=f"Test {role}",
                    role=role
                )
                db.add(test_user)
                db.flush()  # Test without committing
                print(f"  ✅ Role '{role}' works")
                db.rollback()  # Rollback the test
            except Exception as e:
                db.rollback()
                print(f"  ❌ Role '{role}' fails: {str(e)[:100]}...")
        
        print("\nTesting UserRole enum values...")
        for role_enum in UserRole:
            try:
                phone = f"+124000{hash(role_enum.name) % 10000}"
                test_user = User(
                    phone_number=phone,
                    name=f"Test {role_enum.name}",
                    role=role_enum
                )
                db.add(test_user)
                db.flush()
                print(f"  ✅ UserRole.{role_enum.name} ({role_enum.value}) works")
                db.rollback()
            except Exception as e:
                db.rollback()
                print(f"  ❌ UserRole.{role_enum.name} ({role_enum.value}) fails: {str(e)[:100]}...")
                
    finally:
        db.close()

if __name__ == "__main__":
    test_roles()