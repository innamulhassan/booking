"""
Ultramsg WhatsApp Service
Drop-in replacement for ChatAPI
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os

# Add the parent directory to the path to find config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'other_scripts'))

try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    from other_scripts.environment_config import get_config
    env_config = get_config()
except ImportError:
    env_config = None

from config.settings import config

logger = logging.getLogger(__name__)

class UltramsgService:
    """
    Ultramsg WhatsApp API integration
    Handles WhatsApp messaging for therapy booking system
    """
    
    def __init__(self):
        # Use environment config if available, otherwise fallback to legacy config
        if env_config:
            self.instance_id = env_config.ULTRAMSG_INSTANCE_ID
            self.token = env_config.ULTRAMSG_TOKEN
            self.base_url = env_config.ULTRAMSG_BASE_URL
            self.clinic_name = env_config.BUSINESS_NAME
            self.therapist_name = getattr(env_config, 'THERAPIST_NAME', 'Dr. Smith')
            self.clinic_address = getattr(env_config, 'CLINIC_ADDRESS', '123 Health St, City')
            
            # Critical phone numbers from environment
            self.agent_phone = env_config.AGENT_PHONE_NUMBER
            self.therapist_phone = env_config.COORDINATOR_PHONE_NUMBER
            
            logger.info(f"✅ Using environment config - Instance: {self.instance_id}")
            logger.info(f"📞 Agent: {self.agent_phone}, Therapist: {self.therapist_phone}")
        else:
            # Fallback to legacy config
            self.instance_id = config.ULTRAMSG_INSTANCE_ID
            self.token = config.ULTRAMSG_TOKEN
            self.base_url = config.ULTRAMSG_BASE_URL
            self.clinic_name = getattr(config, 'CLINIC_NAME', 'Therapy Clinic')
            self.therapist_name = getattr(config, 'THERAPIST_NAME', 'Dr. Smith')
            self.clinic_address = getattr(config, 'CLINIC_ADDRESS', '123 Health St, City')
            
            # Use fixed phone numbers if not in legacy config
            self.agent_phone = getattr(config, 'AGENT_PHONE_NUMBER', '+97451334514')
            self.therapist_phone = getattr(config, 'COORDINATOR_PHONE_NUMBER', '+97471669569')
            
            logger.info(f"⚠️  Using legacy config - Instance: {self.instance_id}")
        
        self.session = None
        logger.info(f"Ultramsg Service initialized - Instance: {self.instance_id}")
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def send_message(self, to_number: str, message: str) -> dict:
        """Send WhatsApp message via Ultramsg API"""
        try:
            session = await self._get_session()
            
            # Clean phone number (remove whatsapp: prefix if present)
            phone = to_number.replace('whatsapp:', '').replace('+', '')
            
            url = f"{self.base_url}/{self.instance_id}/messages/chat?token={self.token}"
            
            payload = {
                'to': phone,
                'body': message,
                'priority': 10  # High priority for therapy messages
            }
            
            async with session.post(url, data=payload) as response:
                result = await response.json()
                
                if result.get("sent"):
                    logger.info(f"Message sent successfully to {phone}")
                    return {
                        "success": True,
                        "message_id": result.get("id"),
                        "status": "sent"
                    }
                else:
                    logger.error(f"Failed to send message: {result}")
                    return {
                        "success": False, 
                        "error": result.get("error", "Unknown error")
                    }
                    
        except Exception as e:
            logger.error(f"Error sending message via Ultramsg: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_therapeutic_message(self, phone: str, message: str, message_type: str = "general") -> dict:
        """Send message with therapy-specific formatting"""
        
        # Format message based on type
        formatted_message = self._format_therapeutic_message(message, message_type)
        
        return await self.send_message(phone, formatted_message)
    
    def _format_therapeutic_message(self, message: str, message_type: str) -> str:
        """Format messages for therapy practice"""
        
        if message_type == "appointment_confirmation":
            return f"""
🩺 *Appointment Confirmation*

{message}

📞 Questions? Reply to this message
🏥 {self.clinic_name}
👨‍⚕️ {self.therapist_name}

We're looking forward to supporting your wellness journey! 🌱
            """.strip()
            
        elif message_type == "appointment_reminder":
            return f"""
⏰ *Gentle Reminder*

{message}

💡 *Preparation Tips:*
• Arrive 5 minutes early
• Bring any questions you may have
• Take a moment to center yourself

📍 Location: {self.clinic_address}
🤝 Looking forward to our session
            """.strip()
            
        elif message_type == "welcome":
            return f"""
👋 *Welcome to {self.clinic_name}*

{message}

I'm {self.therapist_name}, and I'm here to support you.

🌟 *Let's find the right time for you:*

🌅 Morning (9am-12pm)
🌤️ Afternoon (12pm-5pm) 
🌙 Evening (5pm-8pm)

What works best with your schedule?
            """.strip()
            
        elif message_type == "service_inquiry":
            return f"""
🌿 *Our Therapy Services*

{message}

💚 *All sessions include:*
• Confidential & secure environment
• Personalized treatment approach
• Professional & caring support

Which service interests you most?
            """.strip()
            
        elif message_type == "availability_check":
            return f"""
📅 *Available Appointments*

{message}

✅ To book: Reply with your preferred time
📞 Questions: Feel free to ask anything
🔄 Rescheduling: Always available if needed

What time works for you?
            """.strip()
            
        else:
            # General therapeutic communication
            return f"{message}\n\nHow can I further assist you today? 💙"
    
    async def send_appointment_card(self, phone: str, appointment_data: dict) -> dict:
        """Send structured appointment information"""
        
        service_emojis = {
            "in-call": "📞",
            "out-call": "🚗",
            "home-visit": "🏠", 
            "clinic-visit": "🏥"
        }
        
        emoji = service_emojis.get(appointment_data.get('service_type', ''), "🩺")
        
        card_message = f"""
📋 *Appointment Details*

👤 Client: {appointment_data.get('client_name', 'You')}
🗓️ Date: {appointment_data.get('date')}
⏰ Time: {appointment_data.get('time')}
{emoji} Service: {appointment_data.get('service_type', 'Therapy Session')}
📍 Location: {appointment_data.get('location', self.clinic_address)}

✅ Status: Confirmed

💬 *Need changes?*
• Reply RESCHEDULE for new time
• Reply CANCEL to cancel
• Reply CONFIRM to acknowledge

We're looking forward to seeing you! 🌟
        """.strip()
        
        return await self.send_therapeutic_message(phone, card_message, "appointment_confirmation")
    
    async def send_service_menu(self, phone: str) -> dict:
        """Send therapy services menu"""
        
        services_message = """
*Our Therapy Services:*

📞 *In-Call Therapy*
   • Video/phone sessions from home
   • 50 minutes • $120

🏥 *Clinic Visit*  
   • In-person at our office
   • Private, comfortable setting
   • 50 minutes • $150

🏠 *Home Visit*
   • Therapy at your location
   • Maximum comfort & privacy
   • 60 minutes • $200

🚗 *Mobile Therapy*
   • Meet at convenient location
   • Parks, cafes, neutral spaces
   • 50 minutes • $175

What type of session would you prefer?
        """.strip()
        
        return await self.send_therapeutic_message(phone, services_message, "service_inquiry")
    
    async def send_availability_slots(self, phone: str, available_slots: List[dict]) -> dict:
        """Send available appointment times"""
        
        if not available_slots:
            message = """
*Currently Fully Booked*

I don't have immediate openings, but I'd love to help you find a time.

📅 *Options:*
• Join waiting list for cancellations
• Schedule for next available (1-2 weeks)
• Emergency consultations available

What would you prefer?
            """.strip()
        else:
            slots_text = ""
            for slot in available_slots:
                day_emoji = self._get_day_emoji(slot['date'])
                slots_text += f"{day_emoji} *{slot['date']}* at {slot['time']}\n"
            
            message = f"""
*Available Appointments:*

{slots_text}

💡 *Session Details:*
• Duration: {available_slots[0].get('duration', '50')} minutes
• Confirmation: Sent immediately
• Rescheduling: Easy and flexible

Which time works best for you?
            """.strip()
        
        return await self.send_therapeutic_message(phone, message, "availability_check")
    
    def _get_day_emoji(self, date_str: str) -> str:
        """Get emoji for day of week"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            day = date_obj.strftime("%A")
            
            day_emojis = {
                "Monday": "🌅",
                "Tuesday": "🌤️",
                "Wednesday": "🌞", 
                "Thursday": "🌻",
                "Friday": "🌟",
                "Saturday": "🌈",
                "Sunday": "🌙"
            }
            return day_emojis.get(day, "📅")
        except:
            return "📅"
    
    async def send_document(self, phone: str, document_url: str, caption: str = "") -> dict:
        """Send document (intake forms, etc.)"""
        try:
            session = await self._get_session()
            phone = phone.replace('whatsapp:', '').replace('+', '')
            
            url = f"{self.base_url}/{self.instance_id}/messages/document"
            
            payload = {
                'token': self.token,
                'to': phone,
                'document': document_url,
                'caption': caption,
                'priority': 10
            }
            
            async with session.post(url, data=payload) as response:
                result = await response.json()
                return result
                
        except Exception as e:
            logger.error(f"Error sending document: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_location(self, phone: str, latitude: float, longitude: float, address: str) -> dict:
        """Send location for clinic visits"""
        try:
            session = await self._get_session()
            phone = phone.replace('whatsapp:', '').replace('+', '')
            
            url = f"{self.base_url}/{self.instance_id}/messages/location"
            
            payload = {
                'token': self.token,
                'to': phone,
                'lat': latitude,
                'lng': longitude,
                'address': address,
                'priority': 10
            }
            
            async with session.post(url, data=payload) as response:
                result = await response.json()
                
                # Follow up with directions
                if result.get('sent'):
                    await asyncio.sleep(2)
                    follow_up = f"""
📍 *{self.clinic_name} Location*

{address}

🅿️ Parking: Available on-site
🚇 Transit: Bus stop nearby  
♿ Accessibility: Wheelchair accessible

See you at your appointment! 🏥
                    """.strip()
                    
                    await self.send_message(phone, follow_up)
                
                return result
                
        except Exception as e:
            logger.error(f"Error sending location: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def handle_emergency_response(self, phone: str) -> dict:
        """Handle crisis/emergency keywords"""
        
        emergency_message = """
🚨 *Important - Crisis Resources*

If you're experiencing a mental health emergency:

📞 *Immediate Help:*
• National Suicide Prevention Lifeline: 988
• Crisis Text Line: Text HOME to 741741  
• Emergency Services: 911

🏥 *Local Support:*
• {clinic_name}: {emergency_contact}
• Walk-in Crisis Center Available

💙 *You're not alone. Help is available 24/7.*

Please reach out to emergency services if you're in immediate danger.
        """.format(
            clinic_name=self.clinic_name,
            emergency_contact=getattr(config, 'EMERGENCY_CONTACT', '(555) 123-4567')
        ).strip()
        
        return await self.send_message(phone, emergency_message)
    
    def get_coordinator_phone(self) -> Optional[str]:
        """Get coordinator phone number from environment config"""
        try:
            if env_config and hasattr(env_config, 'COORDINATOR_PHONE_NUMBER'):
                return env_config.COORDINATOR_PHONE_NUMBER
            return getattr(config, 'COORDINATOR_PHONE_NUMBER', None)
        except Exception as e:
            logger.error(f"Could not get coordinator phone: {e}")
            return None
    
    async def get_instance_status(self) -> dict:
        """Check if Ultramsg instance is active"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/{self.instance_id}/instance/status"
            
            params = {'token': self.token}
            
            async with session.get(url, params=params) as response:
                result = await response.json()
                return result
                
        except Exception as e:
            logger.error(f"Error checking instance status: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def create_webhook_response(self, message: str) -> str:
        """Create response for incoming messages (if using webhooks)"""
        # Ultramsg doesn't require XML responses like Twilio
        return ""
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

# Initialize service
ultramsg_service = UltramsgService()
