import axios from 'axios';
import config from '../config';

// Create axios instance
// Use config.js for consistent port configuration (auto-generated from ports_config.py)
const request = axios.create({
    baseURL: process.env.REACT_APP_API_BASE_URL || `${config.BACKEND_URL}/api`,
    timeout: 300000, // 5-minute default timeout, suitable for long-running Avatar operations
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor
request.interceptors.request.use(
    (config) => {
        // Get token from localStorage
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        // Add request timestamp
        config.headers['X-Request-Time'] = Date.now();

        // If it's FormData, make sure not to set Content-Type
        if (config.data instanceof FormData) {
            delete config.headers['Content-Type'];
            console.log('FormData request detected, removed Content-Type header');
        }

        console.log('Sending request:', {
            method: config.method?.toUpperCase(),
            url: config.url,
            params: config.params,
            headers: config.headers,
            dataType: config.data instanceof FormData ? 'FormData' : typeof config.data
        });

        return config;
    },
    (error) => {
        console.error('Request error:', error);
        return Promise.reject(error);
    }
);

// Response interceptor
request.interceptors.response.use(
    (response) => {
        console.log('Received response:', response.status, response.data);

        // If response contains new token, update localStorage
        if (response.data.token) {
            localStorage.setItem('token', response.data.token);
        }

        return response.data;
    },
    (error) => {
        console.error('Response error:', error);

        const { response } = error;

        if (response) {
            // Server returned error status code
            switch (response.status) {
                case 401:
                    console.error(response.data.msg);
                    // Token expired, clear local authentication info
                    auth.clearAuth();
                    // You can trigger global token expiration handling here
                    if (window.location.pathname !== '/login') {
                        alert('Your session has expired. Please login again.');
                        window.location.href = '/login';
                    }
                    break;
                case 403:
                    // Forbidden
                    console.error('No permission to access this resource');
                    break;
                case 404:
                    // Resource not found
                    console.error('Requested resource not found');
                    break;
                case 500:
                    // Internal server error
                    console.error('Internal server error');
                    break;
                default:
                    console.error(`Request failed: ${response.status}`);
            }

            // Return unified error format
            return Promise.reject({
                code: response.status,
                message: response.data.msg || 'Request failed',
                data: response.data
            });
        } else if (error.request) {
            // Request was sent but no response received
            console.error('Network error, please check network connection');
            return Promise.reject({
                code: 'NETWORK_ERROR',
                message: 'Network error, please check network connection',
                data: null
            });
        } else {
            // Request configuration error
            console.error('Request configuration error:', error.message);
            return Promise.reject({
                code: 'REQUEST_ERROR',
                message: error.message,
                data: null
            });
        }
    }
);

// Encapsulate common HTTP methods
export const http = {
    // GET request
    get: (url, params = {}, config = {}) => {
        return request.get(url, { params, ...config });
    },

    // POST request
    post: (url, data = {}, config = {}) => {
        // If it's FormData, remove Content-Type so the browser sets it automatically
        if (data instanceof FormData) {
            const newConfig = {
                ...config,
                headers: {
                    ...config.headers,
                    // Remove Content-Type; the browser will set multipart/form-data automatically
                }
            };
            // Explicitly remove Content-Type
            delete newConfig.headers['Content-Type'];

            console.log('Sending FormData request:', {
                url,
                headers: newConfig.headers,
                formDataKeys: [...data.keys()]
            });

            return request.post(url, data, newConfig);
        }
        return request.post(url, data, config);
    },

    // PUT request
    put: (url, data = {}, config = {}) => {
        return request.put(url, data, config);
    },

    // DELETE request
    delete: (url, config = {}) => {
        return request.delete(url, config);
    },

    // PATCH request
    patch: (url, data = {}, config = {}) => {
        return request.patch(url, data, config);
    },

    // File upload
    upload: (url, file, onProgress = null, config = {}) => {
        const formData = new FormData();
        formData.append('file', file);

        return request.post(url, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: onProgress,
            ...config,
        });
    },

    // Batch upload
    uploadMultiple: (url, files, onProgress = null, config = {}) => {
        const formData = new FormData();
        files.forEach((file, index) => {
            formData.append(`files[${index}]`, file);
        });

        return request.post(url, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: onProgress,
            ...config,
        });
    }
};

// Authentication related utility functions
export const auth = {
    // Set authentication information
    setAuth: (token, user) => {
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
    },

    // Get authentication information
    getAuth: () => {
        const token = localStorage.getItem('token');
        const user = localStorage.getItem('user');
        return {
            token,
            user: user ? JSON.parse(user) : null,
        };
    },

    // Clear authentication information
    clearAuth: () => {
        console.log('auth.clearAuth() called');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        console.log('auth.clearAuth() completed');
    },

    // Check if already logged in
    isAuthenticated: () => {
        return !!localStorage.getItem('token');
    },

    // Get user information
    getUser: () => {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    },

    // Update user information
    updateUser: (userData) => {
        const currentUser = auth.getUser();
        const updatedUser = { ...currentUser, ...userData };
        localStorage.setItem('user', JSON.stringify(updatedUser));
        return updatedUser;
    }
};

// Error handling utilities
export const errorHandler = {
    // Handle API errors
    handleApiError: (error) => {
        if (error.code === 'NETWORK_ERROR') {
            return 'Network connection failed, please check network settings';
        } else if (error.code === 'REQUEST_ERROR') {
            return 'Request configuration error';
        } else if (error.code === 401) {
            return error.data.msg;
        } else if (error.code === 403) {
            return 'No permission to perform this operation';
        } else if (error.code === 404) {
            return 'Requested resource not found';
        } else if (error.code === 500) {
            return 'Internal server error, please try again later';
        } else {
            return error.message || 'Unknown error';
        }
    },

    // Show error message
    showError: (error) => {
        const message = errorHandler.handleApiError(error);
        console.error('API error:', message);
        // Here you can integrate toast or other notification components
        return message;
    }
};

// Request status management
export const requestStatus = {
    IDLE: 'idle',
    LOADING: 'loading',
    SUCCESS: 'success',
    ERROR: 'error'
};

export default request; 