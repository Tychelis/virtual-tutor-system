#!/usr/bin/env python3
"""
Generate frontend config.js from ports_config.py
Usage: python scripts/generate_frontend_config.py
"""
import sys
import os

# Add parent directory to path to import ports_config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.ports_config import (
    BACKEND_PORT,
    LIVE_SERVER_PORT,
    AVATAR_BASE_PORT,
    TTS_PORT
)

config_template = """// API Configuration
// 🤖 Auto-generated from ports_config.py - DO NOT EDIT MANUALLY
// Run: python scripts/generate_frontend_config.py to regenerate

const config = {{
    get BACKEND_URL() {{
        const host = (typeof window !== 'undefined' && window.location) ? window.location.hostname : 'localhost';
        return `http://${{host}}:{backend_port}`;
    }},
    get LIPSYNC_MANAGER_URL() {{
        const host = (typeof window !== 'undefined' && window.location) ? window.location.hostname : 'localhost';
        return `http://${{host}}:{live_server_port}`;
    }},
    get WEBRTC_URL() {{
        const host = (typeof window !== 'undefined' && window.location) ? window.location.hostname : 'localhost';
        return `http://${{host}}:{avatar_base_port}`;
    }},
    get TTS_URL() {{
        const host = (typeof window !== 'undefined' && window.location) ? window.location.hostname : 'localhost';
        return `http://${{host}}:{tts_port}`;
    }}
}};

export default config;
"""

if __name__ == "__main__":
    config_content = config_template.format(
        backend_port=BACKEND_PORT,
        live_server_port=LIVE_SERVER_PORT,
        avatar_base_port=AVATAR_BASE_PORT,
        tts_port=TTS_PORT
    )
    
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "frontend",
        "src",
        "config.js"
    )
    
    with open(output_path, 'w') as f:
        f.write(config_content)
    
    print(f"✅ Generated {output_path}")
    print(f"   BACKEND_PORT: {BACKEND_PORT}")
    print(f"   LIVE_SERVER_PORT: {LIVE_SERVER_PORT}")
    print(f"   AVATAR_BASE_PORT: {AVATAR_BASE_PORT}")
    print(f"   TTS_PORT: {TTS_PORT}")
