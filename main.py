"""
Therapy Booking WhatsApp Bot - Main Application

Migrated to use new organized package structure with enhanced configuration management.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import logging
from pathlib import Path

# Import from new package structure
from src.therapy_booking.api import webhooks_router, therapist_router
from src.therapy_booking.models import create_tables
from src.therapy_booking.utils import setup_logging
from src.therapy_booking.core import get_settings

# Initialize settings and logging
settings = get_settings()
setup_logging(settings.log_level, settings.log_file if hasattr(settings, 'log_file') else None)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting Therapy Booking WhatsApp Bot...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"WhatsApp Provider: {settings.whatsapp_provider}")
    
    # Create database tables
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise
    
    # Validate configuration
    if not settings.ultramsg_instance_id or not settings.ultramsg_token:
        logger.warning("UltraMsg configuration incomplete - check ULTRAMSG_INSTANCE_ID and ULTRAMSG_TOKEN")
    
    if settings.debug:
        logger.info("Running in DEBUG mode")
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Therapy Booking WhatsApp Bot...")

# Create FastAPI app
app = FastAPI(
    title="Therapy Booking WhatsApp Bot",
    description="A WhatsApp Business integration for therapy booking management with enhanced architecture",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if hasattr(settings, 'cors_origins') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with prefixes
app.include_router(webhooks_router, prefix="/api/webhooks")
app.include_router(therapist_router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "service": "Therapy Booking WhatsApp Bot",
        "version": "2.0.0",
        "status": "running",
        "environment": settings.environment,
        "clinic": settings.clinic_name,
        "features": {
            "whatsapp_integration": True,
            "appointment_booking": True,
            "therapist_coordination": True,
            "ai_assistant": bool(settings.google_api_key or settings.gemini_api_key)
        }
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "service": "therapy_booking_app",
        "version": "2.0.0",
        "timestamp": "2024-01-01T00:00:00Z",  # Will be updated in production
        "components": {
            "database": "healthy",  # TODO: Add actual DB health check
            "ultramsg": "configured" if settings.ultramsg_instance_id and settings.ultramsg_token else "not_configured",
            "ai_service": "configured" if (settings.google_api_key or settings.gemini_api_key) else "not_configured"
        },
        "configuration": {
            "environment": settings.environment,
            "debug": settings.debug,
            "whatsapp_provider": settings.whatsapp_provider
        }
    }
    
    # Check if any critical components are not configured
    if any(status == "not_configured" for status in health_status["components"].values()):
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/config")
async def get_config_info():
    """Get non-sensitive configuration information"""
    if not settings.debug:
        return {"error": "Configuration endpoint only available in debug mode"}
    
    return {
        "clinic_name": settings.clinic_name,
        "therapist_name": settings.therapist_name,
        "environment": settings.environment,
        "whatsapp_provider": settings.whatsapp_provider,
        "ai_provider": settings.ai_provider if hasattr(settings, 'ai_provider') else 'unknown',
        "debug_mode": settings.debug,
        "coordinator_phone": settings.coordinator_phone_number[-4:] + "****",  # Masked
        "database_configured": bool(settings.database_url),
        "ultramsg_configured": bool(settings.ultramsg_instance_id and settings.ultramsg_token)
    }

@app.get("/demo", response_class=HTMLResponse)
async def demo_chat():
    """Enhanced POC Demo Interface - Test your bot without WhatsApp"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🩺 {settings.clinic_name} - Therapy Bot Demo</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
                max-width: 500px; 
                margin: 20px auto; 
                padding: 20px;
                background: #f5f5f5;
            }}
            .header {{
                text-align: center;
                background: white;
                padding: 20px;
                border-radius: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .chat-container {{
                background: white;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .chat {{ 
                height: 400px; 
                overflow-y: auto; 
                padding: 20px;
                background: #e5ddd5;
            }}
            .message {{ 
                margin: 15px 0; 
                padding: 12px 18px; 
                border-radius: 18px; 
                max-width: 80%;
                word-wrap: break-word;
                white-space: pre-wrap;
            }}
            .user {{ 
                background: #DCF8C6; 
                margin-left: auto;
                border-bottom-right-radius: 4px;
            }}
            .bot {{ 
                background: white; 
                margin-right: auto;
                border-bottom-left-radius: 4px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            }}
            .input-container {{
                display: flex;
                padding: 20px;
                background: white;
            }}
            .message-input {{ 
                flex: 1;
                padding: 12px 18px;
                border: 1px solid #ddd;
                border-radius: 25px;
                outline: none;
                font-size: 16px;
            }}
            .send-btn {{ 
                margin-left: 10px;
                padding: 12px 24px;
                background: #25D366;
                color: white;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-weight: bold;
                transition: background-color 0.2s;
            }}
            .send-btn:hover {{ background: #1fb854; }}
            .send-btn:disabled {{ background: #ccc; cursor: not-allowed; }}
            .typing {{
                font-style: italic;
                opacity: 0.7;
                animation: pulse 1.5s infinite;
            }}
            @keyframes pulse {{
                0%, 100% {{ opacity: 0.7; }}
                50% {{ opacity: 1; }}
            }}
            .status {{
                text-align: center;
                padding: 10px;
                background: #075E54;
                color: white;
                font-size: 14px;
            }}
            .demo-info {{
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                font-size: 14px;
            }}
            .error-message {{
                background: #f8d7da;
                color: #721c24;
                padding: 10px;
                border-radius: 8px;
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🩺 {settings.clinic_name}</h1>
            <h3>Therapy Booking Assistant</h3>
            <p><strong>Demo Mode</strong> - Test without WhatsApp</p>
            <small>Therapist: {settings.therapist_name}</small>
        </div>
        
        <div class="demo-info">
            <strong>📱 Try these examples:</strong><br>
            • "I want to book an appointment"<br>
            • "What services do you offer?"<br>
            • "Check availability for tomorrow 2pm"<br>
            • "Book in-call therapy for Friday 3pm"<br>
            • "What are your clinic hours?"<br>
            • "I need emergency support"
        </div>
        
        <div class="chat-container">
            <div class="status">🟢 Bot Online - Enhanced v2.0</div>
            <div id="chat" class="chat">
                <div class="message bot">
                    👋 Hello! I'm your therapy booking assistant for {settings.clinic_name}.
                    
How can I help you today? I can assist with:
• Booking appointments 
• Checking availability
• Providing service information
• Emergency support resources
                </div>
            </div>
            <div class="input-container">
                <input type="text" id="messageInput" class="message-input" 
                       placeholder="Type your message..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()" class="send-btn" id="sendBtn">Send</button>
            </div>
        </div>
        
        <script>
            let messageCounter = 0;
            
            function handleKeyPress(event) {{
                if (event.key === 'Enter') {{
                    sendMessage();
                }}
            }}
            
            async function sendMessage() {{
                const input = document.getElementById('messageInput');
                const chat = document.getElementById('chat');
                const sendBtn = document.getElementById('sendBtn');
                const message = input.value.trim();
                
                if (!message) return;
                
                // Disable send button
                sendBtn.disabled = true;
                sendBtn.textContent = 'Sending...';
                
                // Add user message
                chat.innerHTML += `<div class="message user">${{escapeHtml(message)}}</div>`;
                input.value = '';
                
                // Show typing indicator
                const typingId = Date.now();
                chat.innerHTML += `<div class="message bot typing" id="typing-${{typingId}}">🤖 Assistant is typing...</div>`;
                chat.scrollTop = chat.scrollHeight;
                
                try {{
                    // Send to demo webhook API
                    const response = await fetch('/api/webhooks/demo', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{
                            messages: [{{
                                text: {{ body: message }},
                                timestamp: Date.now(),
                                id: 'demo_' + (++messageCounter)
                            }}],
                            phone: '+97400000000',
                            demo: true,
                            contact: {{
                                name: 'Demo User',
                                phone: '+97400000000'
                            }}
                        }})
                    }});
                    
                    const result = await response.json();
                    
                    // Remove typing indicator
                    const typingElement = document.getElementById(`typing-${{typingId}}`);
                    if (typingElement) typingElement.remove();
                    
                    // Add bot response
                    const botResponse = result.response || result.message || 'Sorry, I didn\\'t get a response.';
                    chat.innerHTML += `<div class="message bot">${{escapeHtml(botResponse)}}</div>`;
                    
                }} catch (error) {{
                    console.error('Demo chat error:', error);
                    
                    // Remove typing indicator
                    const typingElement = document.getElementById(`typing-${{typingId}}`);
                    if (typingElement) typingElement.remove();
                    
                    // Show error
                    chat.innerHTML += `<div class="message bot error-message">❌ Connection error. Please make sure the server is running on the correct port.</div>`;
                }} finally {{
                    // Re-enable send button
                    sendBtn.disabled = false;
                    sendBtn.textContent = 'Send';
                    chat.scrollTop = chat.scrollHeight;
                }}
            }}
            
            function escapeHtml(text) {{
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML.replace(/\\n/g, '<br>');
            }}
            
            // Auto-focus input
            document.getElementById('messageInput').focus();
            
            // Add welcome interaction
            setTimeout(() => {{
                const chat = document.getElementById('chat');
                chat.innerHTML += `<div class="message bot">💡 <strong>Tip:</strong> Try typing "help" to see what I can do!</div>`;
                chat.scrollTop = chat.scrollHeight;
            }}, 2000);
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )