"""Test coordinator response handling"""
import sys
import os
import asyncio

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'therapy_booking_app'))

from app.models.database import get_db, SessionLocal
from app.api.webhooks import process_coordinator_response
from app.models.models import User, UserRole, Therapist, Appointment, AppointmentStatus

async def test_coordinator_responses():
    """Test coordinator approval/decline responses"""
    db = SessionLocal()
    try:
        print("Testing coordinator response handling...")
        
        # Check for existing appointments
        appointments = db.query(Appointment).filter(
            Appointment.status == AppointmentStatus.PENDING
        ).all()
        
        print(f"Found {len(appointments)} pending appointments")
        
        if appointments:
            appointment = appointments[0]
            print(f"Testing with appointment {appointment.id}")
            
            # Test APPROVE response
            print("\n--- Testing APPROVE response ---")
            approval_message = f"APPROVE {appointment.id}"
            coordinator_phone = "+97471669569"  # From config
            
            try:
                # Simulate coordinator approval
                result = await process_coordinator_response(
                    db=db,
                    message_text=approval_message,
                    coordinator_phone=coordinator_phone
                )
                print(f"Approval result: {result}")
                
                # Check appointment status
                db.refresh(appointment)
                print(f"Appointment status after approval: {appointment.status.value}")
                
            except Exception as e:
                print(f"Error during approval test: {e}")
                import traceback
                traceback.print_exc()
        
        else:
            print("No pending appointments found. Run test_direct_booking.py first.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def run_coordinator_test():
    """Run the async coordinator test"""
    asyncio.run(test_coordinator_responses())

if __name__ == "__main__":
    run_coordinator_test()