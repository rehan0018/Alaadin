"""
Alaadin - Application Launcher
Starts the FastAPI server and serves both API and React frontend on http://localhost:8000
Usage:
    python run.py
"""

import os
import sys
import uvicorn

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    print("="*65)
    print("⚡ ALAADIN: Autonomous AI Payment Recovery Agent")
    print("   Starting server on http://localhost:8000 (or http://127.0.0.1:8000)")
    print("="*65)
    
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
