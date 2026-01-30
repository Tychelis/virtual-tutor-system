import { http, errorHandler } from '../utils/request';
import config from '../config';

// Use config.js for consistent port configuration
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || `${config.BACKEND_URL}/api`;

const API_ENDPOINTS = {
    CHAT: '/chat',
    CHAT_STREAM: '/chat/stream',
    CHAT_UPLOAD: '/chat/upload',
    CREATE_SESSION: '/chat/new',
    LIST_SESSIONS: '/chat/history',
    GET_MESSAGES: '/message/list',
    SET_FAVORITE: (chatId) => `/chat/${chatId}/favorite`,
    DELETE_SESSION: (chatId) => `/chat/${chatId}`,
    RECEIVE_SESSION_ID: '/sessionid'
};

class ChatService {
    /**
     * 发送聊天消息（支持文本、音频、图片、文档）
     * @param {FormData} formData - 包含 message/audio/image/document/session_id
     */
    async chat(formData) {
        try {
            const res = await http.post(API_ENDPOINTS.CHAT, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            return { success: true, data: res, message: 'Chat success' };
        } catch (error) {
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    /**
     * 上传文件
     * @param {FormData} formData - 包含 file/session_id
     */
    async uploadFile(formData) {
        try {
            const res = await http.post(API_ENDPOINTS.CHAT_UPLOAD, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            return { success: true, data: res, message: 'File uploaded successfully' };
        } catch (error) {
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    /**
     * 流式发送聊天消息
     * @param {FormData} formData - 包含 message/session_id
     * @param {Function} onChunk - 接收每个chunk的回调函数
     * @param {Function} onComplete - 完成时的回调
     * @param {Function} onError - 错误时的回调
     */
    async chatStream(formData, onChunk, onComplete, onError) {
        try {
            const token = localStorage.getItem('token');
            
            const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.CHAT_STREAM}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Accept': 'text/event-stream'
                    // Don't set Content-Type, let browser set it for FormData with boundary
                },
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullText = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            if (data.chunk) {
                                fullText += data.chunk;
                                if (onChunk) {
                                    onChunk(data.chunk, fullText);
                                }
                            }
                            
                            if (data.status === 'finished') {
                                if (onComplete) {
                                    onComplete(fullText);
                                }
                                return { success: true, data: { text_output: fullText }, message: 'Chat success' };
                            }
                        } catch (e) {
                            console.warn('Failed to parse SSE data:', line, e);
                        }
                    }
                }
            }

            if (onComplete) {
                onComplete(fullText);
            }
            return { success: true, data: { text_output: fullText }, message: 'Chat success' };

        } catch (error) {
            console.error('Stream chat error:', error);
            if (onError) {
                onError(error);
            }
            return { success: false, error: error.message, message: 'Chat failed' };
        }
    }

    /**
     * 创建新会话
     * @param {string} title
     */
    async createSession(title) {
        try {
            const res = await http.post(API_ENDPOINTS.CREATE_SESSION, { title });
            return { success: true, data: res, message: 'Session created' };
        } catch (error) {
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    /**
     * 获取会话历史
     */
    async listSessions() {
        try {
            const res = await http.get(API_ENDPOINTS.LIST_SESSIONS);
            return { success: true, data: res, message: 'Session list fetched' };
        } catch (error) {
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    /**
     * 获取会话消息
     * @param {string} session_id
     */
    async getMessages(session_id) {
        try {
            const res = await http.get(API_ENDPOINTS.GET_MESSAGES, { session_id });
            return { success: true, data: res, message: 'Messages fetched' };
        } catch (error) {
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    /**
     * 设置/取消会话收藏
     * @param {number} chatId
     * @param {boolean} is_favorite
     */
    async setSessionFavorite(chatId, is_favorite = true) {
        try {
            const res = await http.post(API_ENDPOINTS.SET_FAVORITE(chatId), { is_favorite });
            return { success: true, data: res, message: 'Favorite status updated' };
        } catch (error) {
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    /**
     * 删除会话
     * @param {number} chatId
     */
    async deleteSession(chatId) {
        try {
            const res = await http.delete(API_ENDPOINTS.DELETE_SESSION(chatId));
            return { success: true, data: res, message: 'Session deleted' };
        } catch (error) {
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }

    /**
     * 接收/保存 sessionid
     * @param {string|number} sessionid
     */
    async receiveSessionId(sessionid) {
        try {
            const res = await http.post(API_ENDPOINTS.RECEIVE_SESSION_ID, { sessionid });
            return { success: true, data: res, message: 'Session ID received' };
        } catch (error) {
            return { success: false, error: errorHandler.handleApiError(error), message: errorHandler.showError(error) };
        }
    }
}

export default new ChatService(); 