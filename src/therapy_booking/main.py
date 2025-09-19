#!/usr/bin/env python3
"""
Therapy Booking System - Main Entry Point

FastAPI application for WhatsApp-based therapy booking with:
- Google ADK Agent Integration
- Natural language processing
- Coordinator approval workflow
- Appointment management
"""

import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Add src directory to Python path for development
src_path = Path(__file__).parent.parent.parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from therapy_booking.core.config import get_settings
from therapy_booking.core.database import create_tables, close_database
from therapy_booking.utils.logging_config import setup_logging
from therapy_booking.api import webhooks, appointments, therapists, health

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - startup and shutdown events"""
    
    # Startup
    logger.info("🚀 Starting Therapy Booking System...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    
    try:
        # Initialize database
        logger.info("📊 Initializing database...")
        create_tables()
        logger.info("✅ Database initialized successfully")
        
        # Initialize external services
        logger.info("🔗 Initializing external services...")
        # Add any service initialization here
        
        logger.info("✅ Therapy Booking System started successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("⏹️ Shutting down Therapy Booking System...")
    try:
        await close_database()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {str(e)}")
    
    logger.info("👋 Therapy Booking System shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Therapy Booking System",
    description="WhatsApp-based therapy booking system with Google ADK integration",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
app.include_router(therapists.router, prefix="/therapists", tags=["therapists"])
app.include_router(health.router, prefix="/health", tags=["health"])


@app.get("/", response_class=JSONResponse)
async def root() -> Dict[str, Any]:
    """Root endpoint - API information"""
    return {
        "service": "Therapy Booking System",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "features": [
            "WhatsApp Integration",
            "Google ADK Agent",
            "Natural Language Processing",
            "Appointment Management", 
            "Coordinator Workflow"
        ],
        "endpoints": {
            "health": "/health/",
            "webhooks": "/webhooks/",
            "appointments": "/appointments/",
            "therapists": "/therapists/",
            "docs": "/docs" if settings.DEBUG else None,
        }
    }


@app.get("/demo", response_class=HTMLResponse)
async def demo_interface():
    """Demo interface for testing the bot without WhatsApp"""
    if not settings.DEBUG:
        return JSONResponse(
            status_code=404,
            content={"detail": "Demo interface only available in debug mode"}
        )
    
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🩺 Therapy Booking Bot - Demo</title>
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
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .demo-info {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                font-size: 14px;
            }
            .message {
                margin: 10px 0;
                padding: 10px;
                border-radius: 10px;
            }
            .bot { background: #e3f2fd; }
            .user { background: #f1f8e9; text-align: right; }
            .input-container {
                display: flex;
                margin-top: 20px;
                gap: 10px;
            }
            input {
                flex: 1;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 20px;
                outline: none;
            }
            button {
                padding: 10px 20px;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 20px;
                cursor: pointer;
            }
            button:hover { background: #45a049; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🩺 Therapy Booking Bot</h1>
            <p><strong>Demo Interface</strong></p>
        </div>
        
        <div class="demo-info">
            <strong>📱 Try these commands:</strong><br>
            • "I want to book an appointment"<br>
            • "Check availability for tomorrow"<br>
            • "What services do you offer?"<br>
            • "Book therapy session for Friday 3pm"
        </div>
        
        <div class="chat-container">
            <div id="chat">
                <div class="message bot">
                    👋 Hello! I'm your therapy booking assistant. How can I help you today?
                </div>
            </div>
            <div class="input-container">
                <input type="text" id="messageInput" placeholder="Type your message..." 
                       onkeypress="if(event.key==='Enter') sendMessage()">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>

        <script>
            async function sendMessage() {
                const input = document.getElementById('messageInput');
                const chat = document.getElementById('chat');
                const message = input.value.trim();
                
                if (!message) return;
                
                // Add user message
                chat.innerHTML += `<div class="message user">${message}</div>`;
                input.value = '';
                
                try {
                    // Send to webhook
                    const response = await fetch('/webhooks/demo', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            messages: [{
                                from: 'demo_user',
                                text: {body: message},
                                type: 'text'
                            }]
                        })
                    });
                    
                    const result = await response.json();
                    
                    // Add bot response
                    const botMessage = result.response || "I'm processing your request...";
                    chat.innerHTML += `<div class="message bot">${botMessage}</div>`;
                    
                } catch (error) {
                    chat.innerHTML += `<div class="message bot">❌ Sorry, there was an error processing your message.</div>`;
                }
                
                // Scroll to bottom
                chat.scrollTop = chat.scrollHeight;
            }
        </script>
    </body>
    </html>
    """)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred",
        }
    )


def run_server():
    """Run the FastAPI server"""
    uvicorn.run(
        "therapy_booking.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
        access_log=True,
    )


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Therapy Booking System")
    parser.add_argument("--host", default=settings.HOST, help="Host to bind to")
    parser.add_argument("--port", type=int, default=settings.PORT, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", default=settings.DEBUG, 
                       help="Enable auto-reload")
    
    args = parser.parse_args()
    
    logger.info(f"🚀 Starting server on {args.host}:{args.port}")
    
    uvicorn.run(
        "therapy_booking.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()