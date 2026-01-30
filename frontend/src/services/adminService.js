import { http, errorHandler } from '../utils/request';

const API_ENDPOINTS = {
    USER_LIST: '/admin/users',
    USER_DETAIL: (userId) => `/admin/users/${userId}`,
    MODEL_LIST: '/admin/models',
    KNOWLEDGE_LIST: '/admin/knowledge',
    USER_LOGS: '/admin/user-action-logs',
    // Avatar endpoints
    AVATAR_LIST: '/avatar/list',
    AVATAR_ADD: '/avatar/add',
    AVATAR_DELETE: '/avatar/delete',
    AVATAR_START: '/avatar/start',
    AVATAR_PREVIEW: '/avatar/preview',
    TTS_MODELS: '/tts/models',
    // Chat avatar endpoints
    GET_AVATARS: '/avatar/get_avatars',
    // File management endpoints
    UPLOAD_FILE: '/upload',
    DELETE_FILE: (fileName) => `/upload/${fileName}`,
    FETCH_ALL_USERS: '/upload/users',
    FETCH_USER_FILES: '/user_files',
    FETCH_PUBLIC_FILES: '/public_files'
};

class AdminService {
    // 1. 獲取用戶列表
    async getUserList({ page = 1, limit = 20, search = '', role, status } = {}) {
        try {
            const params = { page, limit };
            if (search) params.search = search;
            if (role) params.role = role;
            if (status) params.status = status;
            const response = await http.get(API_ENDPOINTS.USER_LIST, { params });
            return { success: true, data: response, message: 'Successfully obtained user list' };
        } catch (error) {
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    // 2. 創建用戶
    async createUser(userData) {
        try {
            const response = await http.post(API_ENDPOINTS.USER_LIST, userData);
            return { success: true, data: response, message: 'User created successfully' };
        } catch (error) {
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    // 3. 編輯用戶
    async updateUser(userId, userData) {
        try {
            const response = await http.put(API_ENDPOINTS.USER_DETAIL(userId), userData);
            return { success: true, data: response, message: 'User update successful' };
        } catch (error) {
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    // 4. 刪除用戶
    async deleteUser(userId, reason = '') {
        try {
            const response = await http.delete(API_ENDPOINTS.USER_DETAIL(userId), { data: { reason } });
            return { success: true, data: response, message: 'User deleted successfully' };
        } catch (error) {
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    // 5. 查詢模型列表
    async getModelList({ page = 1, limit = 20 } = {}) {
        try {
            const params = { page, limit };
            const response = await http.get(API_ENDPOINTS.MODEL_LIST, { params });
            return { success: true, data: response, message: 'Successfully obtained the model list' };
        } catch (error) {
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    // 6. 查詢知識庫列表
    async getKnowledgeList({ page = 1, limit = 20 } = {}) {
        try {
            const params = { page, limit };
            const response = await http.get(API_ENDPOINTS.KNOWLEDGE_LIST, { params });
            return { success: true, data: response, message: 'Successfully obtained the knowledge base list' };
        } catch (error) {
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    // 7. 查詢用戶操作日誌 - 根据后端接口重写
    async getUserLogs(params = {}) {
        try {
            const { page = 1, per_page = 20, operator_email, target_user_email, action, search_id, search_info } = params;
            const apiParams = { page, per_page };

            console.log('getUserLogs called with params:', params); // 调试信息

            // 添加后端接口支持的参数
            if (operator_email) apiParams.operator_email = operator_email;
            if (target_user_email) apiParams.target_user_email = target_user_email;
            if (action) apiParams.action = action;

            // 处理前端搜索参数，转换为后端支持的参数
            if (search_id) {
                // 如果search_id是数字，可能是用户ID
                const searchIdNum = parseInt(search_id);
                if (!isNaN(searchIdNum)) {
                    // 后端接口中没有target_user_id参数，可能需要调整
                    console.log('Search ID is number:', searchIdNum);
                }
            }
            if (search_info) {
                // search_info可能是邮箱或操作类型
                if (search_info.includes('@')) {
                    // 如果包含@，可能是邮箱
                    apiParams.operator_email = search_info;
                } else {
                    // 否则可能是操作类型
                    apiParams.action = search_info;
                }
            }

            console.log('Final API params:', apiParams); // 调试信息
            console.log('API URL:', API_ENDPOINTS.USER_LOGS); // 调试API URL

            // 尝试直接构建URL参数
            const urlParams = new URLSearchParams();
            Object.keys(apiParams).forEach(key => {
                if (apiParams[key] !== undefined && apiParams[key] !== null) {
                    urlParams.append(key, apiParams[key]);
                }
            });
            const fullUrl = `${API_ENDPOINTS.USER_LOGS}?${urlParams.toString()}`;
            console.log('Full URL with params:', fullUrl); // 调试完整URL

            const response = await http.get(fullUrl);
            return { success: true, data: response, message: 'Successfully obtained user operation log' };
        } catch (error) {
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    // Avatar related methods
    // 8. 獲取Avatar列表
    async getAvatarList() {
        try {
            const response = await http.get(API_ENDPOINTS.AVATAR_LIST, {
                timeout: 30000 // 30秒超时
            });
            return { success: true, data: response, message: 'Successfully obtained Avatar list' };
        } catch (error) {
            console.error('Avatar list fetch error:', error);
            if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
                return {
                    success: false,
                    error: 'Request timeout',
                    message: 'Failed to fetch avatar list due to network timeout. Please try again.'
                };
            }
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    // 9. 創建Avatar
    async createAvatar(avatarData) {
        try {
            const formData = new FormData();

            // Add text fields - 确保字段名称与后端接口匹配，包括null值
            formData.append('name', avatarData.name || '');
            formData.append('avatar_blur', avatarData.avatar_blur !== undefined ? avatarData.avatar_blur : false);
            formData.append('support_clone', avatarData.support_clone !== undefined ? avatarData.support_clone : '');
            formData.append('timbre', avatarData.timbre || '');
            formData.append('ref_text', avatarData.ref_text || '');
            formData.append('tts_model', avatarData.tts_model || '');
            formData.append('avatar_model', avatarData.avatar_model || '');

            // Add files
            if (avatarData.prompt_face) {
                formData.append('prompt_face', avatarData.prompt_face);
            } else {
                // 如果prompt_face为空，发送一个空文件或标记
                formData.append('prompt_face', '');
            }
            if (avatarData.prompt_voice) {
                formData.append('prompt_voice', avatarData.prompt_voice);
            } else {
                // 如果prompt_voice为空，发送一个空文件或标记
                formData.append('prompt_voice', '');
            }

            console.log('Creating avatar with timeout of 15 minutes...');
            const response = await http.post(API_ENDPOINTS.AVATAR_ADD, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                timeout: 900000, // 15分钟超时
            });
            return { success: true, data: response, message: 'Avatar created successfully' };
        } catch (error) {
            console.error('Avatar creation error:', error);
            if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
                return {
                    success: false,
                    error: 'Request timeout',
                    message: 'Avatar creation is taking longer than expected. Please wait and check the status later.'
                };
            }
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    // 10. 刪除Avatar
    async deleteAvatar(avatarName) {
        try {
            const formData = new FormData();
            formData.append('name', avatarName);

            const response = await http.post(API_ENDPOINTS.AVATAR_DELETE, formData, {
                timeout: 30000 // 30秒超时
            });
            return { success: true, data: response, message: 'Avatar deleted successfully' };
        } catch (error) {
            console.error('Avatar delete error:', error);
            if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
                return {
                    success: false,
                    error: 'Request timeout',
                    message: 'Avatar deletion is taking longer than expected. Please try again.'
                };
            }
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    // 11. 啟動Avatar
    async startAvatar(avatarName) {
        try {
            const formData = new FormData();
            formData.append('avatar_name', avatarName);

            console.log('Starting avatar with timeout of 5 minutes...');
            const response = await http.post(API_ENDPOINTS.AVATAR_START, formData, {
                timeout: 300000, // 5分钟超时
            });
            return { success: true, data: response, message: 'Avatar startup successful' };
        } catch (error) {
            console.error('Avatar start error:', error);
            if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
                return {
                    success: false,
                    error: 'Request timeout',
                    message: 'Avatar start is taking longer than expected. Please wait and check the status later.'
                };
            }
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    // 11-1. 断开Avatar连接（减少连接计数）
    async disconnectAvatar() {
        try {
            const response = await http.post('/avatar/disconnect');
            return { success: true, data: response };
        } catch (error) {
            console.error('Avatar disconnect error:', error);
            return { success: false, error: errorHandler.handleApiError(error) };
        }
    }

    // 12. 獲取TTS模型列表
    async getTtsModels() {
        try {
            const response = await http.get(API_ENDPOINTS.TTS_MODELS, {
                timeout: 30000 // 30秒超时
            });
            return { success: true, data: response, message: 'Successfully obtained TTS model list' };
        } catch (error) {
            console.error('TTS models fetch error:', error);
            if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
                return {
                    success: false,
                    error: 'Request timeout',
                    message: 'Failed to fetch TTS models due to network timeout. Please try again.'
                };
            }
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    // 13. 獲取Avatar預覽
    async getAvatarPreview(avatarName) {
        try {
            const formData = new FormData();
            formData.append('avatar_name', avatarName);

            const response = await http.post(API_ENDPOINTS.AVATAR_PREVIEW, formData, {
                responseType: 'blob',
                timeout: 30000 // 30秒超时
            });
            return { success: true, data: response, message: 'Successfully obtained Avatar preview' };
        } catch (error) {
            console.error('Avatar preview fetch error:', error);
            if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
                return {
                    success: false,
                    error: 'Request timeout',
                    message: 'Failed to fetch avatar preview due to network timeout. Please try again.'
                };
            }
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    // 14. 獲取可用Avatar列表（用於聊天界面）
    async getAvailableAvatars() {
        try {
            const response = await http.get(API_ENDPOINTS.AVATAR_LIST, {
                timeout: 30000 // 30秒超时
            });
            return { success: true, data: response, message: 'Successfully obtained the list of available Avatars' };
        } catch (error) {
            console.error('Get available avatars error:', error);
            if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
                return {
                    success: false,
                    error: 'Request timeout',
                    message: 'Failed to fetch available avatars due to network timeout. Please try again.'
                };
            }
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    // 15. 上傳文件
    async uploadFile(file, additionalData = {}) {
        try {
            const formData = new FormData();
            formData.append('file', file);

            // 添加额外的表单数据
            Object.keys(additionalData).forEach(key => {
                formData.append(key, additionalData[key]);
            });

            const response = await http.post(API_ENDPOINTS.UPLOAD_FILE, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                timeout: 60000 // 60秒超时
            });
            return { success: true, data: response, message: 'File uploaded successfully' };
        } catch (error) {
            console.error('File upload error:', error);
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    // 16. 刪除文件
    async deleteFile(fileName) {
        try {
            const response = await http.delete(API_ENDPOINTS.DELETE_FILE(fileName), {
                timeout: 30000 // 30秒超时
            });
            return { success: true, data: response, message: 'File deleted successfully' };
        } catch (error) {
            console.error('File delete error:', error);
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    // 17. 獲取所有用戶（用於文件管理）
    async getAllUsers() {
        try {
            const response = await http.get(API_ENDPOINTS.FETCH_ALL_USERS, {
                timeout: 30000 // 30秒超时
            });
            return { success: true, data: response, message: 'Successfully obtained user list' };
        } catch (error) {
            console.error('Get all users error:', error);
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    // 18. 獲取用戶文件列表
    async getUserFiles() {
        try {
            const response = await http.get(API_ENDPOINTS.FETCH_USER_FILES, {
                timeout: 30000 // 30秒超时
            });
            return { success: true, data: response, message: 'Successfully obtained user file list' };
        } catch (error) {
            console.error('Get user files error:', error);
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    // 19. 獲取公共文件列表
    async getPublicFiles() {
        try {
            const response = await http.get(API_ENDPOINTS.FETCH_PUBLIC_FILES, {
                timeout: 30000 // 30秒超时
            });
            return { success: true, data: response, message: 'Successfully obtained the list of public files' };
        } catch (error) {
            console.error('Get public files error:', error);
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }
}

export default new AdminService(); 