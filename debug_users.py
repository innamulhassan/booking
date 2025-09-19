#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from src.therapy_booking.models.database import engine
from src.therapy_booking.models.models import User

def check_existing_data():
    """Check what data already exists in database"""
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Check existing users
        users = db.query(User).all()
        print(f"Existing users: {len(users)}")
        for user in users:
            print(f"  - {user.name} ({user.phone_number}) - Role: {user.role}")
            
        # Check if we can create a simple client user
        print("\nTrying to create a test client user...")
        test_user = User(
            phone_number="+1234567890",
            name="Test Client",
            role="client"  # Try string value directly
        )
        db.add(test_user)
        db.commit()
        print("✅ Client user created successfully")
        
        # Now try coordinator
        print("Trying to create coordinator user...")
        coordinator_test = User(
            phone_number="+9876543210", 
            name="Test Coordinator",
            role="coordinator"
        )
        db.add(coordinator_test)
        db.commit()
        print("✅ Coordinator user created successfully")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_existing_data()