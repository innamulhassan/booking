# WhatsApp Therapy Booking System

A comprehensive WhatsApp-based therapy booking system using Google ADK Agent, FastAPI, and MySQL database integration.

## 🚀 Features

- **WhatsApp Integration**: Ultramsg webhook for WhatsApp message handling
- **AI-Powered Conversations**: Google ADK Agent for intelligent responses
- **Booking Management**: Complete therapy appointment booking system
- **Session Persistence**: Reliable session management with automatic recovery
- **Database Integration**: MySQL database for users, appointments, and conversations
- **Automated Scripts**: Complete batch automation for system management

## 📁 Project Structure

```
booking/
├── therapy_booking_app/        # Main FastAPI application
│   ├── app/
│   │   ├── services/          # ADK agent and core services
│   │   ├── models/            # Database models
│   │   └── main.py            # FastAPI application entry point
├── therapy_booking_agent/      # Google ADK Agent configuration
├── startup_scripts/           # System startup/shutdown scripts
├── test_scripts/              # Testing and utility scripts
├── other_scripts/             # Legacy and alternative scripts
├── CLEAR-*.bat               # System cleanup scripts
├── START-ALL.bat             # Complete system startup
├── STOP-ALL.bat              # Complete system shutdown
└── requirements.txt          # Python dependencies
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- MySQL Server
- Ultramsg WhatsApp Business API account
- Google Cloud Platform account (for ADK Agent)

### 1. Clone Repository
```bash
git clone https://github.com/innamulhassan/booking.git
cd booking
```

### 2. Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file with the following variables:
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=booking

# Ultramsg Configuration
ULTRAMSG_TOKEN=your_ultramsg_token
ULTRAMSG_INSTANCE_ID=your_instance_id

# Google ADK Configuration
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
PROJECT_ID=your_gcp_project_id
LOCATION=your_gcp_location
AGENT_ID=your_adk_agent_id

# Application Configuration
WEBHOOK_URL=your_webhook_url
PORT=8000
```

### 4. Database Setup
```bash
# Initialize database
python database_setup.py

# Test database connection
python test_db_connection.py
```

## 🎮 Usage

### Quick Start
```bash
# Start complete system (recommended)
START-ALL.bat

# Stop complete system
STOP-ALL.bat
```

### Manual Control
```bash
# Start individual components
cd startup_scripts
start_webhook_server.bat      # Start FastAPI webhook server
start_cloudflare_tunnel.bat   # Start Cloudflare tunnel

# Stop individual components
stop_webhook_server.bat
stop_cloudflare_tunnel.bat
```

### System Cleanup
```bash
# Clear all logs and database data
CLEAR-ALL.bat

# Clear only logs
CLEAR-LOGS.bat

# Clear only database conversations/messages
CLEAR-DATABASE.bat
```

## 🔧 Configuration

### ADK Agent Session Management
The system uses persistent session management to prevent "Session not found" errors:
- Persistent `InMemorySessionService` and `Runner` instances
- Automatic session recovery on startup
- Session state preservation across requests

### Database Schema
- **users**: User information and preferences
- **therapist_availability**: Therapist schedule management
- **appointments**: Booking records
- **conversations**: WhatsApp conversation tracking
- **messages**: Message history and content

### Webhook Integration
- FastAPI server on port 8000
- Ultramsg webhook endpoint: `/webhook`
- Message filtering (excludes own messages)
- Real-time message processing with ADK Agent

## 🛠️ Development

### Testing
```bash
# Test ADK Agent functionality
python test_adk_agent.py

# Test webhook integration
python test_webhook_simple.py

# Test database connectivity
python test_db_connection.py
```

### Adding Features
1. Modify ADK Agent instructions in `therapy_booking_agent/`
2. Update database models in `therapy_booking_app/app/models/`
3. Extend webhook handling in `therapy_booking_app/app/main.py`
4. Test with provided test scripts

## 📋 Available Scripts

### Startup Scripts
- `START-ALL.bat` - Complete system startup with error handling
- `STOP-ALL.bat` - Complete system shutdown with cleanup
- Individual component scripts in `startup_scripts/`

### Cleanup Scripts
- `CLEAR-ALL.bat` - Master cleanup (logs + database)
- `CLEAR-LOGS.bat` - Log and cache cleanup
- `CLEAR-DATABASE.bat` - Database conversation cleanup

### Utility Scripts
- `database_setup.py` - Database initialization
- `test_db_connection.py` - Database connectivity test
- `db_migration.py` - Database schema migrations

## 🚨 Troubleshooting

### Common Issues

1. **Session not found errors**
   - Fixed with persistent session architecture
   - Restart system with `START-ALL.bat`

2. **Database connection issues**
   - Verify MySQL service is running
   - Check `.env` database configuration
   - Run `test_db_connection.py`

3. **Webhook not receiving messages**
   - Check Ultramsg webhook configuration
   - Verify Cloudflare tunnel is active
   - Test with `test_webhook_simple.py`

### System Logs
- Application logs: `logs/session_*/`
- Cloudflare tunnel logs: `logs/session_*/cloudflare_tunnel.log`
- Webhook server logs: `logs/session_*/webhook_server.log`

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 Support

For issues and questions:
- Create an issue in this repository
- Check the troubleshooting section above
- Review system logs for detailed error information

---

**Built with ❤️ for seamless therapy booking automation**