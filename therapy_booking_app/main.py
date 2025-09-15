from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.api.webhooks import router as webhooks_router
from app.api.therapist import router as therapist_router
from app.models.database import create_tables
from app.utils.helpers import setup_logging
from config.settings import config
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Therapy Booking WhatsApp Bot",
    description="A WhatsApp Business integration for therapy booking management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhooks_router)
app.include_router(therapist_router)

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Therapy Booking WhatsApp Bot...")
    
    # Create database tables
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise
    
    logger.info("Application started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down Therapy Booking WhatsApp Bot...")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Therapy Booking WhatsApp Bot API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "therapy_booking_app",
        "version": "1.0.0"
    }

@app.get("/demo", response_class=HTMLResponse)
async def demo_chat():
    """POC Demo Interface - Test your bot without WhatsApp"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🩺 Therapy Booking Bot - POC Demo</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
                max-width: 500px; 
                margin: 20px auto; 
                padding: 20px;
                background: #f5f5f5;
            }
            .header {
                text-align: center;
                background: white;
                padding: 20px;
                border-radius: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .chat-container {
                background: white;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .chat { 
                height: 400px; 
                overflow-y: auto; 
                padding: 20px;
                background: #e5ddd5;
            }
            .message { 
                margin: 15px 0; 
                padding: 12px 18px; 
                border-radius: 18px; 
                max-width: 80%;
                word-wrap: break-word;
            }
            .user { 
                background: #DCF8C6; 
                margin-left: auto;
                border-bottom-right-radius: 4px;
            }
            .bot { 
                background: white; 
                margin-right: auto;
                border-bottom-left-radius: 4px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            }
            .input-container {
                display: flex;
                padding: 20px;
                background: white;
            }
            .message-input { 
                flex: 1;
                padding: 12px 18px;
                border: 1px solid #ddd;
                border-radius: 25px;
                outline: none;
                font-size: 16px;
            }
            .send-btn { 
                margin-left: 10px;
                padding: 12px 24px;
                background: #25D366;
                color: white;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-weight: bold;
            }
            .send-btn:hover { background: #1fb854; }
            .typing {
                font-style: italic;
                opacity: 0.7;
            }
            .status {
                text-align: center;
                padding: 10px;
                background: #075E54;
                color: white;
                font-size: 14px;
            }
            .demo-info {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🩺 Therapy Booking Bot</h1>
            <p><strong>POC Demo</strong> - Test without WhatsApp</p>
        </div>
        
        <div class="demo-info">
            <strong>📱 Demo Instructions:</strong><br>
            • Try: "I want to book an appointment"<br>
            • Try: "What services do you offer?"<br>
            • Try: "Check availability for tomorrow 2pm"<br>
            • Try: "Book in-call therapy for Friday 3pm"
        </div>
        
        <div class="chat-container">
            <div class="status">🟢 Bot Online - Ready for Messages</div>
            <div id="chat" class="chat">
                <div class="message bot">
                    👋 Hello! I'm your therapy booking assistant. How can I help you today?
                </div>
            </div>
            <div class="input-container">
                <input type="text" id="messageInput" class="message-input" 
                       placeholder="Type your message..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()" class="send-btn">Send</button>
            </div>
        </div>
        
        <script>
            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }
            
            async function sendMessage() {
                const input = document.getElementById('messageInput');
                const chat = document.getElementById('chat');
                const message = input.value.trim();
                
                if (!message) return;
                
                // Add user message
                chat.innerHTML += `<div class="message user">${escapeHtml(message)}</div>`;
                input.value = '';
                
                // Show typing indicator
                const typingId = Date.now();
                chat.innerHTML += `<div class="message bot typing" id="typing-${typingId}">Bot is typing...</div>`;
                chat.scrollTop = chat.scrollHeight;
                
                try {
                    // Send to your API
                    const response = await fetch('/api/demo-chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            message: message, 
                            phone: '+1234567890',
                            demo: true
                        })
                    });
                    
                    const result = await response.json();
                    
                    // Remove typing indicator
                    document.getElementById(`typing-${typingId}`).remove();
                    
                    // Add bot response
                    chat.innerHTML += `<div class="message bot">${escapeHtml(result.response)}</div>`;
                    
                } catch (error) {
                    // Remove typing indicator
                    document.getElementById(`typing-${typingId}`).remove();
                    
                    // Show error
                    chat.innerHTML += `<div class="message bot">❌ Sorry, there was an error. Please make sure the server is running.</div>`;
                }
                
                chat.scrollTop = chat.scrollHeight;
            }
            
            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
            
            // Auto-focus input
            document.getElementById('messageInput').focus();
        </script>
    </body>
    </html>
    """

@app.post("/api/demo-chat")
async def demo_chat_api(request: Request):
    """Demo chat API endpoint"""
    try:
        data = await request.json()
        message = data.get('message', '')
        phone = data.get('phone', '+1234567890')
        
        # Process with your ADK agent service
        from app.services.adk_agent_service import adk_service
        response = await adk_service.process_message(message, phone)
        
        return {"response": response, "status": "success"}
    except Exception as e:
        logger.error(f"Demo chat error: {str(e)}")
        return {"response": "I'm sorry, I'm having trouble processing your request right now. Please try again.", "status": "error"}

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {config.HOST}:{config.PORT}")
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info"
    )
