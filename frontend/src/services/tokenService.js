import { http } from '../utils/request';

class TokenService {
    constructor() {
        this.checkInterval = null;
        this.warningThreshold = 5 * 60; // 5-minute warning threshold
        this.expiredThreshold = 0; // 0-second expired threshold
    }

    /**
     * Check token status
     * @returns {Promise<Object>} Token status info
     */
    async checkTokenStatus() {
        try {
            const response = await http.get('/token_status');
            return {
                success: true,
                data: response,
                expiresInSeconds: response.expires_in_seconds,
                expiresInMinutes: response.expires_in_minutes
            };
        } catch (error) {
            return {
                success: false,
                error: error,
                message: 'Failed to check token status'
            };
        }
    }

    /**
     * Start periodic token status checks
     * @param {Function} onTokenExpired - Callback when token expires
     * @param {Function} onTokenWarning - Callback when token is about to expire
     */
    startTokenMonitoring(onTokenExpired, onTokenWarning) {
        // Clear any previous interval
        this.stopTokenMonitoring();

        // Check token status every 30 seconds
        this.checkInterval = setInterval(async () => {
            const result = await this.checkTokenStatus();

            if (!result.success) {
                // If the check fails, the token may have expired
                if (onTokenExpired) {
                    onTokenExpired('Token check failed');
                }
                return;
            }

            const { expiresInSeconds, expiresInMinutes } = result;

            // Check if expired
            if (expiresInSeconds <= this.expiredThreshold) {
                if (onTokenExpired) {
                    onTokenExpired(`Token expired. Please login again.`);
                }
                return;
            }

            // Check if about to expire (within 5 minutes)
            if (expiresInSeconds <= this.warningThreshold) {
                if (onTokenWarning) {
                    onTokenWarning(`Your session will expire in ${Math.ceil(expiresInMinutes)} minutes. Please save your work.`);
                }
            }
        }, 30000); // Check every 30 seconds
    }

    /**
     * Stop token status monitoring
     */
    stopTokenMonitoring() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
    }

    /**
     * Check if token is expiring soon
     * @returns {Promise<boolean>} Whether the token is expiring soon
     */
    async isTokenExpiringSoon() {
        const result = await this.checkTokenStatus();
        if (!result.success) {
            return true; // If the check fails, assume it is expiring soon
        }
        return result.expiresInSeconds <= this.warningThreshold;
    }

    /**
     * Check if token is expired
     * @returns {Promise<boolean>} Whether the token is expired
     */
    async isTokenExpired() {
        const result = await this.checkTokenStatus();
        if (!result.success) {
            return true; // If the check fails, assume it is expired
        }
        return result.expiresInSeconds <= this.expiredThreshold;
    }

    /**
     * Get token remaining time (seconds)
     * @returns {Promise<number>} Remaining seconds
     */
    async getTokenRemainingTime() {
        const result = await this.checkTokenStatus();
        if (!result.success) {
            return 0;
        }
        return result.expiresInSeconds;
    }
}

export default new TokenService(); 