# Google Gemini API Setup Guide

This guide explains how to get your Gemini API key and configure the Google Agent Development Kit (ADK) for the therapy booking application.

## Step 1: Get Gemini API Key

### 1.1 Access Google AI Studio
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Accept the terms of service if prompted

### 1.2 Create API Key
1. Click on "Create API Key" 
2. Choose "Create API key in new project" or select an existing project
3. Copy the generated API key
4. **Important**: Store this key securely - you won't be able to see it again

### 1.3 Test Your API Key
You can test your API key with a simple curl command:

```bash
curl -H 'Content-Type: application/json' \
     -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
     -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_API_KEY"
```

## Step 2: Configure Environment Variables

### 2.1 Update .env File
Add your Gemini API key to the `.env` file:

```bash
# Google Agent Development Kit (ADK)
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-pro
ADK_AGENT_CONFIG=config/agent_config.json
```

### 2.2 Available Models
You can use different Gemini models:
- `gemini-pro` - General purpose model (recommended)
- `gemini-pro-vision` - For image and text (not needed for this app)

## Step 3: Agent Configuration

### 3.1 Understanding agent_config.json
The `config/agent_config.json` file contains:

- **Intents**: What the user wants to do (book appointment, check availability, etc.)
- **Entities**: Important information to extract (dates, service types, etc.) 
- **Training Phrases**: Examples of how users might express their intent
- **Response Templates**: Pre-defined responses for common scenarios

### 3.2 Customizing the Agent
You can modify `config/agent_config.json` to:

**Add new intents:**
```json
{
  "name": "cancel_appointment",
  "description": "Handle appointment cancellations",
  "training_phrases": [
    "cancel my appointment",
    "I need to cancel",
    "remove my booking"
  ]
}
```

**Add new entities:**
```json
{
  "name": "urgency_level",
  "values": [
    {
      "value": "urgent",
      "synonyms": ["urgent", "asap", "emergency", "immediate"]
    },
    {
      "value": "flexible", 
      "synonyms": ["flexible", "anytime", "whenever"]
    }
  ]
}
```

**Modify responses:**
```json
"responses": {
  "fallback": [
    "I'm not sure I understand. Could you please rephrase that?",
    "I didn't catch that. Can you tell me what you'd like to do?"
  ]
}
```

## Step 4: Testing the Agent

### 4.1 Local Testing
1. Start the application:
   ```bash
   python main.py
   ```

2. Use a tool like Postman to test the webhook:
   ```bash
   POST http://localhost:8000/webhook/client
   Content-Type: application/x-www-form-urlencoded
   
   From=whatsapp:+1234567890&To=whatsapp:+your_business_number&Body=Hello&MessageSid=test123&AccountSid=test
   ```

### 4.2 Check Logs
Monitor the application logs to see:
- Intent detection results
- Entity extraction
- Gemini API responses
- Conversation flow

## Step 5: Advanced Configuration

### 5.1 Conversation Context
The ADK agent maintains conversation context including:
- Previous messages
- Extracted entities
- Current booking state
- Session information

### 5.2 Confidence Thresholds
In `agent_config.json`, you can adjust:
```json
"settings": {
  "confidence_threshold": 0.7,
  "fallback_threshold": 0.3
}
```

- **confidence_threshold**: Minimum confidence to act on an intent
- **fallback_threshold**: Below this, use fallback responses

### 5.3 Session Management
Sessions are automatically managed:
- Each WhatsApp user gets a unique session
- Sessions timeout after 30 minutes of inactivity
- Booking state is preserved within sessions

## Step 6: Production Considerations

### 6.1 API Limits
Gemini API has usage limits:
- Free tier: 60 requests per minute
- Check current limits in Google AI Studio

### 6.2 Error Handling
The application includes:
- Automatic retry for API failures
- Fallback responses when Gemini is unavailable
- Graceful degradation to rule-based responses

### 6.3 Monitoring
Monitor these metrics:
- API response times
- Intent detection accuracy
- Conversation completion rates
- User satisfaction

## Step 7: Switching to Other LLMs

The architecture is designed to be LLM-agnostic. To switch to another LLM:

### 7.1 Create New Service
Create a new file like `app/services/openai_service.py`:

```python
import openai
from config.settings import config

class OpenAIService:
    def __init__(self):
        openai.api_key = config.OPENAI_API_KEY
    
    async def process_message(self, message: str, context: str) -> dict:
        # Implement OpenAI integration
        pass
```

### 7.2 Update Configuration
Add new environment variables:
```bash
LLM_PROVIDER=openai  # or 'gemini', 'anthropic', etc.
OPENAI_API_KEY=your_openai_key
```

### 7.3 Modify Agent Service
Update `adk_agent_service.py` to use the LLM provider:
```python
if config.LLM_PROVIDER == 'openai':
    from app.services.openai_service import openai_service
    response = await openai_service.process_message(message, context)
elif config.LLM_PROVIDER == 'gemini':
    # Use Gemini
    pass
```

## Troubleshooting

### Common Issues:

**"API key not valid"**
- Double-check your API key in the .env file
- Ensure no extra spaces or characters
- Verify the key is active in Google AI Studio

**"Model not found"**
- Check the model name in GEMINI_MODEL
- Use 'gemini-pro' for text generation

**"Rate limit exceeded"**
- You've hit the API usage limit
- Wait and try again or upgrade your plan

**Intent not detected correctly**
- Add more training phrases to agent_config.json
- Check the confidence thresholds
- Review the logs for debugging info

### Getting Help:
- Check application logs for detailed error messages
- Review the agent configuration file
- Test individual components separately
- Monitor API usage in Google AI Studio dashboard
