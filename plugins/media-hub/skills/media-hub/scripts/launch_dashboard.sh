#!/usr/bin/env bash
# ==============================================================================
# Antigravity Media Hub & Command Center Launcher
# Starts Dashboard HTTP Server + Agent Queue Watcher + Optional Cloudflare Tunnel
# ==============================================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT=8888

echo "=================================================="
echo "🚀 Starting Antigravity Media Hub Dashboard v2.4"
echo "=================================================="

# Check if port 8888 is already running
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️ Port $PORT is already in use. Killing previous server instance..."
    pkill -f "media-hub/scripts/server.py" || true
    sleep 1
fi

# 1. Start Server
python3 "$DIR/server.py" &
SERVER_PID=$!
echo "✅ Media Hub Server running on http://127.0.0.1:$PORT (PID: $SERVER_PID)"

# 2. Start Agent Queue Watcher Daemon
python3 "$DIR/agent_queue_watcher.py" &
WATCHER_PID=$!
echo "✅ Agent Queue Watcher Daemon running (PID: $WATCHER_PID)"

# 3. Optional Cloudflare Tunnel
if command -v cloudflared &> /dev/null; then
    echo "🌐 Starting Cloudflare Public Tunnel..."
    cloudflared tunnel --url http://127.0.0.1:$PORT &
    TUNNEL_PID=$!
    echo "✅ Cloudflare Tunnel started (PID: $TUNNEL_PID)"
fi

echo "=================================================="
echo "🎉 Dashboard is READY! Open: http://127.0.0.1:$PORT"
echo "=================================================="

wait $SERVER_PID
