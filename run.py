#!/usr/bin/env python3
"""
Chat API Startup Script
Run this file to start the chat application
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    print(f"🚀 Starting Chat API on {host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"🔌 WebSocket endpoint: ws://{host}:{port}/ws/{{room_id}}")
    print(f"🌐 Frontend: Open frontend/index.html in your browser")
    print(f"🔄 Auto-reload: {'Enabled' if reload else 'Disabled'}")
    print("=" * 50)
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )