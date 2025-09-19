#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from src.therapy_booking.models.database import engine, SessionLocal
from src.therapy_booking.models.models import (
    Therapist, MainService, TherapistService
)

def reassign_therapist_services():
    """Reassign all therapists to all main services"""
    
    db = SessionLocal()
    
    try:
        # Get all therapists and main services
        therapists = db.query(Therapist).all()
        main_services = db.query(MainService).all()
        
        print(f"Reassigning {len(therapists)} therapists to {len(main_services)} main services...")
        
        # Create therapist-service relationships
        for therapist in therapists:
            for service in main_services:
                therapist_service = TherapistService(
                    therapist_id=therapist.id,
                    main_service_id=service.id,
                    is_available=True,
                    notes="Standard pricing applies"
                )
                db.add(therapist_service)
        
        db.commit()
        
        # Display results
        assignments = db.query(TherapistService).all()
        print(f"\n✅ Successfully created {len(assignments)} therapist-service assignments!")
        
        print(f"\n👩‍⚕️ Therapist Services Summary:")
        for therapist in therapists:
            print(f"  • {therapist.name}:")
            therapist_services = db.query(TherapistService).filter(
                TherapistService.therapist_id == therapist.id
            ).all()
            for ts in therapist_services:
                service = db.query(MainService).filter(MainService.id == ts.main_service_id).first()
                price_qar = service.base_price / 100
                print(f"    - {service.name}: {price_qar} QAR")
        
        print(f"\n🎯 System Ready:")
        print(f"  - All therapists can provide all main services")
        print(f"  - Fixed pricing structure implemented") 
        print(f"  - Extra services rates set by individual therapists")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error reassigning therapist services: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reassign_therapist_services()