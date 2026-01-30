import config from '../config';

const API_BASE_URL = `${config.BACKEND_URL}/api`;

const notificationService = {
    /**
     * 获取通知列表
     * @param {Object} params - 查询参数 { page, limit, is_read }
     * @returns {Promise<Object>} - { success, data: { notifications, total, unread_count } }
     */
    async getNotifications(params = {}) {
        const token = localStorage.getItem('token');
        if (!token) {
            return { success: false, message: 'No authentication token' };
        }

        const queryParams = new URLSearchParams();
        if (params.page) queryParams.append('page', params.page);
        if (params.limit) queryParams.append('limit', params.limit);
        if (params.is_read !== undefined) queryParams.append('is_read', params.is_read);

        try {
            const response = await fetch(`${API_BASE_URL}/user/notifications?${queryParams}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (response.ok) {
                return {
                    success: true,
                    data: data
                };
            } else {
                return {
                    success: false,
                    message: data.msg || data.message || 'Failed to fetch notifications'
                };
            }
        } catch (error) {
            console.error('Get notifications error:', error);
            return {
                success: false,
                message: error.message || 'Network error'
            };
        }
    },

    /**
     * 标记通知为已读
     * @param {number} notificationId - 通知ID
     * @returns {Promise<Object>} - { success, message }
     */
    async markAsRead(notificationId) {
        const token = localStorage.getItem('token');
        if (!token) {
            return { success: false, message: 'No authentication token' };
        }

        try {
            const response = await fetch(`${API_BASE_URL}/user/notifications/${notificationId}/read`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (response.ok) {
                return {
                    success: true,
                    message: data.msg || 'Notification marked as read'
                };
            } else {
                return {
                    success: false,
                    message: data.msg || data.message || 'Failed to mark notification as read'
                };
            }
        } catch (error) {
            console.error('Mark notification as read error:', error);
            return {
                success: false,
                message: error.message || 'Network error'
            };
        }
    },

    /**
     * 获取未读通知数量
     * @returns {Promise<Object>} - { success, count }
     */
    async getUnreadCount() {
        const result = await this.getNotifications({ page: 1, limit: 1 });
        if (result.success && result.data) {
            return {
                success: true,
                count: result.data.unread_count || 0
            };
        }
        return { success: false, count: 0 };
    }
};

export default notificationService;

