# Quick POC Setup Guide - No Business Registration Required

## Option 1: Twilio WhatsApp Sandbox (Recommended)

### Step 1: Create Free Twilio Account
1. Go to https://www.twilio.com/try-twilio
2. Sign up with email (no business verification needed)
3. Verify your phone number
4. You get **FREE CREDITS** to test with

### Step 2: Access WhatsApp Sandbox
1. In Twilio Console, go to **Messaging** > **Try it out** > **Send a WhatsApp message**
2. You'll see a sandbox number like: `+1 415 523 8886`
3. Join code will be something like: `join doctor-booking`

### Step 3: Test Immediately
1. Send `join doctor-booking` to the sandbox number from your WhatsApp
2. Your personal WhatsApp is now connected to your app!
3. No business verification, no waiting period

### Step 4: Configure Your App
Update your `.env` file:

```env
# Twilio Sandbox Configuration (POC)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=+14155238886  # Sandbox number
SANDBOX_MODE=true

# Your app webhook (use ngrok for local testing)
WEBHOOK_URL=https://abc123.ngrok.io/webhook/client
```

### Step 5: Local Testing with ngrok
```bash
# Install ngrok
npm install -g ngrok

# Run your app
uvicorn main:app --host 0.0.0.0 --port 8000

# In another terminal, expose your app
ngrok http 8000
# Copy the https URL (like https://abc123.ngrok.io)
```

### Step 6: Set Webhook in Twilio
1. In Twilio Console, go to WhatsApp Sandbox Settings
2. Set **Webhook URL**: `https://abc123.ngrok.io/webhook/client`
3. Set **HTTP Method**: POST

**That's it! Your POC is ready in 10 minutes!**

---

## Option 2: WhatsApp Business API Providers (No Registration)

### 2.1 Ultramsg (Instant Setup)
- **Website**: https://ultramsg.com/
- **Free Trial**: 7 days free
- **Setup Time**: 2 minutes
- **No Business Verification**: Just QR code scan

```python
# Quick integration example
import requests

def send_whatsapp_message(phone, message):
    url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
    payload = {
        "token": "your_token",
        "to": phone,
        "body": message
    }
    response = requests.post(url, data=payload)
    return response.json()
```

### 2.2 ChatAPI (QR Code Setup)
- **Website**: https://chat-api.com/
- **Free Trial**: 3 days free
- **Setup**: Scan QR code with WhatsApp Web
- **Perfect for**: Quick POC demos

### 2.3 WhatsMate (Simple API)
- **Website**: https://www.whatsmate.net/
- **Free**: 100 messages/day
- **No Registration**: Just API key
- **Instant**: Works immediately

---

## Option 3: Testing Services (Simulation)

### 3.1 Mock WhatsApp Service
Create a simple web interface that simulates WhatsApp:

```python
# Add to your main.py for POC demo
from fastapi import Request
from fastapi.responses import HTMLResponse

@app.get("/demo", response_class=HTMLResponse)
async def demo_chat():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WhatsApp Simulator - Therapy Booking</title>
        <style>
            body { font-family: Arial; max-width: 400px; margin: 50px auto; }
            .chat { border: 1px solid #ccc; height: 400px; overflow-y: scroll; padding: 10px; }
            .message { margin: 10px 0; padding: 10px; border-radius: 10px; }
            .user { background: #DCF8C6; text-align: right; }
            .bot { background: #F1F1F1; }
            input[type="text"] { width: 80%; padding: 10px; }
            button { padding: 10px; }
        </style>
    </head>
    <body>
        <h2>🩺 Therapy Booking Bot Demo</h2>
        <div id="chat" class="chat"></div>
        <input type="text" id="messageInput" placeholder="Type your message...">
        <button onclick="sendMessage()">Send</button>
        
        <script>
            async function sendMessage() {
                const input = document.getElementById('messageInput');
                const chat = document.getElementById('chat');
                
                // Add user message
                chat.innerHTML += `<div class="message user">${input.value}</div>`;
                
                // Send to your API
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: input.value, phone: '+1234567890'})
                });
                
                const result = await response.json();
                
                // Add bot response
                chat.innerHTML += `<div class="message bot">${result.response}</div>`;
                
                input.value = '';
                chat.scrollTop = chat.scrollTop = chat.scrollHeight;
            }
        </script>
    </body>
    </html>
    """

@app.post("/api/chat")
async def demo_chat_api(request: Request):
    data = await request.json()
    # Process with your ADK agent service
    response = await adk_service.process_message(data['message'], data['phone'])
    return {"response": response}
```

Access at: `http://localhost:8000/demo`

---

## Recommended POC Flow

### Phase 1: Local Demo (Day 1)
1. Use the web simulator above
2. Test your booking logic
3. Demo to stakeholders

### Phase 2: WhatsApp Testing (Day 2)
1. Set up Twilio Sandbox
2. Test with real WhatsApp messages
3. Refine conversation flow

### Phase 3: Extended Testing (Week 1)
1. Use Ultramsg or ChatAPI
2. Test with multiple users
3. Gather feedback

### Phase 4: Business Setup (When Ready)
1. Register business
2. Get official WhatsApp Business API
3. Deploy to production

---

## Cost Comparison

| Service | Setup Time | Cost (POC) | Business Required |
|---------|------------|------------|------------------|
| Twilio Sandbox | 5 minutes | Free | No |
| Ultramsg | 2 minutes | $5/week | No |
| ChatAPI | 3 minutes | $9/3 days | No |
| WhatsMate | 1 minute | Free (100 msgs) | No |
| Web Simulator | 0 minutes | Free | No |

**For your POC, I recommend starting with the Web Simulator for immediate demo, then moving to Twilio Sandbox for real WhatsApp testing.**

Would you like me to help you set up any of these options?
