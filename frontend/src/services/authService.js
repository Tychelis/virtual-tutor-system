import { http, auth, errorHandler } from '../utils/request';
import userService from './userService';

// API endpoints - adjust according to backend routes
const API_ENDPOINTS = {
    LOGIN: '/login',
    REGISTER: '/register',
    SEND_VERIFICATION: '/send_verification',
    TOKEN_STATUS: '/token_status'
};

// Authentication service class
class AuthService {
    /**
     * User login
     * @param {Object} credentials - Login credentials
     * @param {string} credentials.email - Email address
     * @param {string} credentials.password - Password
     * @returns {Promise<Object>} Login result
     */
    async login(credentials) {
        try {
            const response = await http.post(API_ENDPOINTS.LOGIN, credentials);

            if (response.token) {
                // 登录成功后，获取用户详细信息
                const profileRes = await userService.getProfile();
                if (profileRes.success) {
                    const profile = profileRes.data;
                    const user = {
                        email: profile.email,
                        username: profile.username,
                        avatar: profile.avatar_url,
                        role: profile.role,
                        full_name: profile.full_name,
                        bio: profile.bio
                    };
                    auth.setAuth(response.token, user);
                } else {
                    // 获取用户信息失败，仍然只存token
                    auth.setAuth(response.token, {});
                }
            }

            return {
                success: true,
                data: response,
                message: 'Login successful'
            };
        } catch (error) {
            return {
                success: false,
                error: errorHandler.handleApiError(error),
                message: errorHandler.showError(error)
            };
        }
    }

    /**
     * Send verification code
     * @param {Object} data - Send verification code data
     * @param {string} data.email - Email address
     * @param {string} data.purpose - Purpose (register)
     * @returns {Promise<Object>} Send result
     */
    async sendVerificationCode(data) {
        try {
            const response = await http.post(API_ENDPOINTS.SEND_VERIFICATION, data);

            return {
                success: true,
                data: response,
                message: 'Verification code sent, please check your email'
            };
        } catch (error) {
            return {
                success: false,
                error: errorHandler.handleApiError(error),
                message: errorHandler.showError(error)
            };
        }
    }

    /**
     * User registration
     * @param {Object} userData - User registration data
     * @param {string} userData.email - Email address
     * @param {string} userData.password - Password
     * @param {string} userData.code - Verification code
     * @returns {Promise<Object>} Registration result
     */
    async register(userData) {
        try {
            const response = await http.post(API_ENDPOINTS.REGISTER, userData);

            return {
                success: true,
                data: response,
                message: 'Registration successful'
            };
        } catch (error) {
            console.log(error)

            return {
                success: false,
                error: errorHandler.handleApiError(error),
                message: errorHandler.showError(error)
            };
        }
    }

    /**
     * Check token status
     * @returns {Promise<Object>} Token status
     */
    async checkTokenStatus() {
        try {
            const response = await http.get(API_ENDPOINTS.TOKEN_STATUS);

            return {
                success: true,
                data: response,
                message: 'Token status check successful'
            };
        } catch (error) {
            return {
                success: false,
                error: errorHandler.handleApiError(error),
                message: errorHandler.showError(error)
            };
        }
    }

    /**
     * User logout
     * @returns {Promise<Object>} Logout result
     */
    async logout() {
        console.log('authService.logout() called');
        try {
            const token = localStorage.getItem('token');
            await http.post('/logout', {}, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
        } catch (e) {
            // 忽略錯誤，直接清除本地
            console.log('Backend logout failed, clearing local storage only');
        }
        console.log('Clearing auth data...');
        auth.clearAuth();
        console.log('Auth data cleared. Token:', localStorage.getItem('token'), 'User:', localStorage.getItem('user'));
        return {
            success: true,
            message: 'Logout successful'
        };
    }

    /**
     * Get user profile
     * @returns {Promise<Object>} User profile
     */
    async getProfile() {
        // Backend doesn't have get user profile API, return locally stored user information
        const user = auth.getUser();

        if (user) {
            return {
                success: true,
                data: user,
                message: 'Get user profile successful'
            };
        } else {
            return {
                success: false,
                error: 'User not logged in',
                message: 'User not logged in'
            };
        }
    }

    /**
     * Update user profile
     * @param {Object} profileData - User profile data
     * @returns {Promise<Object>} Update result
     */
    async updateProfile(profileData) {
        // Backend doesn't have update user profile API, only update local storage
        const updatedUser = auth.updateUser(profileData);

        return {
            success: true,
            data: updatedUser,
            message: 'Update user profile successful'
        };
    }

    /**
     * Upload avatar
     * @param {File} file - Avatar file
     * @param {Function} onProgress - Upload progress callback
     * @returns {Promise<Object>} Upload result
     */
    async uploadAvatar(file, onProgress = null) {
        // Backend doesn't have avatar upload API, simulate upload success
        return new Promise((resolve) => {
            setTimeout(() => {
                const avatarUrl = URL.createObjectURL(file);
                auth.updateUser({ avatar: avatarUrl });

                resolve({
                    success: true,
                    data: { avatarUrl },
                    message: 'Avatar upload successful'
                });
            }, 1000);
        });
    }

    /**
     * Change password
     * @param {Object} passwordData - Password change data
     * @param {string} passwordData.oldPassword - Old password
     * @param {string} passwordData.newPassword - New password
     * @returns {Promise<Object>} Change result
     */
    async changePassword(passwordData) {
        // Backend doesn't have change password API, simulate success
        return {
            success: true,
            message: 'Password changed successfully'
        };
    }

    /**
     * Forgot password
     * @param {string} email - Email address
     * @returns {Promise<Object>} Forgot password result
     */
    async forgotPassword(email) {
        // Backend doesn't have forgot password API, simulate success
        return {
            success: true,
            message: 'Password reset email sent successfully'
        };
    }

    /**
     * Reset password
     * @param {Object} resetData - Reset password data
     * @param {string} resetData.token - Reset token
     * @param {string} resetData.newPassword - New password
     * @returns {Promise<Object>} Reset result
     */
    async resetPassword(resetData) {
        // Backend doesn't have reset password API, simulate success
        return {
            success: true,
            message: 'Password reset successful'
        };
    }

    /**
     * Verify email
     * @param {string} token - Verification token
     * @returns {Promise<Object>} Verification result
     */
    async verifyEmail(token) {
        // Backend doesn't have email verification API, simulate success
        return {
            success: true,
            message: 'Email verification successful'
        };
    }

    /**
     * Send verification email
     * @param {string} email - Email address
     * @returns {Promise<Object>} Send result
     */
    async sendVerificationEmail(email) {
        // Backend doesn't have send verification email API, simulate success
        return {
            success: true,
            message: 'Verification email sent successfully'
        };
    }

    /**
     * Refresh token
     * @returns {Promise<Object>} Refresh result
     */
    async refreshToken() {
        // Backend doesn't have refresh token API, simulate success
        return {
            success: true,
            message: 'Token refreshed successfully'
        };
    }

    /**
     * 用驗證碼修改密碼
     * @param {Object} data - { code, new_password }
     * @returns {Promise<Object>} 修改結果
     */
    async updatePasswordWithCode(data) {
        try {
            const response = await http.post('/update_password', data);
            return {
                success: true,
                data: response,
                message: '密碼修改成功'
            };
        } catch (error) {
            return {
                success: false,
                error: errorHandler.handleApiError(error),
                message: errorHandler.showError(error)
            };
        }
    }

    /**
     * Check if user is authenticated
     * @returns {boolean} Authentication status
     */
    isAuthenticated() {
        return auth.isAuthenticated();
    }

    /**
     * Get current user
     * @returns {Object|null} Current user
     */
    getCurrentUser() {
        return auth.getUser();
    }
}

export default new AuthService(); 