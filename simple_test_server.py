"""
Simple webhook test - bypass ADK agent
"""

from fastapi import FastAPI, Request
import json
import logging

# Setup simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Simple test server", "status": "running"}

@app.post("/webhook")
async def test_webhook(request: Request):
    """Simple webhook handler for testing"""
    try:
        logger.info("Webhook received!")
        
        # Get content type
        content_type = request.headers.get("content-type", "")
        logger.info(f"Content-Type: {content_type}")
        
        if "application/json" in content_type:
            # Handle JSON payload
            payload = await request.json()
            logger.info(f"JSON payload: {payload}")
            
            if 'data' in payload:
                data = payload['data']
                from_phone = data.get('from', '')
                message_text = data.get('body', '')
                
                logger.info(f"From: {from_phone}, Message: {message_text}")
                
                # Simple response without ADK agent
                response_message = f"Hello! I received your message: '{message_text}'. This is a test response from the booking system."
                
                return {
                    "status": "ok", 
                    "message": "Message processed successfully",
                    "response": response_message
                }
        
        return {"status": "ok", "message": "Webhook processed"}
        
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)