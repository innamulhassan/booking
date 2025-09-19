"""Test booking directly with client info"""
import sys
import os
import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'therapy_booking_app'))

from app.models.database import get_db, SessionLocal
from app.services.booking_service import booking_service
from app.models.models import User, UserRole, Therapist, Appointment, AppointmentStatus, ServiceType

def test_direct_booking():
    """Test booking directly through booking service"""
    db = SessionLocal()
    try:
        print("Testing direct booking...")
        
        # Get a client and therapist
        client = db.query(User).filter(User.role == UserRole.CLIENT).first()
        therapist = db.query(Therapist).filter(Therapist.is_active == True).first()
        
        if not client:
            print("No client found")
            return
        if not therapist:
            print("No therapist found")
            return
            
        print(f"Client: {client.name} ({client.phone_number})")
        print(f"Therapist: {therapist.name} ({therapist.phone_number})")
        
        # Create booking data
        booking_data = {
            'datetime': '2024-12-25 10:00:00',
            'service_type': 'in_call',
            'therapist_id': therapist.id,
            'service_description': 'Individual Therapy Session - Test booking'
        }
        
        # Create appointment
        appointment = booking_service.create_pending_appointment(
            db=db,
            client_id=client.id,
            booking_data=booking_data
        )
        
        print(f"Created appointment: ID={appointment.id}, Status={appointment.status.value}")
        print(f"Service: {appointment.service_description}")
        print(f"Date: {appointment.preferred_datetime}")
        
        # Test coordinator notification
        try:
            import asyncio
            from app.services.ultramsg_service import ultramsg_service
            
            # Get coordinator phone from environment config
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'other_scripts'))
            from other_scripts.environment_config import get_config
            env_config = get_config()
            coordinator_phone = env_config.COORDINATOR_PHONE_NUMBER
            
            coordinator_message = f"""🔔 NEW BOOKING REQUEST #{appointment.id}

📱 Client: {client.name} ({client.phone_number})
📅 Date & Time: 2024-12-25 at 10:00
🏥 Service: Individual Therapy
👨‍⚕️ Therapist: {therapist.name}
💰 Price: 200 QAR (estimate)
📝 Notes: Test booking

Please reply:
✅ "APPROVE {appointment.id}" - to confirm booking
❌ "DECLINE {appointment.id}" - to reject booking
📝 "MODIFY {appointment.id} [reason]" - to request changes

Client is waiting for confirmation."""

            print(f"Coordinator phone: {coordinator_phone}")
            print("Coordinator message:")
            print(coordinator_message)
            
            # Send async message (just simulate for now)
            print("✅ Coordinator notification would be sent successfully")
            
        except Exception as e:
            print(f"Error with coordinator notification: {e}")
        
        print("✅ Booking test completed successfully!")
        
    except Exception as e:
        print(f"Error during booking: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_direct_booking()