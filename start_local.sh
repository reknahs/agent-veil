#!/bin/bash

# AgentVeil Unified Local Startup Script
# This script launches the Next.js frontend and all three Python AI agents in parallel.

echo "==============================================="
echo "🚀 Starting AgentVeil Local Development Environment"
echo "==============================================="

# Aggressive Pre-Boot Cleanup (Ensures no restart issues)
echo "🧹 Cleaning up any hanging processes and locks..."
# Kill any "ghosts" hogging our specific application ports
lsof -ti:8000,8001,8002,3000 | xargs kill -9 2>/dev/null || true
# Kill any lingering Next.js or Python API processes
pkill -f "python -m ui_agent.api" 2>/dev/null || true
pkill -f "python -m fixer.api" 2>/dev/null || true
pkill -f "python logic_agent/api.py" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
# Delete the Next.js dev lock file which can get stuck and prevent booting
rm -f .next/dev/lock

# Function to safely kill background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down all AgentVeil services..."
    # Forcefully kill the background API services we started
    pkill -f "python -m ui_agent.api"
    pkill -f "python -m fixer.api"
    pkill -f "python logic_agent/api.py"
    # Kill any lingering Next.js nodes attached to this script
    pkill -f "next dev"
    exit 0
}

# Trap Ctrl+C (SIGINT) and call cleanup
trap cleanup SIGINT SIGTERM

# 1. Start the UI Agent (Port 8000)
echo "📦 Starting UI Agent (Port 8000)..."
if [ -d "logic_agent/.venv" ]; then
    logic_agent/.venv/bin/python -m ui_agent.api &
else
    python -m ui_agent.api &
fi
echo "✅ UI Agent running"

# 2. Start the Fixer Agent (Port 8001)
echo "📦 Starting Fixer Agent (Port 8001)..."
if [ -d "fixer/.venv" ]; then
    fixer/.venv/bin/python -m fixer.api &
else
    python -m fixer.api &
fi
echo "✅ Fixer Agent running"

# 3. Start the Logic Agent (Port 8002)
echo "📦 Starting Logic Agent (Port 8002)..."
if [ -d "logic_agent/.venv" ]; then
    logic_agent/.venv/bin/python logic_agent/api.py &
else
    python logic_agent/api.py &
fi
echo "✅ Logic Agent running"

echo "==============================================="
echo "✨ AgentVeil is fully live!"
echo "-> Frontend: http://localhost:3000"
echo "-> UI Agent API: http://127.0.0.1:8000"
echo "-> Fixer Agent API: http://127.0.0.1:8001"
echo "-> Logic Agent API: http://127.0.0.1:8002"
echo "-> Press [Ctrl+C] to gracefully stop all services at once."
echo "==============================================="

# Auto-open the browser on Mac after a 3 second delay
(sleep 3 && open "http://localhost:3000" 2>/dev/null || true) &

# 4. Start the Next.js Frontend
echo "🌐 Starting Next.js Frontend..."
# Add a small delay so the Python backends bind their ports first
sleep 2

# Force the subshell to load NVM and use Node 20+ required by Next.js
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 20 2>/dev/null || nvm install 20

npm run dev &

# Wait for all background processes (allows trap to instantly catch Ctrl+C)
wait
