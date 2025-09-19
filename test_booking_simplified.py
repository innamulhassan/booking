"""Test if the booking system works with simplified schema"""
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'therapy_booking_app'))

from app.models.database import get_db, SessionLocal
from app.services.adk_agent_service import book_appointment
from app.models.models import User, UserRole, Therapist, Appointment, AppointmentStatus

def test_booking_with_coordinator():
    """Test the booking flow end-to-end"""
    db = SessionLocal()
    try:
        print("Testing booking with simplified schema...")
        
        # Check if we have users and therapists
        users = db.query(User).limit(5).all()
        print(f"Found {len(users)} users")
        for user in users:
            print(f"  - {user.name}: {user.phone_number} ({user.role.value if user.role else 'no role'})")
        
        therapists = db.query(Therapist).limit(5).all()
        print(f"Found {len(therapists)} therapists")
        for therapist in therapists:
            print(f"  - {therapist.name}: {therapist.phone_number}")
            
        # Test booking
        if users and therapists:
            client = users[0]
            therapist = therapists[0]
            
            print(f"\nTesting booking for client: {client.name}")
            
            booking_result = book_appointment(
                date="2024-12-25",
                time="10:00",
                service_name="Individual Therapy",
                therapist_name=therapist.name,
                description="Test booking",
                extra_services=""
            )
            
            print(f"Booking result: {booking_result}")
            
            if booking_result.get('status') == 'success':
                appointment_id = booking_result.get('appointment_id')
                appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
                print(f"Created appointment: {appointment.id} - Status: {appointment.status.value}")
                print(f"Service description: {appointment.service_description}")
            else:
                print(f"Booking failed: {booking_result.get('error_message')}")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_booking_with_coordinator()