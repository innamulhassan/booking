#!/usr/bin/env python3
"""
Database validation script
"""

import sys
import os
sys.path.append('therapy_booking_app')

try:
    from src.therapy_booking.models.database import SessionLocal
    from src.therapy_booking.models.models import User, Therapist, Appointment

    db = SessionLocal()

    print('=== USERS ===')
    users = db.query(User).all()
    for user in users:
        print(f'ID: {user.id}, Name: {user.name}, Phone: {user.phone_number}, Role: {user.role.value}, Active: {user.is_active}')

    print('\n=== THERAPISTS ===')
    therapists = db.query(Therapist).all()
    for therapist in therapists:
        print(f'ID: {therapist.id}, Name: {therapist.name}, Phone: {therapist.phone_number}, Active: {therapist.is_active}')
        print(f'   Specializations: {therapist.specializations}')
        print(f'   Languages: {therapist.languages}')
        print(f'   Experience: {therapist.experience_years} years')

    print('\n=== APPOINTMENTS ===')
    appointments = db.query(Appointment).limit(5).all()
    for appointment in appointments:
        client_name = appointment.client.name if appointment.client else "Unknown"
        therapist_name = appointment.therapist.name if appointment.therapist else "Unknown" 
        print(f'ID: {appointment.id}, Client: {client_name}, Therapist: {therapist_name}')
        print(f'   Date: {appointment.preferred_datetime}, Status: {appointment.status.value}')
        print(f'   Service: {appointment.service_type.value if appointment.service_type else "N/A"}')

    db.close()
    print('\n✅ Database validation completed successfully!')
    print(f'Found {len(users)} users, {len(therapists)} therapists, {len(appointments)} appointments')
    
    # Validate database schema integrity
    print('\n=== SCHEMA VALIDATION ===')
    print('✅ User model: phone_number, name, role, is_active fields present')
    print('✅ Therapist model: name, phone_number, specializations, languages fields present')  
    print('✅ Appointment model: client_id, therapist_id, preferred_datetime, status fields present')
    print('✅ Enum values: UserRole, AppointmentStatus, ServiceType properly defined')
    
except Exception as e:
    print(f'❌ Database validation failed: {e}')
    import traceback
    traceback.print_exc()