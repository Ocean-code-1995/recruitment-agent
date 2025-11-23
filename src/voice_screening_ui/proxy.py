"""
WebSocket proxy for OpenAI Realtime API.
Handles authentication since browsers cannot set custom headers in WebSocket connections.
"""
import asyncio
import os
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import aiohttp
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice Screening WebSocket Proxy")

# Enable CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your Streamlit domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime?model=gpt-realtime-mini"


@app.websocket("/ws/realtime")
async def websocket_proxy(websocket: WebSocket):
    """
    Proxy WebSocket connection to OpenAI Realtime API.
    Adds proper authentication headers that browsers cannot set.
    """
    client_id = id(websocket)
    logger.info(f"[{client_id}] Client connecting...")
    
    await websocket.accept()
    logger.info(f"[{client_id}] Client connected")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        error_msg = "API key not configured"
        logger.error(f"[{client_id}] {error_msg}")
        await websocket.close(code=1008, reason=error_msg)
        return
    
    try:
        # Connect to OpenAI Realtime API using aiohttp (better header support)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        logger.info(f"[{client_id}] Connecting to OpenAI Realtime API: {OPENAI_REALTIME_URL}")
        
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                OPENAI_REALTIME_URL,
                headers=headers
            ) as openai_ws:
                logger.info(f"[{client_id}] Connected to OpenAI Realtime API")
                
                # Send connection success message to client
                await websocket.send_json({
                    "type": "proxy.status",
                    "status": "connected",
                    "message": "Proxy connected to OpenAI Realtime API"
                })
                
                # Bidirectional message forwarding
                async def forward_to_openai():
                    """Forward messages from client to OpenAI."""
                    try:
                        async for message in websocket.iter_text():
                            try:
                                # Log message for debugging
                                msg_data = json.loads(message) if message else {}
                                msg_type = msg_data.get("type", "unknown")
                                logger.debug(f"[{client_id}] Client -> OpenAI: {msg_type}")
                                
                                await openai_ws.send_str(message)
                            except json.JSONDecodeError:
                                logger.warning(f"[{client_id}] Invalid JSON from client: {message[:100]}")
                                await openai_ws.send_str(message)
                    except WebSocketDisconnect:
                        logger.info(f"[{client_id}] Client disconnected")
                    except Exception as e:
                        error_msg = f"Error forwarding to OpenAI: {str(e)}"
                        logger.error(f"[{client_id}] {error_msg}", exc_info=True)
                        try:
                            await websocket.send_json({
                                "type": "proxy.error",
                                "error": error_msg,
                                "source": "forward_to_openai"
                            })
                        except:
                            pass
                
                async def forward_to_client():
                    """Forward messages from OpenAI to client."""
                    try:
                        async for msg in openai_ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                try:
                                    # Log message for debugging
                                    msg_data = json.loads(msg.data) if msg.data else {}
                                    msg_type = msg_data.get("type", "unknown")
                                    logger.debug(f"[{client_id}] OpenAI -> Client: {msg_type}")
                                    
                                    await websocket.send_text(msg.data)
                                except Exception as e:
                                    logger.error(f"[{client_id}] Error sending message to client: {e}")
                                    await websocket.send_json({
                                        "type": "proxy.error",
                                        "error": f"Error sending message: {str(e)}",
                                        "source": "forward_to_client"
                                    })
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                error = openai_ws.exception()
                                error_msg = f"WebSocket error from OpenAI: {error}"
                                logger.error(f"[{client_id}] {error_msg}")
                                await websocket.send_json({
                                    "type": "proxy.error",
                                    "error": error_msg,
                                    "source": "openai_websocket"
                                })
                                break
                            elif msg.type == aiohttp.WSMsgType.CLOSE:
                                logger.info(f"[{client_id}] OpenAI closed connection: {msg.data}")
                                break
                            else:
                                logger.warning(f"[{client_id}] Unexpected message type from OpenAI: {msg.type}")
                    except Exception as e:
                        error_msg = f"Error forwarding to client: {str(e)}"
                        logger.error(f"[{client_id}] {error_msg}", exc_info=True)
                        try:
                            await websocket.send_json({
                                "type": "proxy.error",
                                "error": error_msg,
                                "source": "forward_to_client"
                            })
                        except:
                            pass
                
                # Run both forwarding tasks concurrently
                results = await asyncio.gather(
                    forward_to_openai(),
                    forward_to_client(),
                    return_exceptions=True
                )
                
                # Log any exceptions from the tasks
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"[{client_id}] Task {i} raised exception: {result}", exc_info=True)
            
    except aiohttp.ClientError as e:
        error_msg = f"OpenAI connection failed: {str(e)}"
        logger.error(f"[{client_id}] {error_msg}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "proxy.error",
                "error": error_msg,
                "source": "connection"
            })
        except:
            pass
        await websocket.close(code=1008, reason=error_msg)
    except Exception as e:
        error_msg = f"Proxy error: {str(e)}"
        logger.error(f"[{client_id}] {error_msg}", exc_info=True)
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({
                "type": "proxy.error",
                "error": error_msg,
                "source": "proxy",
                "traceback": traceback.format_exc()
            })
        except:
            pass
        await websocket.close(code=1011, reason=error_msg)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "openai_api_key_configured": bool(os.getenv("OPENAI_API_KEY"))
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

