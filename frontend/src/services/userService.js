import { http, errorHandler } from '../utils/request';

const API_ENDPOINTS = {
    PROFILE: '/user/profile',
    AVATAR: '/user/avatar',
    NOTIFICATIONS: '/user/notifications',
    MARK_NOTIFICATION_READ: (id) => `/user/notifications/${id}/read`
};

class UserService {
    /**
     * Get user profile
     * @returns {Promise<Object>} User profile
     */
    async getProfile() {
        try {
            const profile = await http.get(API_ENDPOINTS.PROFILE);
            return {
                success: true,
                data: profile,
                message: 'Get user profile successful'
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
     * Update user profile
     * @param {Object} data User info
     */
    async updateProfile(data) {
        try {
            const res = await http.post(API_ENDPOINTS.PROFILE, data);
            return {
                success: true,
                message: res.msg || 'User profile updated successfully'
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
     * Upload avatar
     * @param {File} file Avatar file
     */
    async uploadAvatar(file) {
        try {
            const formData = new FormData();
            formData.append('avatar', file);
            const res = await http.post(API_ENDPOINTS.AVATAR, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            return {
                success: true,
                avatar_url: res.avatar_url,
                message: res.msg || 'Avatar uploaded successfully.'
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
     * Get notifications
     * @param {Object} params { page, limit, unread_only }
     */
    async getNotifications(params = {}) {
        try {
            const res = await http.get(API_ENDPOINTS.NOTIFICATIONS, params);
            return {
                success: true,
                data: res,
                message: 'Get notifications successful'
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
     * Mark notification as read
     * @param {number} notificationId Notification ID
     */
    async markNotificationRead(notificationId) {
        try {
            const res = await http.put(API_ENDPOINTS.MARK_NOTIFICATION_READ(notificationId));
            return {
                success: true,
                message: res.msg || 'Notification marked as read'
            };
        } catch (error) {
            return {
                success: false,
                error: errorHandler.handleApiError(error),
                message: errorHandler.showError(error)
            };
        }
    }
}

export default new UserService(); 