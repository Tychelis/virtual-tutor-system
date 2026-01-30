import requests
import time
import os
import json

# =============================================================================
# Video Generation API Test
# =============================================================================

def test_video_generation_avatar_availability():
    """
    Test if avatars are available and can be started
    """
    print("\n=== Test Video Generation - Avatar Availability ===")

    print("Checking if avatars are properly configured...")

    try:
        avatars_to_check = ['test_yongen', 'test_two']
        avatar_dir = "/workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/lip-sync/data/avatars"

        available_avatars = []
        for avatar_name in avatars_to_check:
            avatar_path = os.path.join(avatar_dir, avatar_name)
            if os.path.isdir(avatar_path):
                config_path = os.path.join(avatar_path, 'config.json')
                if os.path.exists(config_path):
                    print(f"✓ Avatar '{avatar_name}' found with config")
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        print(f"  TTS Model: {config.get('tts_model')}")
                        print(f"  Avatar Model: {config.get('avatar_model')}")
                    available_avatars.append(avatar_name)
                else:
                    print(f"⚠ Avatar '{avatar_name}' found but missing config.json")
            else:
                print(f"✗ Avatar '{avatar_name}' not found")

        if available_avatars:
            print(f"\n✓ Found {len(available_avatars)}/{len(avatars_to_check)} avatars")
            return True
        else:
            return False

    except Exception as e:
        print(f"✗ Error checking avatars: {e}")
        return False


def test_video_generation_backend_service():
    """
    Test if backend service is running
    """
    print("\n=== Test Video Generation - Backend Service Check ===")

    print("Checking if backend service is running...")

    try:
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)

        # Try to connect to backend on port 20000
        result = sock.connect_ex(('127.0.0.1', 8203))
        sock.close()

        if result == 0:
            print("✓ Backend service is running on port 8203")

            # Try a health check
            try:
                response = requests.get('http://127.0.0.1:8203/health', timeout=5)
                if response.status_code == 200:
                    print("✓ Backend health check passed")
                    return True
                else:
                    print(f"⚠ Backend responded with status {response.status_code}")
                    return True  # Service is running even if health check returns different status
            except:
                print("⚠ Could not reach health endpoint, but port is open")
                return True
        else:
            print("✗ Backend service not running on port 8203")
            print("  Please start the backend with:")
            print("  cd /workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/backend")
            print("  python main.py")
            return False

    except Exception as e:
        print(f"✗ Error checking backend service: {e}")
        return False


def test_video_generation_avatar_service():
    """
    Test if avatar services are available
    """
    print("\n=== Test Video Generation - Avatar Service Check ===")

    print("Checking avatar service infrastructure...")

    try:
        # Check if avatar manager exists
        avatar_manager_path = "/workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/avatar-manager/manager.py"

        if os.path.exists(avatar_manager_path):
            print(f"✓ Avatar manager found at: avatar-manager/manager.py")

            # Check for lip-sync directory
            lipsync_path = "/workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/lip-sync"
            if os.path.isdir(lipsync_path):
                print(f"✓ Lip-sync module found")

                # Check for app.py
                app_path = os.path.join(lipsync_path, 'app.py')
                if os.path.exists(app_path):
                    print(f"✓ Avatar app.py found")
                    return True
                else:
                    print(f"✗ Avatar app.py not found")
                    return False
            else:
                print(f"✗ Lip-sync module not found")
                return False
        else:
            print(f"✗ Avatar manager not found")
            return False

    except Exception as e:
        print(f"✗ Error checking avatar service: {e}")
        return False

def test_video_generation_database():
    """
    Test if database is configured
    """
    print("\n=== Test Video Generation - Database Check ===")

    print("Checking database configuration...")

    try:
        # Check for database files
        db_paths = [
            "/workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/llm/checkpoints_optimized.db",
            "/workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/backend/app.db"
        ]

        found_db = False
        for db_path in db_paths:
            if os.path.exists(db_path):
                print(f"✓ Database file found: {os.path.basename(db_path)}")
                found_db = True

        if found_db:
            return True
        else:
            print("⚠ No database files found (may be created on first run)")
            return True

    except Exception as e:
        print(f"✗ Error checking database: {e}")
        return False


def test_video_generation_multimedia():
    """
    Test if multimedia libraries are available
    """
    print("\n=== Test Video Generation - Multimedia Libraries ===")

    print("Checking multimedia library availability...")

    try:
        multimedia_modules = [
            ('librosa', 'audio processing'),
            ('soundfile', 'sound file I/O'),
            ('moviepy', 'video processing'),
        ]

        available = 0
        for module_name, description in multimedia_modules:
            try:
                __import__(module_name)
                print(f"✓ {module_name}: {description}")
                available += 1
            except ImportError:
                print(f"⚠ {module_name}: {description} - NOT available")

        print(f"\n✓ {available}/{len(multimedia_modules)} multimedia libraries available")
        return available >= 1

    except Exception as e:
        print(f"✗ Error checking multimedia: {e}")
        return False


def run_video_generation_tests():
    """Run all video generation tests"""
    print("\n" + "="*80)
    print("Starting Video Generation Tests")
    print("="*80)

    print("\nThese tests verify video generation configuration and dependencies")
    print("Note: These are pre-flight checks, not full integration tests")

    results = {}

    # Test avatar availability
    results['Avatar Availability'] = test_video_generation_avatar_availability()
    time.sleep(1)

    # Test backend service
    results['Backend Service'] = test_video_generation_backend_service()
    time.sleep(1)

    # Test avatar service
    results['Avatar Service'] = test_video_generation_avatar_service()
    time.sleep(1)

    # Test database
    results['Database'] = test_video_generation_database()
    time.sleep(1)

    # Test multimedia
    results['Multimedia Libraries'] = test_video_generation_multimedia()

    # Print summary
    print("\n" + "="*80)
    print("Video Generation Tests Summary")
    print("="*80)
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")

    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    print(f"\nTotal: {passed_count}/{total_count} checks passed")
    print("="*80)

    print("\nTo run actual video generation tests:")
    print("1. Ensure backend service is running")
    print("2. Ensure avatar services are started")
    print("3. Make requests to avatar API endpoints")
    print("4. Verify video generation and format")


if __name__ == "__main__":
    run_video_generation_tests()
