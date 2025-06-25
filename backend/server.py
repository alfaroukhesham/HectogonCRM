"""
Simple CRM Server Entry Point

This is the main entry point for the Tiny CRM application.
The actual application logic is now organized in the app/ directory.
"""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0", 
        port=8000,
        reload=True
    )