# WhatsApp Business Account Setup Guide

This guide will walk you through setting up a WhatsApp Business account and integrating it with your therapy booking application using Twilio's WhatsApp Business API.

## Prerequisites

- A phone number dedicated to your business (cannot be already registered with WhatsApp)
- A verified business (business license or registration documents)
- Twilio account with billing information
- SSL certificate for your webhook endpoints (required for production)

## Step 1: Create WhatsApp Business Account

### 1.1 Business Verification
1. Go to [WhatsApp Business](https://business.whatsapp.com/)
2. Click "Get Started" 
3. Choose "WhatsApp Business API"
4. Provide your business information:
   - Business name
   - Business category (Healthcare/Medical Services)
   - Business website
   - Business address
   - Business description

### 1.2 Phone Number Registration
1. Provide a business phone number (must not be registered with WhatsApp)
2. Verify the phone number via SMS or voice call
3. Complete business profile:
   - Upload business logo
   - Add business hours
   - Add business description
   - Set up automated welcome message

## Step 2: Set Up Twilio WhatsApp Business API

### 2.1 Create Twilio Account
1. Go to [Twilio Console](https://console.twilio.com/)
2. Sign up or log in to your account
3. Verify your identity and add billing information
4. Navigate to "Programmable Messaging" > "WhatsApp"

### 2.2 Request WhatsApp Business API Access
1. In Twilio Console, go to WhatsApp > "Get Started"
2. Submit WhatsApp Business API request:
   - Business information
   - Use case description: "Healthcare therapy booking and appointment management"
   - Expected message volume
   - Business verification documents

**Note**: Approval can take 1-3 business days.

### 2.3 Configure WhatsApp Sender
1. Once approved, go to WhatsApp > "Senders"
2. Click "Create new Sender"
3. Provide:
   - Display name for your business
   - Business phone number
   - Business category: Healthcare
   - Business description

## Step 3: Configure Webhook URLs

### 3.1 Set Up Secure Endpoints
Your application must be hosted with HTTPS. For development, you can use:

**Option A: ngrok (for testing)**
```bash
# Install ngrok
npm install -g ngrok

# Run your application
uvicorn main:app --host 0.0.0.0 --port 8000

# In another terminal, expose your local server
ngrok http 8000
```

**Option B: Deploy to Cloud Platform**
- Heroku, AWS, Google Cloud, or any other cloud provider
- Ensure SSL/TLS certificate is configured

### 3.2 Configure Twilio Webhooks
1. In Twilio Console, go to WhatsApp > "Sandbox" (for testing) or "Senders" (for production)
2. Set webhook URLs:
   - **Webhook URL for incoming messages**: `https://your-domain.com/webhook/client`
   - **Status callback URL**: `https://your-domain.com/webhook/status` (optional)

### 3.3 Webhook Configuration in Twilio
```
Webhook URL: https://your-domain.com/webhook/client
HTTP Method: POST
```

## Step 4: Environment Configuration

### 4.1 Get Twilio Credentials
1. In Twilio Console, go to "Account Dashboard"
2. Copy your Account SID and Auth Token
3. Go to WhatsApp > "Senders" and copy your WhatsApp phone number

### 4.2 Update Environment Variables
Create a `.env` file in your project root:

```env
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=therapy_booking
DB_PORT=3306

# Twilio WhatsApp Configuration
WHATSAPP_TOKEN=your_twilio_auth_token
WHATSAPP_SID=your_twilio_account_sid
TWILIO_PHONE_NUMBER=+1234567890  # Your WhatsApp Business number

# Google Cloud / Dialogflow CX
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
DIALOGFLOW_PROJECT_ID=your_project_id
DIALOGFLOW_LOCATION=us-central1
DIALOGFLOW_AGENT_ID=your_agent_id

# Application Settings
SECRET_KEY=your_secret_key_here
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Therapist Configuration
THERAPIST_PHONE=+therapist_whatsapp_number
CLIENT_WEBHOOK_URL=https://your-domain.com/webhook/client
THERAPIST_WEBHOOK_URL=https://your-domain.com/webhook/therapist
```

## Step 5: Set Up Google Dialogflow CX

### 5.1 Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Dialogflow CX API
4. Create a service account:
   - Go to IAM & Admin > Service Accounts
   - Click "Create Service Account"
   - Grant "Dialogflow API Client" role
   - Download the JSON key file

### 5.2 Create Dialogflow CX Agent
1. Go to [Dialogflow CX Console](https://dialogflow.cloud.google.com/cx/)
2. Create a new agent:
   - Agent name: "Therapy Booking Bot"
   - Location: us-central1 (or your preferred region)
   - Time zone: Your business timezone

### 5.3 Configure Intents and Entities

**Intents to create:**
1. `greeting` - Welcome messages
2. `book.appointment` - Appointment booking requests  
3. `check.availability` - Availability inquiries
4. `get.services` - Service information requests
5. `modify.appointment` - Appointment changes

**Entities to create:**
1. `@service-type` - Values: "in-call", "out-call", "home visit", "clinic visit"
2. `@appointment-time` - System entity for date-time
3. `@service-description` - Custom entity for therapy types

**Training Phrases Examples:**

For `book.appointment`:
- "I want to book an appointment"
- "Can I schedule a therapy session?"
- "I need an in-call service for tomorrow at 2 PM"
- "Book me an out-call appointment"

For `check.availability`:
- "What times are available?"
- "Are you free on Monday?"
- "Show me available slots"

## Step 6: Testing Your Setup

### 6.1 Sandbox Testing (Development)
1. In Twilio Console, go to WhatsApp > "Sandbox"
2. Send the join code from your personal WhatsApp to the sandbox number
3. Test messaging your application

### 6.2 Production Testing
1. Use your business WhatsApp number
2. Test both client and therapist workflows
3. Verify database entries are created
4. Test appointment booking flow end-to-end

## Step 7: Business Verification and Going Live

### 7.1 Complete Business Verification
1. Submit required business documents to WhatsApp
2. Wait for approval (can take 1-7 business days)
3. Complete Facebook Business Manager verification if required

### 7.2 Production Deployment
1. Deploy your application to a production server
2. Update webhook URLs to production endpoints
3. Configure production database
4. Set up monitoring and logging

## Step 8: Two-Chat Setup Configuration

### 8.1 Client Chat Configuration
- Main business WhatsApp number receives client messages
- Webhook: `/webhook/client`
- Purpose: Handle booking requests, inquiries, confirmations

### 8.2 Therapist Chat Configuration
For the therapist interface, you have two options:

**Option A: Separate WhatsApp Number**
- Get a second WhatsApp Business number for therapist communications
- Configure separate webhook: `/webhook/therapist`

**Option B: Single Number with Message Routing**
- Use message content/sender identification to route messages
- Implement logic in your webhook to distinguish client vs therapist messages

### 8.3 Message Routing Setup
In your webhook handler:

```python
@router.post("/webhook/client")
async def client_webhook(From: str = Form(...), Body: str = Form(...)):
    sender_phone = From.replace('whatsapp:', '')
    
    # Check if sender is therapist
    if sender_phone == config.THERAPIST_PHONE:
        # Route to therapist handler
        return await process_therapist_message(Body, sender_phone)
    else:
        # Route to client handler  
        return await process_client_message(Body, sender_phone)
```

## Step 9: Security and Compliance

### 9.1 HIPAA Compliance (if applicable)
- Implement message encryption
- Secure data storage
- Access logging
- Data retention policies
- Business Associate Agreements with service providers

### 9.2 Security Best Practices
- Use HTTPS for all endpoints
- Implement request signature verification
- Rate limiting on webhook endpoints
- Input validation and sanitization
- Secure environment variable management

## Step 10: Monitoring and Maintenance

### 10.1 Set Up Monitoring
- Application health checks
- Database connection monitoring
- WhatsApp API rate limit monitoring
- Error tracking and alerting

### 10.2 Regular Maintenance
- Monitor message delivery rates
- Review and update conversation flows
- Backup database regularly
- Update dependencies and security patches

## Troubleshooting Common Issues

### Issue: Messages not delivering
- Check webhook URL accessibility
- Verify Twilio account balance
- Check phone number verification status

### Issue: Webhook not receiving messages
- Verify HTTPS certificate
- Check firewall settings
- Test webhook URL directly

### Issue: Dialogflow not responding
- Verify service account permissions
- Check project ID and agent ID
- Review intent training and matching

### Issue: Database connection errors
- Verify database credentials
- Check network connectivity
- Review connection pool settings

## Support and Resources

- **Twilio WhatsApp Documentation**: https://www.twilio.com/docs/whatsapp
- **Dialogflow CX Documentation**: https://cloud.google.com/dialogflow/cx/docs
- **WhatsApp Business API Documentation**: https://developers.facebook.com/docs/whatsapp
- **Business Verification Support**: https://business.whatsapp.com/support

For technical support with this application, review the logs and error messages, and ensure all environment variables are correctly configured.
