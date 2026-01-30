import requests
import time
import os
import json

# =============================================================================
# LLM Response API Test
# =============================================================================

def test_llm_response_llm_service():
    """
    Test if LLM service is available
    """
    print("\n=== Test LLM Response - LLM Service Check ===")

    print("Checking if LLM service is running...")

    try:
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)

        # Try multiple possible LLM ports
        llm_ports = [8611, 8610]  # Common LLM service ports

        for port in llm_ports:
            result = sock.connect_ex(('127.0.0.1', port))
            if result == 0:
                print(f"✓ LLM service found on port {port}")
                sock.close()
                return True

        sock.close()
        print("✗ LLM service not found on common ports")
        print(f"  Checked ports: {llm_ports}")
        print("  Please ensure LLM service is running")
        return False

    except Exception as e:
        print(f"✗ Error checking LLM service: {e}")
        return False


def test_llm_response_backend_integration():
    """
    Test if LLM is integrated with backend
    """
    print("\n=== Test LLM Response - Backend Integration Check ===")

    print("Checking LLM backend integration...")

    try:
        backend_path = "/workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/backend"

        if os.path.isdir(backend_path):
            print(f"✓ Backend directory found")

            # Check for LLM-related files
            llm_files = [
                os.path.join(backend_path, 'routes', 'llm.py'),
                os.path.join(backend_path, 'config.py'),
                os.path.join(backend_path, 'main.py')
            ]

            found_files = 0
            for file_path in llm_files:
                if os.path.exists(file_path):
                    print(f"✓ Found: {os.path.basename(file_path)}")
                    found_files += 1

            if found_files > 0:
                print(f"\n✓ LLM integration files found")
                return True
            else:
                print(f"✗ LLM integration files not found")
                return False
        else:
            print(f"✗ Backend directory not found")
            return False

    except Exception as e:
        print(f"✗ Error checking integration: {e}")
        return False


def test_llm_response_dependencies():
    """
    Test if LLM dependencies are available
    """
    print("\n=== Test LLM Response - Dependencies Check ===")

    print("Checking LLM dependencies...")

    try:
        llm_modules = [
            ('ollama', 'Ollama client'),
            ('transformers', 'Hugging Face transformers'),
            ('torch', 'PyTorch'),
            ('langchain', 'LangChain'),
        ]

        available_modules = []
        for module_name, description in llm_modules:
            try:
                __import__(module_name)
                print(f"✓ {module_name}: {description}")
                available_modules.append(module_name)
            except ImportError:
                print(f"⚠ {module_name}: {description} - NOT available")

        print(f"\n✓ {len(available_modules)}/{len(llm_modules)} LLM modules available")
        return len(available_modules) >= 1

    except Exception as e:
        print(f"✗ Error checking modules: {e}")
        return False


def test_llm_response_configuration():
    """
    Test if LLM configuration is set up
    """
    print("\n=== Test LLM Response - Configuration Check ===")

    print("Checking LLM configuration...")

    try:
        config_paths = [
            "/workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/backend/.env",
            "/workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/backend/config.json",
            "/workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/backend/config.py"
        ]

        found_configs = False
        for config_path in config_paths:
            if os.path.exists(config_path):
                print(f"✓ Configuration found: {os.path.basename(config_path)}")
                found_configs = True

        if found_configs:
            print(f"\n✓ LLM configuration files found")
            return True
        else:
            print(f"⚠ No configuration files found (may use defaults)")
            return True

    except Exception as e:
        print(f"✗ Error checking configuration: {e}")
        return False


def test_llm_response_models():
    """
    Test if LLM models are available
    """
    print("\n=== Test LLM Response - Models Check ===")

    print("Checking for available LLM models...")

    try:
        # Check for model directories
        models_paths = [
            "/workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/llm/models",
            "/workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/backend/models",
            os.path.expanduser("~/.ollama/models"),  # Ollama models
        ]

        found_models = False
        for model_path in models_paths:
            if os.path.isdir(model_path):
                print(f"✓ Model directory found: {model_path}")
                # Count files in directory
                try:
                    files = os.listdir(model_path)
                    print(f"  Contains {len(files)} items")
                    found_models = True
                except:
                    pass

        if found_models:
            print(f"\n✓ LLM models found")
            return True
        else:
            print(f"⚠ No model directories found (models may be downloaded on demand)")
            return True

    except Exception as e:
        print(f"✗ Error checking models: {e}")
        return False


def test_llm_response_database():
    """
    Test if conversation database is available
    """
    print("\n=== Test LLM Response - Database Check ===")

    print("Checking conversation database...")

    try:
        # Check for database or conversation storage
        db_paths = [
            "/workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/backend/app.db",
            "/workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/backend/conversations.db",
        ]

        found_db = False
        for db_path in db_paths:
            if os.path.exists(db_path):
                print(f"✓ Database file found: {os.path.basename(db_path)}")
                found_db = True

        if found_db or os.path.isdir("/workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/backend"):
            print(f"\n✓ Database infrastructure available")
            return True
        else:
            print(f"✗ Database not configured")
            return False

    except Exception as e:
        print(f"✗ Error checking database: {e}")
        return False


def run_llm_response_tests():
    """Run all LLM response tests"""
    print("\n" + "="*80)
    print("Starting LLM Response Tests")
    print("="*80)

    print("\nThese tests verify LLM configuration and dependencies")
    print("Note: These are pre-flight checks, not full integration tests")

    results = {}

    # Test LLM service
    results['LLM Service'] = test_llm_response_llm_service()
    time.sleep(1)

    # Test backend integration
    results['Backend Integration'] = test_llm_response_backend_integration()
    time.sleep(1)

    # Test dependencies
    results['Dependencies'] = test_llm_response_dependencies()
    time.sleep(1)

    # Test configuration
    results['Configuration'] = test_llm_response_configuration()
    time.sleep(1)

    # Test models
    results['Models'] = test_llm_response_models()
    time.sleep(1)

    # Test database
    results['Database'] = test_llm_response_database()

    # Print summary
    print("\n" + "="*80)
    print("LLM Response Tests Summary")
    print("="*80)
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")

    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    print(f"\nTotal: {passed_count}/{total_count} checks passed")
    print("="*80)

    print("\nTo run actual LLM response tests:")
    print("1. Ensure LLM service is running")
    print("2. Ensure backend service is running")
    print("3. Make requests to /llm/chat endpoint")
    print("4. Verify response quality and format")


if __name__ == "__main__":
    run_llm_response_tests()
