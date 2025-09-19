"""
Ultramsg WhatsApp Service
Migrated to new package structure with improved error handling and configuration management.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..core.config import get_settings

logger = logging.getLogger(__name__)

class UltramsgService:
    """
    Ultramsg WhatsApp API integration
    Handles WhatsApp messaging for therapy booking system
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        # UltraMsg configuration
        self.instance_id = self.settings.ultramsg_instance_id
        self.token = self.settings.ultramsg_token
        self.base_url = self.settings.ultramsg_base_url
        
        # Business information
        self.clinic_name = self.settings.clinic_name or "Wellness Therapy Center"
        self.therapist_name = self.settings.therapist_name or "Dr. Sarah"
        self.clinic_address = self.settings.clinic_address or "123 Wellness Street, City"
        
        # Key phone numbers
        self.agent_phone = self.settings.agent_phone_number
        self.coordinator_phone = self.settings.coordinator_phone_number
        
        # Session management
        self.session = None
        
        logger.info(f"UltraMsg Service initialized - Instance: {self.instance_id}")
        logger.info(f"Business: {self.clinic_name}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def send_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send WhatsApp message via Ultramsg API"""
        try:
            session = await self._get_session()
            
            # Clean phone number (remove whatsapp: prefix if present)
            phone = self._clean_phone_number(to_number)
            
            url = f"{self.base_url}/{self.instance_id}/messages/chat"
            
            payload = {
                'to': phone,
                'body': message,
                'priority': 10,  # High priority for therapy messages
                'token': self.token
            }
            
            async with session.post(url, data=payload) as response:
                result = await response.json()
                
                if result.get("sent"):
                    logger.info(f"Message sent successfully to {phone}")
                    return {
                        "success": True,
                        "id": result.get("id"),
                        "status": "sent",
                        "message_id": result.get("id")
                    }
                else:
                    error_msg = result.get("error", "Unknown error")
                    logger.error(f"Failed to send message to {phone}: {error_msg}")
                    return {
                        "success": False, 
                        "error": error_msg,
                        "raw_response": result
                    }
                    
        except Exception as e:
            logger.error(f"Error sending message via Ultramsg: {str(e)}")
            return {
                "success": False, 
                "error": str(e)
            }
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and format phone number for UltraMsg"""
        if not phone:
            raise ValueError("Phone number is required")
        
        # Remove common prefixes and formatting
        cleaned = phone.replace('whatsapp:', '').replace('+', '').replace('-', '').replace(' ', '')
        
        # Ensure it's all digits
        if not cleaned.isdigit():
            raise ValueError(f"Invalid phone number format: {phone}")
        
        return cleaned
    
    async def send_therapeutic_message(self, phone: str, message: str, message_type: str = "general") -> Dict[str, Any]:
        """Send message with therapy-specific formatting"""
        formatted_message = self._format_therapeutic_message(message, message_type)
        return await self.send_message(phone, formatted_message)
    
    def _format_therapeutic_message(self, message: str, message_type: str) -> str:
        """Format messages for therapy practice"""
        
        formatting_templates = {
            "appointment_confirmation": f"""
🩺 *Appointment Confirmation*

{message}

📞 Questions? Reply to this message
🏥 {self.clinic_name}
👨‍⚕️ {self.therapist_name}

We're looking forward to supporting your wellness journey! 🌱
            """.strip(),
            
            "appointment_reminder": f"""
⏰ *Gentle Reminder*

{message}

💡 *Preparation Tips:*
• Arrive 5 minutes early
• Bring any questions you may have
• Take a moment to center yourself

📍 Location: {self.clinic_address}
🤝 Looking forward to our session
            """.strip(),
            
            "welcome": f"""
👋 *Welcome to {self.clinic_name}*

{message}

I'm {self.therapist_name}, and I'm here to support you.

🌟 *Let's find the right time for you:*

🌅 Morning (9am-12pm)
🌤️ Afternoon (12pm-5pm) 
🌙 Evening (5pm-8pm)

What works best with your schedule?
            """.strip(),
            
            "service_inquiry": f"""
🌿 *Our Therapy Services*

{message}

💚 *All sessions include:*
• Confidential & secure environment
• Personalized treatment approach
• Professional & caring support

Which service interests you most?
            """.strip(),
            
            "availability_check": f"""
📅 *Available Appointments*

{message}

✅ To book: Reply with your preferred time
📞 Questions: Feel free to ask anything
🔄 Rescheduling: Always available if needed

What time works for you?
            """.strip()
        }
        
        if message_type in formatting_templates:
            return formatting_templates[message_type]
        else:
            # General therapeutic communication
            return f"{message}\n\nHow can I further assist you today? 💙"
    
    async def send_appointment_card(self, phone: str, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send structured appointment information"""
        
        service_emojis = {
            "in_call": "📞",
            "out_call": "🚗",
            "home_visit": "🏠", 
            "clinic_visit": "🏥"
        }
        
        service_type = appointment_data.get('service_type', '').lower()
        emoji = service_emojis.get(service_type, "🩺")
        
        card_message = f"""
📋 *Appointment Details*

👤 Client: {appointment_data.get('client_name', 'You')}
🗓️ Date: {appointment_data.get('date')}
⏰ Time: {appointment_data.get('time')}
{emoji} Service: {appointment_data.get('service_name', 'Therapy Session')}
📍 Location: {appointment_data.get('location', self.clinic_address)}

✅ Status: Confirmed

💬 *Need changes?*
• Reply RESCHEDULE for new time
• Reply CANCEL to cancel
• Reply CONFIRM to acknowledge

We're looking forward to seeing you! 🌟
        """.strip()
        
        return await self.send_therapeutic_message(phone, card_message, "appointment_confirmation")
    
    async def send_service_menu(self, phone: str) -> Dict[str, Any]:
        """Send therapy services menu"""
        
        services_message = f"""
*Our Therapy Services at {self.clinic_name}:*

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
    
    async def send_availability_slots(self, phone: str, available_slots: List[Dict[str, Any]]) -> Dict[str, Any]:
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
            
            duration = available_slots[0].get('duration', '50') if available_slots else '50'
            message = f"""
*Available Appointments:*

{slots_text}

💡 *Session Details:*
• Duration: {duration} minutes
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
        except Exception:
            return "📅"
    
    async def send_document(self, phone: str, document_url: str, caption: str = "") -> Dict[str, Any]:
        """Send document (intake forms, etc.)"""
        try:
            session = await self._get_session()
            phone_cleaned = self._clean_phone_number(phone)
            
            url = f"{self.base_url}/{self.instance_id}/messages/document"
            
            payload = {
                'token': self.token,
                'to': phone_cleaned,
                'document': document_url,
                'caption': caption,
                'priority': 10
            }
            
            async with session.post(url, data=payload) as response:
                result = await response.json()
                
                if result.get('sent'):
                    logger.info(f"Document sent to {phone_cleaned}")
                    return {"success": True, "id": result.get("id")}
                else:
                    logger.error(f"Document send failed: {result}")
                    return {"success": False, "error": result.get("error", "Unknown error")}
                
        except Exception as e:
            logger.error(f"Error sending document: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_location(self, phone: str, latitude: float, longitude: float, address: str) -> Dict[str, Any]:
        """Send location for clinic visits"""
        try:
            session = await self._get_session()
            phone_cleaned = self._clean_phone_number(phone)
            
            url = f"{self.base_url}/{self.instance_id}/messages/location"
            
            payload = {
                'token': self.token,
                'to': phone_cleaned,
                'lat': latitude,
                'lng': longitude,
                'address': address,
                'priority': 10
            }
            
            async with session.post(url, data=payload) as response:
                result = await response.json()
                
                # Follow up with directions if successful
                if result.get('sent'):
                    logger.info(f"Location sent to {phone_cleaned}")
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
                
                return {
                    "success": result.get('sent', False),
                    "id": result.get("id"),
                    "error": result.get("error")
                }
                
        except Exception as e:
            logger.error(f"Error sending location: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def handle_emergency_response(self, phone: str) -> Dict[str, Any]:
        """Handle crisis/emergency keywords"""
        
        emergency_message = f"""
🚨 *Important - Crisis Resources*

If you're experiencing a mental health emergency:

📞 *Immediate Help:*
• National Suicide Prevention Lifeline: 988
• Crisis Text Line: Text HOME to 741741  
• Emergency Services: 911

🏥 *Local Support:*
• {self.clinic_name}: {self.settings.emergency_contact or '(555) 123-4567'}
• Walk-in Crisis Center Available

💙 *You're not alone. Help is available 24/7.*

Please reach out to emergency services if you're in immediate danger.
        """.strip()
        
        return await self.send_message(phone, emergency_message)
    
    def get_coordinator_phone(self) -> Optional[str]:
        """Get coordinator phone number from settings"""
        return self.coordinator_phone
    
    def get_agent_phone(self) -> Optional[str]:
        """Get agent phone number from settings"""
        return self.agent_phone
    
    async def get_instance_status(self) -> Dict[str, Any]:
        """Check if Ultramsg instance is active"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/{self.instance_id}/instance/status"
            
            params = {'token': self.token}
            
            async with session.get(url, params=params) as response:
                result = await response.json()
                logger.info(f"Instance status check: {result}")
                return result
                
        except Exception as e:
            logger.error(f"Error checking instance status: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the UltraMsg connection"""
        try:
            status = await self.get_instance_status()
            if status.get('account_status') == 'authenticated':
                return {
                    "success": True,
                    "message": "UltraMsg connection successful",
                    "instance_id": self.instance_id,
                    "status": status
                }
            else:
                return {
                    "success": False,
                    "message": "UltraMsg instance not authenticated",
                    "status": status
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}"
            }
    
    async def create_webhook_response(self, message: str) -> str:
        """Create response for incoming messages (if using webhooks)"""
        # UltraMsg doesn't require XML responses like Twilio
        return ""
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
            logger.info("UltraMsg session closed")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_session()


# Initialize service instance
ultramsg_service = UltramsgService()