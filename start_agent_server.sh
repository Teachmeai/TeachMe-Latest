#!/bin/bash
echo "Starting Super Admin Agent Server..."
cd "$(dirname "$0")"
python3 agents/start_agent_server.py
