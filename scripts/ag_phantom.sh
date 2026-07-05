#!/bin/bash

# 👻 Elite OS: Phantom Swarm Orchestrator
# Manage headless background agents and restore them to the UI.

ACTION=$1
ID=$2 # Instance ID (port offset)
PROJECT=$3

BASE_PORT=9555
IDE_PORT=$((BASE_PORT + ID))
BRIDGE_PORT=$((IDE_PORT + 100))

case $ACTION in
  "start")
    echo "🚀 Starring Phantom Agent [$ID] for $PROJECT..."
    # Start in headless mode (no display)
    DISPLAY="" nohup antigravity $PROJECT --remote-debugging-port=$IDE_PORT > /dev/null 2>&1 &
    # Start the bridge
    IDE_PORT=$IDE_PORT BRIDGE_PORT=$BRIDGE_PORT nohup npx tsx scripts/ag_portal_bridge.js > /dev/null 2>&1 &
    echo "✅ Phantom [$ID] is running at port $IDE_PORT (Headless)"
    ;;
  
  "restore")
    echo "👁️ Restoring Phantom Agent [$ID] to UI..."
    # Stop the headless instance
    pkill -f "remote-debugging-port=$IDE_PORT"
    sleep 1
    # Restart with Display
    DISPLAY=:0 nohup antigravity $PROJECT --remote-debugging-port=$IDE_PORT > /dev/null 2>&1 &
    echo "✅ Agent [$ID] is now VISIBLE on Display :0"
    ;;

  "hide")
    echo "🙈 Hiding Agent [$ID] (Moving to Background)..."
    pkill -f "remote-debugging-port=$IDE_PORT"
    sleep 1
    DISPLAY="" nohup antigravity $PROJECT --remote-debugging-port=$IDE_PORT > /dev/null 2>&1 &
    echo "✅ Agent [$ID] is now STEALTH (Headless)"
    ;;

  "list")
    echo "📊 Active Phantom Swarm:"
    ps aux | grep "remote-debugging-port" | grep -v grep | awk '{print "ID: " $NF " | PID: " $2}'
    ;;

  *)
    echo "Usage: ag_phantom [start|restore|hide|list] [ID] [ProjectDir]"
    ;;
esac
