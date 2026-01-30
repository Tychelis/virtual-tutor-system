#!/usr/bin/env python3
"""Avatar Manager Test Script"""

import requests
import time
import json
from typing import Dict

BASE_URL = "http://localhost:8607"


def test_health():
    """Test health check"""
    print("\n" + "="*70)
    print("Test 1: API Health Check")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f" API healthy: {data['service']} v{data['version']}")
            return True
        else:
            print(f" API response error: {response.status_code}")
            return False
    except Exception as e:
        print(f" API unreachable: {e}")
        print("\nPlease start Avatar Manager API first:")
        print("  cd avatar-manager && python api.py")
        return False


def test_start_avatar(avatar_id: str):
    """Test starting Avatar"""
    print(f"\nStarting Avatar: {avatar_id}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/avatar/start",
            json={'avatar_id': avatar_id},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                info = data['data']
                print(f" Started successfully:")
                print(f"   PID: {info['pid']}")
                print(f"   Port: {info['port']}")
                print(f"   GPU: {info['gpu']}")
                print(f"   WebRTC: {info['webrtc_url']}")
                return info
        else:
            error = response.json()
            print(f" Start failed: {error.get('message')}")
            return None
            
    except Exception as e:
        print(f" Request failed: {e}")
        return None


def test_list_avatars():
    """Test listing Avatars"""
    print("\n" + "="*70)
    print("Currently Running Avatars:")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/avatar/list", timeout=5)
        if response.status_code == 200:
            data = response.json()
            avatars = data['data']
            
            if not avatars:
                print("  (No running Avatars)")
            else:
                for avatar in avatars:
                    print(f"  • {avatar['avatar_id']}")
                    print(f"    - Port: {avatar['port']}")
                    print(f"    - GPU: {avatar['gpu']}")
                    print(f"    - Uptime: {avatar['uptime_seconds']:.0f}s")
            
            return avatars
        else:
            print(f" Request failed: {response.status_code}")
            return []
            
    except Exception as e:
        print(f" Request failed: {e}")
        return []


def test_get_status():
    """Test getting status"""
    print("\n" + "="*70)
    print("System Status:")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()['data']
            
            # Manager status
            manager = data['manager']
            print(f"\nAvatar Manager:")
            print(f"  Running: {manager['running']}/{manager['max']}")
            print(f"  Available: {manager['available']}")
            print(f"  GPU Distribution: {manager['gpu_distribution']}")
            
            # GPU status
            gpus = data['gpu']
            if gpus:
                print(f"\nGPU Status:")
                for gpu in gpus:
                    print(f"  GPU {gpu['gpu_id']}: {gpu['name']}")
                    mem = gpu['memory']
                    print(f"    Memory: {mem['used_gb']:.1f}GB / {mem['total_gb']:.1f}GB ({mem['usage_percent']:.1f}%)")
                    if gpu['temperature_celsius']:
                        print(f"    Temperature: {gpu['temperature_celsius']}°C")
            
            return data
        else:
            print(f" Request failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f" Request failed: {e}")
        return None


def test_stop_avatar(avatar_id: str):
    """Test stopping Avatar"""
    print(f"\nStopping Avatar: {avatar_id}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/avatar/stop",
            json={'avatar_id': avatar_id},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f" Stopped successfully")
            return True
        else:
            error = response.json()
            print(f" Stop failed: {error.get('message')}")
            return False
            
    except Exception as e:
        print(f" Request failed: {e}")
        return False


def get_available_avatars():
    """Get list of available avatars"""
    import os
    avatar_dir = "/workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/lip-sync/data/avatars"
    
    if not os.path.exists(avatar_dir):
        return []
    
    avatars = []
    for item in os.listdir(avatar_dir):
        item_path = os.path.join(avatar_dir, item)
        if os.path.isdir(item_path):
            avatars.append(item)
    
    return avatars


def run_basic_test():
    """Run basic tests"""
    print("\n" + "="*70)
    print(" Avatar Manager Basic Function Test")
    print("="*70)
    
    # 1. Health check
    if not test_health():
        return
    
    # 1.5. Find available avatars
    available_avatars = get_available_avatars()
    if not available_avatars:
        print("\n No available avatars found")
        print("   Please ensure there are avatar files in lip-sync/data/avatars/ directory")
        return
    
    print(f"\n Found {len(available_avatars)} available avatar(s):")
    for avatar in available_avatars[:5]:  # Show only first 5
        print(f"   - {avatar}")
    if len(available_avatars) > 5:
        print(f"   ... and {len(available_avatars) - 5} more")
    
    # Use the first available avatar for testing
    test_avatar_id = available_avatars[0]
    
    # 2. Start 1 Avatar
    print("\n" + "="*70)
    print(f"Test 2: Start Avatar ({test_avatar_id})")
    print("="*70)
    
    avatar1 = test_start_avatar(test_avatar_id)
    if not avatar1:
        print(f" Failed to start {test_avatar_id}")
        return
    
    time.sleep(2)
    
    # 3. 列出Avatar
    test_list_avatars()
    
    # 4. 获取状态
    test_get_status()
    
    # 5. Stop Avatar
    print("\n" + "="*70)
    print("Test 3: Stop Avatar")
    print("="*70)
    test_stop_avatar(test_avatar_id)
    
    time.sleep(2)
    
    # 6. List again
    test_list_avatars()
    
    print("\n" + "="*70)
    print(" Basic Test Completed")
    print("="*70)


def run_concurrent_test():
    """Run concurrent test"""
    print("\n" + "="*70)
    print(" Avatar Manager Concurrent Test")
    print("="*70)
    
    if not test_health():
        return
    
    # Get available avatars
    available_avatars = get_available_avatars()
    if not available_avatars:
        print("\n No available avatars found")
        return
    
    # Use first 3 available avatars (if available)
    avatar_ids = available_avatars[:3]
    print(f"\n Using {len(avatar_ids)} avatar(s) for concurrent test:")
    for avatar_id in avatar_ids:
        print(f"   - {avatar_id}")
    
    print(f"\nStarting {len(avatar_ids)} Avatar(s)...")
    started = []
    
    for avatar_id in avatar_ids:
        info = test_start_avatar(avatar_id)
        if info:
            started.append(avatar_id)
        time.sleep(1)
    
    print(f"\nSuccessfully started {len(started)}/{len(avatar_ids)} Avatar(s)")
    
    # Check status
    time.sleep(2)
    test_list_avatars()
    test_get_status()
    
    # Cleanup
    print("\nCleaning up test Avatars...")
    for avatar_id in started:
        test_stop_avatar(avatar_id)
        time.sleep(1)
    
    print("\n Concurrent Test Completed")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "health":
            test_health()
        elif command == "list":
            test_list_avatars()
        elif command == "status":
            test_get_status()
        elif command == "start" and len(sys.argv) > 2:
            test_start_avatar(sys.argv[2])
        elif command == "stop" and len(sys.argv) > 2:
            test_stop_avatar(sys.argv[2])
        elif command == "concurrent":
            run_concurrent_test()
        else:
            print("Usage:")
            print("  python test_manager.py              # Run basic test")
            print("  python test_manager.py concurrent   # Run concurrent test")
            print("  python test_manager.py health       # Health check")
            print("  python test_manager.py list         # List Avatars")
            print("  python test_manager.py status       # System status")
            print("  python test_manager.py start <id>   # Start Avatar")
            print("  python test_manager.py stop <id>    # Stop Avatar")
    else:
        run_basic_test()

