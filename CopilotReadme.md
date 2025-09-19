# Therapy Booking System - Copilot Reference Guide

## 🎯 Quick Command Reference

When the user says these phrases, execute the corresponding commands:

### System Control Commands

| User Says | Action | Commands to Execute |
|-----------|--------|-------------------|
| **"restart"** | Standard restart | `./STOP-ALL.bat` → `./START-ALL.bat` |
| **"restart with clear logs"** | Restart + clear logs | `./STOP-ALL.bat` → `cmd /c CLEAR-LOGS.bat` → `./START-ALL.bat` |
| **"restart with clear all"** | Full restart + clear everything | `./STOP-ALL.bat` → `cmd /c CLEAR-ALL.bat` → `./START-ALL.bat` |
| **"stop"** | Stop all services | `./STOP-ALL.bat` |
| **"start"** | Start all services | `./START-ALL.bat` |
| **"status"** | Check system status | `./STATUS.bat` |
| **"clear logs"** | Clear log files only | `cmd /c CLEAR-LOGS.bat` |

### Testing Commands

| User Says | Action | What to Do |
|-----------|--------|------------|
| **"test now"** / **"can i test"** | Ready for testing | Confirm system is running, provide webhook URL |
| **"test booking"** | Test booking flow | Create test script and send sample booking requests |
| **"test natural dates"** | Test date parsing | Run `python test_natural_date.py` |
| **"check logs"** | View recent logs | Check latest webhook server logs |

### Development Commands

| User Says | Action | What to Do |
|-----------|--------|------------|
| **"fix date parsing"** | Update natural language dates | Check/update `app/utils/date_parser.py` |
| **"fix coordinator workflow"** | Remove coordinator mentions | Update ADK agent service responses |
| **"update agent"** | Modify agent behavior | Edit `adk_agent_service.py` agent instructions |

## 🏗️ System Architecture

### Core Services
1. **FastAPI Webhook Server** (Port 8000) - Handles WhatsApp webhooks
2. **Google ADK Agent** - AI conversation handler with natural language processing
3. **MySQL Database** - Stores conversations, appointments, users
4. **Ultramsg Service** - WhatsApp Business API integration
5. **Cloudflare Tunnel** - Public webhook endpoint

### Key Files
- `therapy_booking_app/app/services/adk_agent_service.py` - Main AI agent
- `therapy_booking_app/app/utils/date_parser.py` - Natural language date parsing
- `therapy_booking_app/app/api/webhooks.py` - Webhook endpoints
- `therapy_booking_app/app/services/ultramsg_service.py` - WhatsApp messaging
- `.env` - Environment configuration

### Batch Scripts
- `START-ALL.bat` - Start complete system
- `STOP-ALL.bat` - Stop all services gracefully
- `STATUS.bat` - Check system status
- `CLEAR-LOGS.bat` - Clear log files only
- `CLEAR-ALL.bat` - Clear logs, cache, sessions (full cleanup)

## 🔧 Common Issues & Solutions

### Issue: "System not recognizing 'today'"
**Solution**: Natural language date parsing implemented in `app/utils/date_parser.py`
- Supports: "today", "tomorrow", weekdays, "in X days", day numbers
- Test with: `python test_natural_date.py`

### Issue: "Agent mentions coordinators to clients"
**Solution**: Updated ADK agent to handle everything as "Layla" directly
- Client sees appointments as immediately confirmed
- Coordinator notifications happen in background silently

### Issue: "Session not found errors"
**Solution**: Enhanced session management in ADK service
- Automatic session recovery
- Persistent session service
- Better error handling

### Issue: "Port 8000 already in use"
**Solution**: Run stop command first
```
./STOP-ALL.bat
# Wait for complete shutdown, then
./START-ALL.bat
```

## 📋 Testing Workflows

### Complete System Test
1. **Restart system**: `./STOP-ALL.bat` → `./START-ALL.bat`
2. **Check health**: `Invoke-RestMethod -Uri "http://localhost:8000/health"`
3. **Test natural dates**: `python test_natural_date.py`
4. **Test webhook**: `python test_webhook_today.py`
5. **Check logs**: View latest webhook server logs

### Natural Language Date Test
```python
# Test inputs that should work:
- "today"
- "tomorrow" 
- "monday"
- "next tuesday"
- "in 3 days"
- "15th"
- "25"
```

### Booking Flow Test
```
User: "I want to book an office visit for today"
Expected: System checks availability without asking for date format
```

## 🎭 Agent Persona - Layla

### Personality
- Warm, caring female therapy assistant
- Speaks like a loving sister/best friend
- Uses terms: "habibti", "my love", "sweetie"
- Handles everything personally - no mentions of coordinators to clients

### Critical Rules
1. **MUST use tools**: Never confirm appointments without `book_appointment()` tool
2. **No coordinator mentions**: Clients should never hear about approval processes
3. **Natural language**: Accept "today", "tomorrow", etc. for dates
4. **Immediate confirmation**: Appointments appear confirmed to clients instantly

### Workflow
1. Client requests booking → Check availability with `check_availability()`
2. Available time found → Book with `book_appointment()`
3. Success → Confirm to client as complete
4. Background → Silent coordinator notification

## 🔄 Environment Variables (Key Ones)

Located in `.env` file:
- `GOOGLE_GENAI_API_KEY` - Google AI API key
- `ULTRAMSG_INSTANCE_ID` - WhatsApp integration
- `ULTRAMSG_TOKEN` - WhatsApp API token
- `COORDINATOR_PHONE_NUMBER` - Background notifications
- `DATABASE_URL` - MySQL connection

## 📱 WhatsApp Integration

### Webhook URL (when tunnel running)
- Local: `http://localhost:8000/webhook`
- Public: `https://webhook-booking.innamul.com/webhook`

### Message Flow
1. WhatsApp → Webhook → ADK Agent → Response → Ultramsg → WhatsApp
2. Natural language processing handles dates, times, requests
3. Database stores conversation history and appointments

## 🚀 Quick Start Commands

### For Development
```bash
# Full restart with log clearing
./STOP-ALL.bat && cmd /c CLEAR-LOGS.bat && ./START-ALL.bat

# Test natural language dates
python test_natural_date.py

# Test complete booking flow
python test_webhook_today.py
```

### For Troubleshooting
```bash
# Check if services running
./STATUS.bat

# View latest logs
Get-Content "logs\session_*\webhook_server.log" -Tail 20

# Health check
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

---

## 💡 Pro Tips for Copilot

1. **Always restart after code changes** to apply updates
2. **Check logs first** when debugging issues
3. **Test natural language dates** after any agent updates
4. **Use clear logs** when starting fresh testing
5. **Verify health endpoint** before declaring system ready

This system provides a complete WhatsApp-based therapy booking solution with natural language processing and a caring AI assistant persona.