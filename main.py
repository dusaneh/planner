# plannerv2/main.py

import uvicorn
from fastapi import FastAPI
from plannerv2.routers import admin_main, chatbot

def create_app() -> FastAPI:
    app = FastAPI()
    # Include the main admin router
    app.include_router(admin_main.router)
    # Include the chatbot router
    app.include_router(chatbot.router)
    return app

app = create_app()

if __name__ == "__main__":
    import signal
    import sys
    
    def signal_handler(sig, frame):
        print("\nShutting down gracefully...")
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)