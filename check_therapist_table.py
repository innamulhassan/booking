"""Check what therapists table actually looks like"""
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'therapy_booking_app'))

from app.models.database import get_db, SessionLocal

def check_therapist_table():
    """Check therapists table structure with raw SQL"""
    db = SessionLocal()
    try:
        from sqlalchemy import text
        result = db.execute(text("DESCRIBE therapists"))
        print("Therapists table structure:")
        for row in result:
            print(f"  {row[0]} - {row[1]} - {row[2]} - {row[3]}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_therapist_table()