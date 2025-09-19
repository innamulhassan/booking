#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from src.therapy_booking.models.database import engine, SessionLocal
from src.therapy_booking.models.models import (
    MainService, ServiceCategory
)

def update_main_services():
    """Update main services with correct pricing structure"""
    
    db = SessionLocal()
    
    try:
        # First, clear therapist_services relationships
        from src.therapy_booking.models.models import TherapistService
        db.query(TherapistService).delete()
        
        # Then clear existing main services
        db.query(MainService).delete()
        db.commit()
        
        # Create new main services with correct pricing
        main_services = [
            {
                "name": "45 Min In-Call Session",
                "category": ServiceCategory.INDIVIDUAL_THERAPY,
                "description": "45-minute therapy session at clinic",
                "duration_minutes": 45,
                "base_price": 20000,  # 200 QAR in fils (200 * 100)
                "service_type": "in_call"
            },
            {
                "name": "1 Hour In-Call Session", 
                "category": ServiceCategory.INDIVIDUAL_THERAPY,
                "description": "60-minute therapy session at clinic",
                "duration_minutes": 60,
                "base_price": 25000,  # 250 QAR in fils (250 * 100)
                "service_type": "in_call"
            },
            {
                "name": "1 Hour Out-Call Session",
                "category": ServiceCategory.INDIVIDUAL_THERAPY, 
                "description": "60-minute home visit session (includes transport)",
                "duration_minutes": 60,
                "base_price": 30000,  # 300 QAR in fils (250 + 50 uber)
                "service_type": "out_call"
            },
            {
                "name": "1.5 Hour In-Call Session",
                "category": ServiceCategory.INDIVIDUAL_THERAPY,
                "description": "90-minute extended therapy session at clinic", 
                "duration_minutes": 90,
                "base_price": 35000,  # 350 QAR in fils (350 * 100)
                "service_type": "in_call"
            },
            {
                "name": "1.5 Hour Out-Call Session",
                "category": ServiceCategory.INDIVIDUAL_THERAPY,
                "description": "90-minute extended home visit session (includes transport)",
                "duration_minutes": 90, 
                "base_price": 40000,  # 400 QAR in fils (350 + 50 uber)
                "service_type": "out_call"
            }
        ]
        
        # Add main services to database
        for service_data in main_services:
            service = MainService(
                name=service_data["name"],
                category=service_data["category"],
                description=service_data["description"],
                duration_minutes=service_data["duration_minutes"],
                base_price=service_data["base_price"],
                is_active=True
            )
            db.add(service)
        
        db.commit()
        
        # Display created services
        services = db.query(MainService).all()
        print("✅ Main services updated successfully!")
        print(f"\n📋 Main Services ({len(services)}):")
        for service in services:
            price_qar = service.base_price / 100  # Convert fils to QAR
            print(f"  • {service.name}: {price_qar} QAR ({service.duration_minutes} min)")
            print(f"    - {service.description}")
        
        print("\n💡 Notes:")
        print("  - All therapists can provide these main services")
        print("  - Extra services rates are set by individual therapists")
        print("  - Out-call prices include 50 QAR transport fee")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating main services: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_main_services()