#!/usr/bin/env python3
"""
Script to create dummy therapy service data for testing
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.therapy_booking.models.database import SessionLocal, engine
from src.therapy_booking.models.models import (
    User, UserRole, Therapist, Coordinator, MainService, ExtraService,
    TherapistService, TherapistExtraService, ServiceCategory, Base
)

def create_dummy_data():
    """Create dummy data for testing"""
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 1. Create coordinator user and profile
        # Note: Using 'therapist' role temporarily because database doesn't accept 'coordinator' yet
        coordinator_user = User(
            phone_number="+97471234999",  # Changed to avoid duplicate
            name="Sarah Johnson - Coordinator",
            role=UserRole.THERAPIST.value  # Using therapist role temporarily
        )
        db.add(coordinator_user)
        db.commit()
        db.refresh(coordinator_user)
        
        coordinator_profile = Coordinator(
            user_id=coordinator_user.id,
            name="Sarah Johnson",
            phone_number="+97471234999"
        )
        db.add(coordinator_profile)
        
        # 2. Create therapists
        therapists_data = [
            {
                "name": "Dr. Ahmad Al-Rashid",
                "phone_number": "+97471234567",
                "specializations": "Individual Therapy, Anxiety, Depression",
                "experience_years": 8,
                "education": "PhD in Clinical Psychology, University of Dubai",
                "languages": "English, Arabic, Urdu",
                "bio": "Specialized in cognitive behavioral therapy and anxiety disorders"
            },
            {
                "name": "Dr. Fatima Al-Zahra",
                "phone_number": "+97471234568",
                "specializations": "Family Therapy, Couple Counseling, Child Psychology",
                "experience_years": 12,
                "education": "PhD in Family Psychology, American University",
                "languages": "English, Arabic, French",
                "bio": "Expert in family dynamics and relationship counseling"
            },
            {
                "name": "Dr. Omar Hassan",
                "phone_number": "+97471234569",
                "specializations": "Group Therapy, Trauma, PTSD",
                "experience_years": 6,
                "education": "MS in Clinical Psychology, Kuwait University",
                "languages": "English, Arabic",
                "bio": "Specialized in trauma recovery and group therapeutic approaches"
            }
        ]
        
        therapists = []
        for data in therapists_data:
            therapist = Therapist(**data)
            db.add(therapist)
            therapists.append(therapist)
        
        # 3. Create main services
        main_services_data = [
            {
                "name": "Individual Therapy Session",
                "category": ServiceCategory.INDIVIDUAL_THERAPY,
                "description": "One-on-one therapy session with licensed therapist",
                "duration_minutes": 60,
                "base_price": 15000  # 150 AED in cents
            },
            {
                "name": "Couple Therapy Session",
                "category": ServiceCategory.COUPLE_THERAPY,
                "description": "Relationship counseling for couples",
                "duration_minutes": 75,
                "base_price": 20000  # 200 AED in cents
            },
            {
                "name": "Family Therapy Session",
                "category": ServiceCategory.FAMILY_THERAPY,
                "description": "Family counseling session",
                "duration_minutes": 90,
                "base_price": 25000  # 250 AED in cents
            },
            {
                "name": "Group Therapy Session",
                "category": ServiceCategory.GROUP_THERAPY,
                "description": "Group therapy session (max 8 participants)",
                "duration_minutes": 90,
                "base_price": 10000  # 100 AED in cents
            },
            {
                "name": "Initial Consultation",
                "category": ServiceCategory.CONSULTATION,
                "description": "First-time consultation and assessment",
                "duration_minutes": 45,
                "base_price": 12000  # 120 AED in cents
            },
            {
                "name": "Psychological Assessment",
                "category": ServiceCategory.ASSESSMENT,
                "description": "Comprehensive psychological evaluation",
                "duration_minutes": 120,
                "base_price": 30000  # 300 AED in cents
            }
        ]
        
        main_services = []
        for data in main_services_data:
            service = MainService(**data)
            db.add(service)
            main_services.append(service)
        
        # 4. Create extra services
        extra_services_data = [
            {
                "name": "Weekend Session",
                "description": "Additional charge for weekend appointments",
                "duration_minutes": 0,
                "base_price": 5000  # 50 AED extra
            },
            {
                "name": "Home Visit Charge",
                "description": "Travel fee for home visits",
                "duration_minutes": 0,
                "base_price": 8000  # 80 AED extra
            },
            {
                "name": "Extended Session (90 min)",
                "description": "Extended session duration",
                "duration_minutes": 30,
                "base_price": 7500  # 75 AED extra
            },
            {
                "name": "Emergency Session",
                "description": "Same-day or urgent appointment",
                "duration_minutes": 0,
                "base_price": 10000  # 100 AED extra
            },
            {
                "name": "Report Writing",
                "description": "Written psychological report",
                "duration_minutes": 0,
                "base_price": 15000  # 150 AED
            }
        ]
        
        extra_services = []
        for data in extra_services_data:
            service = ExtraService(**data)
            db.add(service)
            extra_services.append(service)
        
        db.commit()
        db.refresh(coordinator_profile)
        for therapist in therapists:
            db.refresh(therapist)
        for service in main_services:
            db.refresh(service)
        for service in extra_services:
            db.refresh(service)
        
        # 5. Assign main services to therapists
        for therapist in therapists:
            for service in main_services:
                # Each therapist can provide all main services
                therapist_service = TherapistService(
                    therapist_id=therapist.id,
                    main_service_id=service.id,
                    is_available=True
                )
                db.add(therapist_service)
        
        # 6. Assign extra services to therapists (selective)
        # Dr. Ahmad - all extra services
        for extra_service in extra_services:
            therapist_extra = TherapistExtraService(
                therapist_id=therapists[0].id,
                extra_service_id=extra_service.id,
                is_available=True
            )
            db.add(therapist_extra)
        
        # Dr. Fatima - weekend, home visit, extended session
        for extra_service in extra_services[:3]:
            therapist_extra = TherapistExtraService(
                therapist_id=therapists[1].id,
                extra_service_id=extra_service.id,
                is_available=True
            )
            db.add(therapist_extra)
        
        # Dr. Omar - weekend, emergency, report writing
        for extra_service in [extra_services[0], extra_services[3], extra_services[4]]:
            therapist_extra = TherapistExtraService(
                therapist_id=therapists[2].id,
                extra_service_id=extra_service.id,
                is_available=True
            )
            db.add(therapist_extra)
        
        db.commit()
        
        print("✅ Dummy data created successfully!")
        print("\n📊 Summary:")
        print(f"  - 1 Coordinator: Sarah Johnson (+97471669569)")
        print(f"  - 3 Therapists: Dr. Ahmad, Dr. Fatima, Dr. Omar")
        print(f"  - 6 Main Services: Individual, Couple, Family, Group, Consultation, Assessment")
        print(f"  - 5 Extra Services: Weekend, Home Visit, Extended, Emergency, Report")
        print(f"  - All therapists can provide all main services")
        print(f"  - Extra services assigned selectively to therapists")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating dummy data: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    create_dummy_data()