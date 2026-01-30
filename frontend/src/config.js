// API Configuration
// 🤖 Auto-generated from ports_config.py - DO NOT EDIT MANUALLY
// Run: python scripts/generate_frontend_config.py to regenerate

const config = {
    get BACKEND_URL() {
        const host = (typeof window !== 'undefined' && window.location) ? window.location.hostname : 'localhost';
        return `http://${host}:8203`;
    },
    get LIPSYNC_MANAGER_URL() {
        const host = (typeof window !== 'undefined' && window.location) ? window.location.hostname : 'localhost';
        return `http://${host}:8606`;
    },
    get WEBRTC_URL() {
        const host = (typeof window !== 'undefined' && window.location) ? window.location.hostname : 'localhost';
        return `http://${host}:8615`;
    },
    get TTS_URL() {
        const host = (typeof window !== 'undefined' && window.location) ? window.location.hostname : 'localhost';
        return `http://${host}:8604`;
    }
};

export default config;
