from app import create_app
import logging
import traceback
import sys
import os

# 导入统一端口配置
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.ports_config import BACKEND_PORT

# Configure logging for error tracking
logging.basicConfig(
    filename='error.log',        # Log file path
    filemode='a',                 # Append mode
    level=logging.ERROR,          # Only log ERROR and above
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize Flask app
app = create_app()

def log_uncaught_exception(exc_type, exc_value, exc_traceback):
    """Custom handler to log all uncaught exceptions to error.log."""
    if issubclass(exc_type, KeyboardInterrupt):
        return  # Ignore Ctrl+C interruptions
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

# Set global exception hook
sys.excepthook = log_uncaught_exception

if __name__ == '__main__':
    # Run the Flask app in debug mode, listening on all interfaces
    # 优先使用环境变量，否则使用统一配置的端口
    port = int(os.getenv("PORT", BACKEND_PORT))
    print(f"Starting Flask on 0.0.0.0:{port} (debug=True)")
    app.run(debug=True, host="0.0.0.0", port=port)