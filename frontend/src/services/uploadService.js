import { http, errorHandler } from '../utils/request';

const API_ENDPOINTS = {
    UPLOAD_FILE: '/upload/file',
    UPLOAD_IMAGE: '/upload/image',
    UPLOAD_DOCUMENT: '/upload',
    UPLOAD_AUDIO: '/upload/audio',
    DELETE_FILE: (fileName) => `/upload/${fileName}`
};

class UploadService {
    /**
     * General file upload method
     * @param {File} file - File to upload
     * @param {string} type - File type ('image', 'document', 'audio', 'file')
     * @param {Object} options - Extra options
     */
    async uploadFile(file, type = 'file', options = {}) {
        try {
            // Validate file
            if (!file) {
                throw new Error('Please select a file to upload');
            }

            // File size limit (default 10MB)
            const maxSize = options.maxSize || 10 * 1024 * 1024;
            if (file.size > maxSize) {
                throw new Error(`File size cannot exceed ${Math.round(maxSize / 1024 / 1024)}MB`);
            }

            // Create FormData
            const formData = new FormData();
            formData.append('file', file);

            // Add extra parameters
            if (options.sessionId) {
                formData.append('session_id', options.sessionId);
            }
            if (options.description) {
                formData.append('description', options.description);
            }

            // Debug FormData contents
            console.log('FormData contents:');
            for (let [key, value] of formData.entries()) {
                if (value instanceof File) {
                    console.log(`${key}:`, {
                        name: value.name,
                        size: value.size,
                        type: value.type,
                        lastModified: value.lastModified
                    });
                } else {
                    console.log(`${key}:`, value);
                }
            }

            // Choose the corresponding API endpoint
            let endpoint;
            switch (type) {
                case 'image':
                    endpoint = API_ENDPOINTS.UPLOAD_IMAGE;
                    break;
                case 'document':
                    endpoint = API_ENDPOINTS.UPLOAD_DOCUMENT;
                    break;
                case 'audio':
                    endpoint = API_ENDPOINTS.UPLOAD_AUDIO;
                    break;
                default:
                    endpoint = API_ENDPOINTS.UPLOAD_FILE;
            }

            console.log('Uploading file:', {
                name: file.name,
                size: file.size,
                type: file.type,
                endpoint: endpoint
            });

            const res = await http.post(endpoint, formData, {
                onUploadProgress: options.onProgress,
                timeout: 30000 // 30s timeout
            });

            console.log('Upload response:', res);

            return {
                success: true,
                data: res,
                message: 'File uploaded successfully',
                fileInfo: {
                    name: file.name,
                    size: file.size,
                    type: file.type,
                    uploadType: type
                }
            };
        } catch (error) {
            console.error('Upload error details:', error);

            // More detailed error handling
            let errorMessage = 'File upload failed';

            if (error.response) {
                // Server returned an error status code
                console.error('Server error response:', error.response.data);
                errorMessage = error.response.data?.msg || error.response.data?.message || `Server error: ${error.response.status}`;
            } else if (error.request) {
                // Request sent but no response received
                console.error('No response received:', error.request);
                errorMessage = 'No response from server. Please check your network connection.';
            } else {
                // Request configuration error
                console.error('Request setup error:', error.message);
                errorMessage = error.message;
            }

            return {
                success: false,
                error: error,
                message: errorMessage
            };
        }
    }

    /**
     * Upload image
     * @param {File} file - Image file
     * @param {Object} options - Options
     */
    async uploadImage(file, options = {}) {
        // Validate image type
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            return {
                success: false,
                message: 'Only JPG, PNG, GIF, and WebP image formats are supported'
            };
        }

        return this.uploadFile(file, 'image', { ...options, maxSize: 5 * 1024 * 1024 }); // 5MB limit
    }

    /**
     * Upload document
     * @param {File} file - Document file
     * @param {Object} options - Options
     */
    async uploadDocument(file, options = {}) {
        // Validate document type - consistent with backend
        const allowedTypes = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ];

        if (!allowedTypes.includes(file.type)) {
            return {
                success: false,
                message: 'Only PDF, Word (.doc/.docx), Excel (.xls/.xlsx), and TXT files are supported'
            };
        }

        return this.uploadFile(file, 'document', { ...options, maxSize: 20 * 1024 * 1024 }); // 20MB limit
    }

    /**
     * Upload audio
     * @param {File} file - Audio file
     * @param {Object} options - Options
     */
    async uploadAudio(file, options = {}) {
        // Validate audio type
        const allowedTypes = [
            'audio/mpeg',
            'audio/mp3',
            'audio/wav',
            'audio/ogg',
            'audio/m4a',
            'audio/aac'
        ];

        if (!allowedTypes.includes(file.type)) {
            return {
                success: false,
                message: 'Only MP3, WAV, OGG, M4A, and AAC audio formats are supported'
            };
        }

        return this.uploadFile(file, 'audio', { ...options, maxSize: 50 * 1024 * 1024 }); // 50MB limit
    }

    /**
     * Get file type
     * @param {File} file - File object
     * @returns {string} - File type ('image', 'document', 'audio', 'other')
     */
    getFileType(file) {
        const { type } = file;

        if (type.startsWith('image/')) {
            return 'image';
        }

        if (type.startsWith('audio/')) {
            return 'audio';
        }

        const documentTypes = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ];

        if (documentTypes.includes(type)) {
            return 'document';
        }

        return 'other';
    }

    /**
     * Format file size
     * @param {number} bytes - Number of bytes
     * @returns {string} - Formatted size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Delete file
     * @param {string} fileName - File name to delete
     */
    async deleteFile(fileName) {
        try {
            console.log('Deleting file:', fileName);

            const response = await http.delete(API_ENDPOINTS.DELETE_FILE(fileName));

            console.log('Delete response:', response);

            return {
                success: true,
                data: response,
                message: 'File deleted successfully'
            };
        } catch (error) {
            console.error('Delete file error:', error);

            return {
                success: false,
                error: errorHandler.handleApiError(error),
                message: errorHandler.showError(error)
            };
        }
    }
}

export default new UploadService();
