# Therapy Booking WhatsApp Bot

A WhatsApp Business integration for therapy booking management using Python, Google Agent Development Kit, and MySQL.

## Features

- **Dual Chat System**: Separate WhatsApp channels for client-bot and therapist-bot communication
- **LLM-Powered Conversations**: Natural language processing for booking workflows
- **Real-time Availability Checking**: Bot confirms with therapist before finalizing appointments
- **Service Options**: Support for in-call and out-call therapy services
- **Therapist Dashboard**: Interface for managing appointments and client interactions

## Tech Stack

- **Backend**: Python with FastAPI
- **Database**: MySQL with SQLAlchemy ORM
- **LLM Integration**: Google Agent Development Kit (ADK) with Gemini API
- **WhatsApp**: WhatsApp Business API (via Twilio)
- **NLP**: NLTK for text processing

## Project Structure

```
therapy_booking_app/
├── app/
│   ├── models/          # Database models
│   ├── services/        # Business logic
│   ├── api/            # API endpoints
│   └── utils/          # Utility functions
├── config/             # Configuration files
├── migrations/         # Database migrations
└── requirements.txt    # Dependencies
```

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Setup**
   - Install MySQL Server
   - Create database: `therapy_booking`
   - Update connection settings in `.env`

3. **WhatsApp Business Setup**
   - Create WhatsApp Business account
   - Set up Twilio WhatsApp Business API
   - Configure webhooks

4. **Google Gemini API Setup**
   - Get Gemini API key from Google AI Studio
   - Configure ADK agent settings

## Environment Variables

Create a `.env` file with:
```
DB_HOST=localhost
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=therapy_booking
WHATSAPP_TOKEN=your_twilio_token
WHATSAPP_SID=your_twilio_sid
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-pro
ADK_AGENT_CONFIG=config/agent_config.json
```

## Running the Application

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
