#!/bin/bash

# ============================================
# Stop All Avatar Instances Script
# ============================================

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Avatar Manager API URL
API_URL="http://localhost:8607"

echo ""
echo "Stopping All Avatar Instances..."
echo "===================================="
echo ""

# Check if Avatar Manager is running
if ! curl -s "${API_URL}/health" > /dev/null 2>&1; then
    echo -e "${RED}Error: Avatar Manager is not running at ${API_URL}${NC}"
    echo "Please start Avatar Manager first with: cd avatar-manager && python3 api.py"
    exit 1
fi

# Get list of running avatars
echo "Checking running avatar instances..."
echo ""

AVATARS_JSON=$(curl -s "${API_URL}/avatar/list")

# Check if we got a valid response
if [ $? -ne 0 ] || [ -z "$AVATARS_JSON" ]; then
    echo -e "${RED}Error: Failed to connect to Avatar Manager${NC}"
    exit 1
fi

# Parse avatar count
AVATAR_COUNT=$(echo "$AVATARS_JSON" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('count', 0))" 2>/dev/null)

if [ -z "$AVATAR_COUNT" ] || [ "$AVATAR_COUNT" = "0" ]; then
    echo -e "${GREEN}No running avatar instances found${NC}"
    echo ""
    exit 0
fi

echo -e "${YELLOW}Found ${AVATAR_COUNT} running avatar instance(s)${NC}"
echo ""

# Stop all avatars using the API
echo "Stopping all avatar instances..."
RESPONSE=$(curl -s -X POST "${API_URL}/avatar/stop-all" -H "Content-Type: application/json")

# Check response
if echo "$RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}All avatar instances stopped successfully${NC}"
else
    echo -e "${RED}Warning: Some avatar instances may not have stopped properly${NC}"
    echo "Response: $RESPONSE"
fi

echo ""
echo "Verifying..."
sleep 2

# Check if any avatars are still running
FINAL_CHECK=$(curl -s "${API_URL}/avatar/list")
REMAINING_COUNT=$(echo "$FINAL_CHECK" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('count', 0))" 2>/dev/null)

if [ "$REMAINING_COUNT" = "0" ]; then
    echo -e "${GREEN}All avatar instances confirmed stopped${NC}"
    echo ""
else
    echo -e "${YELLOW}Warning: ${REMAINING_COUNT} avatar instance(s) still running${NC}"
    echo ""
    echo "Remaining instances:"
    echo "$FINAL_CHECK" | python3 -m json.tool 2>/dev/null
    echo ""
fi

# Clean up zombie processes on GPU
echo "Cleaning up zombie processes on GPU..."
echo ""

# Function to clean up zombie GPU processes
cleanup_zombie_gpu_processes() {
    echo "Checking for zombie GPU processes..."
    
    # Create a Python script to clean up zombie processes
    python3 << 'ZOMBIE_CLEANUP_EOF'
import subprocess
import os
import signal
import sys

try:
    import pynvml
    pynvml.nvmlInit()
    NVML_AVAILABLE = True
except (ImportError, Exception) as e:
    NVML_AVAILABLE = False
    print(f"Warning: pynvml not available: {e}")
    print("Attempting cleanup using nvidia-smi...")

zombie_count = 0
total_memory_freed = 0

if NVML_AVAILABLE:
    try:
        # Check all GPUs
        gpu_count = pynvml.nvmlDeviceGetCount()
        print(f"Found {gpu_count} GPU(s)")
        print("")
        
        for gpu_id in range(gpu_count):
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                
                print(f"GPU {gpu_id}: {info.used / (1024**2):.1f} MB / {info.total / (1024**2):.1f} MB used")
                
                # Get all compute processes
                try:
                    processes = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
                    
                    for proc in processes:
                        pid = proc.pid
                        mem_mb = proc.usedGpuMemory / (1024**2)
                        
                        # Check if process exists
                        try:
                            os.kill(pid, 0)  # Check if process exists
                            # Process exists, skip
                            continue
                        except (OSError, ProcessLookupError):
                            # Process does not exist - it's a zombie
                            print(f"  Found zombie process PID {pid}: {mem_mb:.1f} MB")
                            zombie_count += 1
                            total_memory_freed += mem_mb
                            
                            # Try to clean up (though this may not work for zombies)
                            try:
                                # Attempt to kill -9 (though process may already be dead)
                                os.kill(pid, signal.SIGKILL)
                                print(f"    Attempted to clean up PID {pid}")
                            except (OSError, ProcessLookupError):
                                print(f"    Process {pid} already cleaned up or inaccessible")
                                
                except Exception as e:
                    print(f"  Error getting processes for GPU {gpu_id}: {e}")
                    
            except Exception as e:
                print(f"Error accessing GPU {gpu_id}: {e}")
                
    except Exception as e:
        print(f"Error during cleanup: {e}")
else:
    # Fallback: Use nvidia-smi to find zombie processes
    print("Using nvidia-smi to detect zombie processes...")
    try:
        result = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader,nounits'],
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split(', ')
                    if len(parts) >= 2:
                        try:
                            pid = int(parts[0].strip())
                            mem = int(parts[1].strip())
                            
                            # Check if process exists
                            try:
                                os.kill(pid, 0)
                                # Process exists
                                continue
                            except (OSError, ProcessLookupError):
                                # Zombie process
                                print(f"  Found zombie process PID {pid}: {mem} MB")
                                zombie_count += 1
                                total_memory_freed += mem
                                
                                # Try to clean up
                                try:
                                    os.kill(pid, signal.SIGKILL)
                                    print(f"    Attempted to clean up PID {pid}")
                                except (OSError, ProcessLookupError):
                                    print(f"    Process {pid} already cleaned up or inaccessible")
                        except (ValueError, IndexError):
                            pass
    except Exception as e:
        print(f"Error using nvidia-smi: {e}")

print("")
if zombie_count > 0:
    print(f"Found {zombie_count} zombie process(es) with {total_memory_freed:.1f} MB GPU memory")
    print("Note: GPU memory from zombie processes will be automatically freed when new processes need it")
    print("      or when the GPU is reset. If memory is still occupied, you may need to restart the system.")
else:
    print("No zombie GPU processes found")

print("")
ZOMBIE_CLEANUP_EOF
}

# Call the cleanup function
cleanup_zombie_gpu_processes

# Clean up avatar logs
echo "Cleaning up avatar logs..."
echo ""

# Get script directory (assumes script is in scripts/ or avatar-manager/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Avatar log directory
AVATAR_LOG_DIR="${PROJECT_ROOT}/avatar-manager/logs"

# Find all avatar log files
AVATAR_LOG_FILES=()
if [ -d "$AVATAR_LOG_DIR" ]; then
    # Find files matching avatar_*.log pattern
    while IFS= read -r -d '' file; do
        AVATAR_LOG_FILES+=("$file")
    done < <(find "$AVATAR_LOG_DIR" -name "avatar_*.log" -type f -print0 2>/dev/null)
fi

# Display log files
if [ ${#AVATAR_LOG_FILES[@]} -gt 0 ]; then
    echo "Found ${#AVATAR_LOG_FILES[@]} avatar log file(s):"
    TOTAL_SIZE=0
    for log in "${AVATAR_LOG_FILES[@]}"; do
        if [ -f "$log" ]; then
            SIZE=$(du -h "$log" 2>/dev/null | cut -f1)
            SIZE_BYTES=$(stat -c%s "$log" 2>/dev/null || echo "0")
            TOTAL_SIZE=$((TOTAL_SIZE + SIZE_BYTES))
            echo "  $(basename "$log") ($SIZE)"
        fi
    done
    
    # Ask whether to clean
    echo ""
    read -p "Delete all avatar log files? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        DELETED_COUNT=0
        for log in "${AVATAR_LOG_FILES[@]}"; do
            if rm -f "$log" 2>/dev/null; then
                DELETED_COUNT=$((DELETED_COUNT + 1))
            fi
        done
        echo -e "${GREEN}Deleted ${DELETED_COUNT} avatar log file(s)${NC}"
    else
        echo "Avatar logs preserved"
    fi
else
    echo "No avatar log files found"
fi

echo ""
if [ "$REMAINING_COUNT" = "0" ]; then
    echo "Tip: View all avatars: curl ${API_URL}/avatar/list | python3 -m json.tool"
    echo ""
    exit 0
else
    exit 1
fi

