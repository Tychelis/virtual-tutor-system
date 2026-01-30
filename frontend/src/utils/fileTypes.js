// File type configuration
export const FILE_TYPES = {
    // Image file types
    IMAGE: {
        accept: '.jpg,.jpeg,.png,.gif,.webp',
        mimeTypes: ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'],
        maxSize: 5 * 1024 * 1024, // 5MB
        description: 'JPG, PNG, GIF, WebP formats, max 5MB'
    },

    // Video file types (MP4)
    VIDEO: {
        accept: '.mp4',
        mimeTypes: ['video/mp4'],
        maxSize: 100 * 1024 * 1024, // 100MB
        description: 'MP4 format, max 100MB'
    },

    // Audio file types (WAV)
    AUDIO: {
        accept: '.wav',
        mimeTypes: ['audio/wav'],
        maxSize: 50 * 1024 * 1024, // 50MB
        description: 'WAV format, max 50MB'
    }
};

// File validation function
export const validateFile = (file, fileType) => {
    const config = FILE_TYPES[fileType];
    if (!config) {
        throw new Error(`Unknown file type: ${fileType}`);
    }

    // Validate file type
    if (!config.mimeTypes.includes(file.type)) {
        const supportedFormats = config.accept.replace(/\./g, '').toUpperCase().split(',');
        throw new Error(`Please select a valid ${fileType.toLowerCase()} file (${supportedFormats.join(', ')})`);
    }

    // Validate file size
    if (file.size > config.maxSize) {
        const maxSizeMB = config.maxSize / 1024 / 1024;
        const currentSizeMB = (file.size / 1024 / 1024).toFixed(2);
        throw new Error(`${fileType} file size cannot exceed ${maxSizeMB}MB. Current size: ${currentSizeMB}MB`);
    }

    return true;
};

// Format file size
export const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}; 