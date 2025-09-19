#!/usr/bin/env python3
"""
Check database schema and fix coordinator role issue
"""
import sys
import os

# Add the therapy_booking_app directory to path
app_path = os.path.join(os.path.dirname(__file__), 'therapy_booking_app')
sys.path.insert(0, app_path)

from app.config.database import SessionLocal
from app.models.models import User, UserRole
from sqlalchemy import text

def check_database_schema():
    """Check the users table schema"""
    db = SessionLocal()
    try:
        # Check table structure
        result = db.execute(text("DESCRIBE users"))
        print("Users table schema:")
        for row in result:
            print(f"  {row}")
        
        # Check existing users
        users = db.query(User).all()
        print(f"\nExisting users: {len(users)}")
        for user in users:
            print(f"  {user.phone_number}: {user.role} (type: {type(user.role)})")
            
        # Test enum values
        print(f"\nUserRole enum values:")
        for role in UserRole:
            print(f"  {role.name} = '{role.value}'")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

def fix_coordinator_user():
    """Try to create coordinator user directly"""
    db = SessionLocal()
    try:
        # Check if coordinator already exists
        coordinator = db.query(User).filter(User.phone_number == "97471669569").first()
        if coordinator:
            print(f"Coordinator exists: {coordinator.name}, role: {coordinator.role}")
            return
        
        # Create coordinator with correct enum value
        coordinator = User(
            phone_number="97471669569",
            name="Coordinator",
            role=UserRole.COORDINATOR
        )
        
        db.add(coordinator)
        db.commit()
        db.refresh(coordinator)
        
        print(f"✅ Created coordinator: {coordinator.name}, role: {coordinator.role}")
        
    except Exception as e:
        print(f"❌ Error creating coordinator: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔍 Checking database schema...")
    check_database_schema()
    print("\n🔧 Attempting to create coordinator...")
    fix_coordinator_user()