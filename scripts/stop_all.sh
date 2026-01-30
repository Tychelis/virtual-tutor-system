#!/bin/bash

# ============================================
# Virtual Tutor System - Stop All Services Script
# ============================================

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
FORCE_MODE=false
CLEAN_LOGS=false
QUIET_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE_MODE=true
            shift
            ;;
        -c|--clean)
            CLEAN_LOGS=true
            shift
            ;;
        -q|--quiet)
            QUIET_MODE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -f, --force    Force mode: immediately use SIGKILL to stop all processes"
            echo "  -c, --clean    Automatically clean log files"
            echo "  -q, --quiet    Quiet mode: reduce output"
            echo "  -h, --help     Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0              # Normal stop (graceful shutdown)"
            echo "  $0 -f           # Force stop"
            echo "  $0 -f -c        # Force stop and clean logs"
            echo "  $0 -q           # Quiet mode stop"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for help"
            exit 1
            ;;
    esac
done

if [ "$QUIET_MODE" = false ]; then
    echo "Stopping Virtual Tutor System..."
    echo "===================================="
    if [ "$FORCE_MODE" = true ]; then
        echo -e "${YELLOW}Force mode enabled${NC}"
    fi
    echo ""
fi

# Define all services
declare -A SERVICES
SERVICES=(
    ["Frontend"]="react-scripts|node.*frontend:3000"
    ["Avatar Manager"]="python3.*api.py.*avatar-manager|avatar-manager/api.py:8607"
    ["Avatar Instance 1"]="python.*app.py.*avatar_id.*8615:8615"
    ["Avatar Instance 2"]="python.*app.py.*avatar_id.*8616:8616"
    ["Avatar Instance 3"]="python.*app.py.*avatar_id.*8617:8617"
    ["Avatar Instance 4"]="python.*app.py.*avatar_id.*8618:8618"
    ["Avatar Instance 5"]="python.*app.py.*avatar_id.*8619:8619"
    ["Avatar Config"]="live_server.py:8606"
    ["Edge TTS"]="edge.*server.py|tts.*server.py:8604"
    ["CosyVoice TTS"]="cosyvoice.*server.py:8605"
    ["LLM (Optimized)"]="gunicorn.*api_interface_optimized|python.*api_interface_optimized.py:8611"
    ["LLM (Legacy)"]="python.*api_interface.py:8610"
    ["RAG"]="python.*app.py.*rag:8602"
    ["Backend"]="gunicorn.*app:create_app|python.*run.py:8203"
)

# Function to stop a single service
stop_service() {
    local service_name=$1
    local pattern_port=$2
    local pattern=$(echo "$pattern_port" | cut -d: -f1)
    local port=$(echo "$pattern_port" | cut -d: -f2)
    
    if [ "$QUIET_MODE" = false ]; then
        echo -n "Stopping ${service_name} (port ${port})..."
    fi
    
    # Find processes - try multiple patterns
    local pids=""
    IFS='|' read -ra PATTERNS <<< "$pattern"
    for p in "${PATTERNS[@]}"; do
        local found_pids=$(pgrep -f "$p" 2>/dev/null)
        if [ -n "$found_pids" ]; then
            pids="$pids $found_pids"
        fi
    done
    
    # Remove duplicates
    pids=$(echo "$pids" | tr ' ' '\n' | sort -u | tr '\n' ' ')
    
    if [ -z "$pids" ]; then
        if [ "$QUIET_MODE" = false ]; then
            echo -e " ${YELLOW}Not running${NC}"
        fi
        return 0
    fi
    
    if [ "$FORCE_MODE" = true ]; then
        # Force mode: direct SIGKILL
        for pid in $pids; do
            kill -9 $pid 2>/dev/null
        done
        sleep 1
    else
        # Graceful mode: SIGTERM first, then SIGKILL
        for pid in $pids; do
            kill $pid 2>/dev/null
        done
        sleep 2
        
        # Check if still running
        local still_running=false
        for pid in $pids; do
            if ps -p $pid > /dev/null 2>&1; then
                still_running=true
                kill -9 $pid 2>/dev/null
            fi
        done
        
        if [ "$still_running" = true ]; then
            sleep 1
        fi
    fi
    
    # Final check
    local success=true
    for pid in $pids; do
        if ps -p $pid > /dev/null 2>&1; then
            success=false
            break
        fi
    done
    
    if [ "$success" = true ]; then
        if [ "$QUIET_MODE" = false ]; then
            echo -e " ${GREEN}Stopped${NC}"
        fi
        return 0
    else
        if [ "$QUIET_MODE" = false ]; then
            echo -e " ${RED}Failed to stop${NC}"
        fi
        return 1
    fi
}

# Stop all services in order
SERVICE_ORDER=("Frontend" "Avatar Instance 1" "Avatar Instance 2" "Avatar Instance 3" "Avatar Instance 4" "Avatar Instance 5" "Avatar Manager" "Avatar Config" "Edge TTS" "CosyVoice TTS" "LLM (Optimized)" "LLM (Legacy)" "RAG" "Backend")

for service in "${SERVICE_ORDER[@]}"; do
    if [ -n "${SERVICES[$service]}" ]; then
        stop_service "$service" "${SERVICES[$service]}"
    fi
done

if [ "$QUIET_MODE" = false ]; then
    echo ""
    echo "Waiting for ports to be released..."
fi
sleep 2

# Additional cleanup: force cleanup via ports
if [ "$FORCE_MODE" = true ]; then
    if [ "$QUIET_MODE" = false ]; then
        echo ""
        echo "Force cleaning residual processes via ports..."
    fi
    
    PORTS=(3000 8619 8618 8617 8616 8615 8607 8606 8605 8604 8611 8610 8602 8203)
    for port in "${PORTS[@]}"; do
        PIDS=$(lsof -ti :$port 2>/dev/null)
        if [ -n "$PIDS" ]; then
            if [ "$QUIET_MODE" = false ]; then
                echo "  Force cleaning processes on port $port..."
            fi
            echo "$PIDS" | xargs kill -9 2>/dev/null
        fi
    done
    sleep 1
fi

# Check final status
if [ "$QUIET_MODE" = false ]; then
    echo ""
    echo "===================================="
    echo "Port Status Check..."
    echo ""
fi

check_port_status() {
    local port=$1
    local name=$2
    
    if lsof -i :$port 2>/dev/null | grep -q LISTEN; then
        if [ "$QUIET_MODE" = false ]; then
            echo -e "  ${RED}[X] $name (port $port) - Still in use${NC}"
            lsof -i :$port 2>/dev/null | grep LISTEN | awk '{print "     PID:", $2, "Process:", $1}'
        fi
        return 1
    else
        if [ "$QUIET_MODE" = false ]; then
            echo -e "  ${GREEN}[OK] $name (port $port) - Released${NC}"
        fi
        return 0
    fi
}

ALL_CLEAR=true
check_port_status 3000 "Frontend" || ALL_CLEAR=false
check_port_status 8619 "Avatar Instance 5" || ALL_CLEAR=false
check_port_status 8618 "Avatar Instance 4" || ALL_CLEAR=false
check_port_status 8617 "Avatar Instance 3" || ALL_CLEAR=false
check_port_status 8616 "Avatar Instance 2" || ALL_CLEAR=false
check_port_status 8615 "Avatar Instance 1" || ALL_CLEAR=false
check_port_status 8607 "Avatar Manager" || ALL_CLEAR=false
check_port_status 8606 "Avatar Config" || ALL_CLEAR=false
check_port_status 8605 "CosyVoice TTS" || ALL_CLEAR=false
check_port_status 8604 "Edge TTS" || ALL_CLEAR=false
check_port_status 8611 "LLM (Optimized)" || ALL_CLEAR=false
check_port_status 8602 "RAG" || ALL_CLEAR=false
check_port_status 8203 "Backend" || ALL_CLEAR=false

if [ "$QUIET_MODE" = false ]; then
    echo ""
    echo "===================================="
fi

# Summary
if [ "$ALL_CLEAR" = true ]; then
    if [ "$QUIET_MODE" = false ]; then
        echo -e "${GREEN}All services stopped successfully!${NC}"
    fi
else
    if [ "$QUIET_MODE" = false ]; then
        echo -e "${YELLOW}Warning: Some services did not stop completely${NC}"
        echo ""
        echo "Suggestions:"
        echo "  1. Use force mode: $0 -f"
        echo "  2. Manually check processes: ps aux | grep -E 'python|node|react'"
        echo "  3. Use sudo: sudo $0 -f"
    fi
fi

# Log cleanup
# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Find all log files recursively from common log directories
LOG_DIRS=(
    "$SCRIPT_DIR/logs"
    "$SCRIPT_DIR/backend/logs"
    "$SCRIPT_DIR/llm/logs"
    "$SCRIPT_DIR/avatar-manager/logs"
)

# Find all .log files in these directories
LOG_FILES=()
for dir in "${LOG_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        mapfile -d '' -t files < <(find "$dir" -name "*.log" -type f -print0 2>/dev/null)
        LOG_FILES+=("${files[@]}")
    fi
done

# Also check for loose log files
LOOSE_LOG_FILES=(
    "$SCRIPT_DIR/backend/error.log"
    "$SCRIPT_DIR/rag/app.log"
    "$SCRIPT_DIR/lip-sync/live_server.log"
    "$SCRIPT_DIR/lip-sync/livetalking.log"
    "$SCRIPT_DIR/livetalking.log"
)

for file in "${LOOSE_LOG_FILES[@]}"; do
    if [ -f "$file" ]; then
        LOG_FILES+=("$file")
    fi
done

# Display log file sizes
if [ "$QUIET_MODE" = false ] && [ "$CLEAN_LOGS" = false ]; then
    echo ""
    echo "Log Files:"
    for log in "${LOG_FILES[@]}"; do
        if [ -f "$log" ]; then
            SIZE=$(du -h "$log" 2>/dev/null | cut -f1)
            echo "  $log ($SIZE)"
        fi
    done
fi

# Handle log cleanup
if [ "$CLEAN_LOGS" = true ]; then
    # Auto cleanup
    for log in "${LOG_FILES[@]}"; do
        rm -f "$log" 2>/dev/null
    done
    if [ "$QUIET_MODE" = false ]; then
        echo -e "${GREEN}Logs cleaned${NC}"
    fi
elif [ "$QUIET_MODE" = false ]; then
    # Ask whether to clean
    echo ""
    read -p "Clean log files? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for log in "${LOG_FILES[@]}"; do
            rm -f "$log" 2>/dev/null
        done
        echo -e "${GREEN}Logs cleaned${NC}"
    else
        echo "Logs preserved"
    fi
fi

if [ "$QUIET_MODE" = false ]; then
    echo ""
    echo "===================================="
    echo ""
    echo "Tips:"
    echo "  - Normal stop: ./stop_all.sh"
    echo "  - Force stop: ./stop_all.sh -f"
    echo "  - Quiet mode: ./stop_all.sh -q"
    echo "  - Show help: ./stop_all.sh -h"
    echo ""
fi

# Return status code
if [ "$ALL_CLEAR" = true ]; then
    exit 0
else
    exit 1
fi

