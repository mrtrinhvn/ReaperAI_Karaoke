#!/bin/bash
# decision-log.sh — Event-sourced decision tracking (inspired by GStack)
# Usage:
#   bash .agent/decisions/decision-log.sh log "Decision text" "Rationale" [scope] [confidence]
#   bash .agent/decisions/decision-log.sh search "keyword"
#   bash .agent/decisions/decision-log.sh recent [N]
#   bash .agent/decisions/decision-log.sh supersede <id> "New decision" "New rationale"
#   bash .agent/decisions/decision-log.sh list

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/decisions.jsonl"

# Ensure log file exists
touch "$LOG_FILE"

get_next_id() {
    if [ ! -s "$LOG_FILE" ]; then
        echo 1
    else
        local max_id
        max_id=$(grep -oP '"id":\s*\K[0-9]+' "$LOG_FILE" | sort -n | tail -1)
        echo $((max_id + 1))
    fi
}

cmd_log() {
    local decision="${1:?Decision text required}"
    local rationale="${2:?Rationale required}"
    local scope="${3:-project}"      # project|feature|session
    local confidence="${4:-7}"       # 1-10
    local source="${5:-agent}"       # user|agent|review
    local id
    id=$(get_next_id)
    local timestamp
    timestamp=$(date -Iseconds)

    local entry
    entry=$(cat <<EOF
{"id":$id,"decision":"$decision","rationale":"$rationale","scope":"$scope","confidence":$confidence,"source":"$source","status":"active","timestamp":"$timestamp","superseded_by":null}
EOF
)
    echo "$entry" >> "$LOG_FILE"
    echo "✅ Decision #$id logged: $decision"
}

cmd_search() {
    local keyword="${1:?Keyword required}"
    if [ ! -s "$LOG_FILE" ]; then
        echo "No decisions recorded yet."
        return
    fi
    echo "🔍 Decisions matching '$keyword':"
    echo "---"
    grep -i "$keyword" "$LOG_FILE" | while IFS= read -r line; do
        local id decision status
        id=$(echo "$line" | grep -oP '"id":\s*\K[0-9]+')
        decision=$(echo "$line" | grep -oP '"decision":\s*"\K[^"]+')
        status=$(echo "$line" | grep -oP '"status":\s*"\K[^"]+')
        local marker="✅"
        [ "$status" = "superseded" ] && marker="⛔"
        echo "  $marker #$id: $decision"
    done
}

cmd_recent() {
    local n="${1:-5}"
    if [ ! -s "$LOG_FILE" ]; then
        echo "No decisions recorded yet."
        return
    fi
    echo "📋 Last $n decisions:"
    echo "---"
    tail -n "$n" "$LOG_FILE" | while IFS= read -r line; do
        local id decision rationale status timestamp
        id=$(echo "$line" | grep -oP '"id":\s*\K[0-9]+')
        decision=$(echo "$line" | grep -oP '"decision":\s*"\K[^"]+')
        rationale=$(echo "$line" | grep -oP '"rationale":\s*"\K[^"]+')
        status=$(echo "$line" | grep -oP '"status":\s*"\K[^"]+')
        timestamp=$(echo "$line" | grep -oP '"timestamp":\s*"\K[^"]+')
        local marker="✅"
        [ "$status" = "superseded" ] && marker="⛔"
        echo "  $marker #$id [$timestamp]: $decision"
        echo "     └─ Rationale: $rationale"
    done
}

cmd_supersede() {
    local old_id="${1:?Old decision ID required}"
    local new_decision="${2:?New decision text required}"
    local new_rationale="${3:?New rationale required}"

    if ! grep -q "\"id\":$old_id," "$LOG_FILE" 2>/dev/null; then
        echo "❌ Decision #$old_id not found"
        return 1
    fi

    # Mark old as superseded
    sed -i "s/\"id\":$old_id,\(.*\)\"status\":\"active\"/\"id\":$old_id,\1\"status\":\"superseded\"/" "$LOG_FILE"

    # Log new decision with reference
    local new_id
    new_id=$(get_next_id)
    local timestamp
    timestamp=$(date -Iseconds)

    local entry
    entry=$(cat <<EOF
{"id":$new_id,"decision":"$new_decision","rationale":"$new_rationale (supersedes #$old_id)","scope":"project","confidence":8,"source":"agent","status":"active","timestamp":"$timestamp","superseded_by":null}
EOF
)
    echo "$entry" >> "$LOG_FILE"

    # Update old entry's superseded_by
    sed -i "s/\"id\":$old_id,\(.*\)\"superseded_by\":null/\"id\":$old_id,\1\"superseded_by\":$new_id/" "$LOG_FILE"

    echo "✅ Decision #$old_id superseded by #$new_id: $new_decision"
}

cmd_list() {
    if [ ! -s "$LOG_FILE" ]; then
        echo "No decisions recorded yet."
        return
    fi
    echo "📋 All active decisions:"
    echo "---"
    grep '"status":"active"' "$LOG_FILE" | while IFS= read -r line; do
        local id decision rationale confidence
        id=$(echo "$line" | grep -oP '"id":\s*\K[0-9]+')
        decision=$(echo "$line" | grep -oP '"decision":\s*"\K[^"]+')
        rationale=$(echo "$line" | grep -oP '"rationale":\s*"\K[^"]+')
        confidence=$(echo "$line" | grep -oP '"confidence":\s*\K[0-9]+')
        echo "  ✅ #$id [confidence:$confidence]: $decision"
        echo "     └─ $rationale"
    done
}

# Main dispatcher
case "${1:-help}" in
    log)       shift; cmd_log "$@" ;;
    search)    shift; cmd_search "$@" ;;
    recent)    shift; cmd_recent "$@" ;;
    supersede) shift; cmd_supersede "$@" ;;
    list)      shift; cmd_list "$@" ;;
    help|*)
        echo "Decision Log — Event-sourced decision tracking"
        echo ""
        echo "Usage:"
        echo "  decision-log.sh log <decision> <rationale> [scope] [confidence] [source]"
        echo "  decision-log.sh search <keyword>"
        echo "  decision-log.sh recent [N]"
        echo "  decision-log.sh supersede <id> <new_decision> <new_rationale>"
        echo "  decision-log.sh list"
        echo ""
        echo "Scope: project | feature | session"
        echo "Confidence: 1-10"
        echo "Source: user | agent | review"
        ;;
esac
