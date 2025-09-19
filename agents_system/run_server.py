#!/usr/bin/env python3
"""Simple server runner for the agents system."""

import os
import sys
import uvicorn
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # Change to project root
    os.chdir(project_root)
    
    # Start the server
    uvicorn.run(
        "agents_system.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
