import React, { useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import uploadService from '../../services/uploadService';
import adminService from '../../services/adminService';
import config from '../../config';

// 允许的文档类型 - 与后端保持一致
const ALLOWED_DOCUMENT_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
];

// 添加旋转动画样式
const spinKeyframes = `
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
@keyframes fadeIn {
    0% { opacity: 0; }
    100% { opacity: 1; }
}
@keyframes slideUp {
    0% { 
        opacity: 0;
        transform: translateY(20px);
    }
    100% { 
        opacity: 1;
        transform: translateY(0);
    }
}
`;

// 将样式注入到页面中
if (typeof document !== 'undefined') {
    const styleElement = document.createElement('style');
    styleElement.textContent = spinKeyframes;
    if (!document.head.querySelector('style[data-spin-animation]')) {
        styleElement.setAttribute('data-spin-animation', 'true');
        document.head.appendChild(styleElement);
    }
}

// 现代化图标组件
const PaperPlaneIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 2L11 13" />
        <path d="M22 2L15 22L11 13L2 9L22 2Z" />
    </svg>
);

const FileIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14,2 14,8 20,8" />
    </svg>
);

const MicIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
        <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
        <line x1="12" y1="19" x2="12" y2="23" />
        <line x1="8" y1="23" x2="16" y2="23" />
    </svg>
);

const PlusIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <line x1="12" y1="5" x2="12" y2="19" />
        <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
);

const FolderIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    </svg>
);

const DeleteIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="3,6 5,6 21,6"></polyline>
        <path d="M19,6v14a2,2 0 0,1 -2,2H7a2,2 0 0,1 -2,-2V6m3,0V4a2,2 0 0,1 2,-2h4a2,2 0 0,1 2,2v2"></path>
    </svg>
);

function HomeFooter({ onSendMessage, onSendFile, onNewChat, themeStyles }) {
    const isDarkMode = themeStyles?.isDarkMode || false;
    const [input, setInput] = useState("");
    const [listening, setListening] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [isTyping, setIsTyping] = useState(false);
    const [isFocused, setIsFocused] = useState(false);

    const [showUserFiles, setShowUserFiles] = useState(false);
    const [userFiles, setUserFiles] = useState([]);
    const [loadingUserFiles, setLoadingUserFiles] = useState(false);
    const [deletingFiles, setDeletingFiles] = useState(new Set());

    const fileInputRef = useRef();
    const recognitionRef = useRef(null);
    const typingTimeoutRef = useRef();

    // 获取用户已上传文件
    const fetchUserFiles = async () => {
        setLoadingUserFiles(true);
        try {
            const result = await adminService.getUserFiles();
            if (result.success && result.data && result.data.files) {
                setUserFiles(result.data.files);
            } else {
                setUserFiles([]);
            }
        } catch (error) {
            console.error('Failed to fetch user files:', error);
            setUserFiles([]);
        } finally {
            setLoadingUserFiles(false);
        }
    };

    // Delete file
    const handleDeleteFile = async (fileName) => {
        if (!window.confirm(`Are you sure you want to delete "${fileName}"?`)) {
            return;
        }

        setDeletingFiles(prev => new Set(prev).add(fileName));

        try {
            const result = await uploadService.deleteFile(fileName);
            if (result.success) {
                await fetchUserFiles();
                console.log('File deleted successfully:', fileName);
            } else {
                console.error('Failed to delete file:', result.message);
                alert(`Delete failed: ${result.message}`);
            }
        } catch (error) {
            console.error('Error deleting file:', error);
            alert('An error occurred while deleting the file');
        } finally {
            setDeletingFiles(prev => {
                const newSet = new Set(prev);
                newSet.delete(fileName);
                return newSet;
            });
        }
    };

    // 处理显示用户文件
    const handleShowUserFiles = () => {
        if (!showUserFiles) {
            fetchUserFiles();
        }
        setShowUserFiles(!showUserFiles);
    };

    // 發送文字
    const handleSend = () => {
        if (input.trim()) {
            onSendMessage(input);
            setInput("");
            setIsTyping(false);
        }
    };

    // 處理輸入變化
    const handleInputChange = (e) => {
        setInput(e.target.value);
        setIsTyping(true);
        
        // 清除之前的定时器
        if (typingTimeoutRef.current) {
            clearTimeout(typingTimeoutRef.current);
        }
        
        // 设置新的定时器，2秒后取消"正在输入"状态
        typingTimeoutRef.current = setTimeout(() => {
            setIsTyping(false);
        }, 2000);
    };

    // 發送文件
    const handleFileClick = () => {
        if (uploading) return;
        fileInputRef.current && fileInputRef.current.click();
    };

    // File upload logic
    const handleFileUpload = async (file) => {
        if (!ALLOWED_DOCUMENT_TYPES.includes(file.type)) {
            alert(`Only the following document types are supported: PDF, Word, Excel, TXT`);
            return;
        }

        const maxSize = 20 * 1024 * 1024;
        if (file.size > maxSize) {
            alert(`File size cannot exceed 20MB. Current file size: ${(file.size / 1024 / 1024).toFixed(2)}MB`);
            return;
        }

        setUploading(true);
        setUploadProgress(0);

        try {
            const fileType = uploadService.getFileType(file);
            const formData = new FormData();
            formData.append('file', file);

            const token = localStorage.getItem('token');
            if (!token) {
                throw new Error('Authentication token not found');
            }

            const response = await fetch(`${config.BACKEND_URL}/api/chat/upload`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
                body: formData
            });

            const responseText = await response.text();

            let result;
            if (response.ok) {
                try {
                    const data = JSON.parse(responseText);
                    result = {
                        success: true,
                        data: data,
                        fileInfo: {
                            name: file.name,
                            size: file.size,
                            type: file.type,
                            uploadType: fileType
                        }
                    };
                } catch (e) {
                    result = {
                        success: false,
                        message: 'Invalid JSON response from server'
                    };
                }
            } else {
                try {
                    const errorData = JSON.parse(responseText);
                    result = {
                        success: false,
                        message: errorData.msg || errorData.message || `Server error: ${response.status}`
                    };
                } catch (e) {
                    result = {
                        success: false,
                        message: `Server error: ${response.status}`
                    };
                }
            }

            if (result.success) {
                onSendFile && onSendFile({
                    file: result.data,
                    fileInfo: result.fileInfo,
                    type: fileType
                });
            } else {
                alert(`Upload failed: ${result.message}`);
            }
        } catch (error) {
            console.error('File upload error:', error);
            alert('File upload failed, please try again');
        } finally {
            setUploading(false);
            setUploadProgress(0);
        }
    };

    const handleFileChange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        await handleFileUpload(file);
        e.target.value = '';
    };

    // Voice input
    const handleMicClick = () => {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            alert('Your browser does not support voice recognition');
            return;
        }
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!recognitionRef.current) {
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.lang = 'en-US';
            recognitionRef.current.continuous = false;
            recognitionRef.current.interimResults = false;
            recognitionRef.current.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                setInput(transcript);
                setListening(false);
            };
            recognitionRef.current.onerror = () => setListening(false);
            recognitionRef.current.onend = () => setListening(false);
        }
        if (listening) {
            recognitionRef.current.stop();
            setListening(false);
            return;
        }
        setListening(true);
        recognitionRef.current.start();
    };

    return (
        <>
        <footer style={{
            background: isDarkMode ? 'rgba(15, 15, 30, 0.98)' : 'rgba(255, 255, 255, 0.98)',
            backdropFilter: 'blur(20px)',
            borderRadius: '24px 24px 0 0',
            padding: '20px 32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 16,
            boxShadow: isDarkMode ? '0 -4px 24px rgba(0, 0, 0, 0.5)' : '0 -4px 24px rgba(0, 0, 0, 0.08)',
            borderTop: isDarkMode ? '1px solid rgba(80, 80, 120, 0.3)' : '1px solid rgba(145, 70, 255, 0.1)',
            transition: 'all 0.3s ease',
        }}>
            {/* New Chat button - Primary gradient */}
            <button 
                onClick={onNewChat} 
                style={{
                    height: 48,
                    minWidth: 140,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 24,
                    fontSize: 15,
                    fontWeight: 600,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 8,
                    padding: '0 24px',
                    boxShadow: '0 4px 16px rgba(102, 126, 234, 0.3)',
                    cursor: 'pointer',
                    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                }}
                onMouseEnter={(e) => {
                    e.target.style.transform = 'translateY(-2px)';
                    e.target.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.4)';
                }}
                onMouseLeave={(e) => {
                    e.target.style.transform = 'translateY(0)';
                    e.target.style.boxShadow = '0 4px 16px rgba(102, 126, 234, 0.3)';
                }}
                onMouseDown={(e) => {
                    e.target.style.transform = 'translateY(0) scale(0.98)';
                }}
                onMouseUp={(e) => {
                    e.target.style.transform = 'translateY(-2px) scale(1)';
                }}
            >
                <PlusIcon />
                New Chat
            </button>

            {/* 语音按钮 */}
            <button
                onClick={handleMicClick}
                disabled={uploading}
                style={{
                    width: 48,
                    height: 48,
                    borderRadius: '50%',
                    background: listening 
                        ? (isDarkMode ? 'rgba(76, 76, 109, 0.3)' : 'rgba(102, 126, 234, 0.1)')
                        : (isDarkMode ? 'rgba(30, 30, 50, 0.9)' : '#F9FAFB'),
                    border: listening 
                        ? (isDarkMode ? '2px solid rgba(76, 76, 109, 0.6)' : '2px solid #667eea')
                        : (isDarkMode ? '2px solid rgba(80, 80, 120, 0.3)' : '2px solid #E5E7EB'),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: listening ? (isDarkMode ? '#c7d2fe' : '#667eea') : (isDarkMode ? '#9ca3af' : '#64748b'),
                    boxShadow: 'none',
                    cursor: uploading ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s ease',
                    animation: listening ? 'pulse 1.5s ease-in-out infinite' : 'none',
                }}
                title={listening ? 'Listening...' : 'Voice Input'}
                onMouseEnter={(e) => {
                    if (!listening && !uploading) {
                        e.target.style.background = isDarkMode ? 'rgba(40, 40, 60, 0.8)' : 'rgba(102, 126, 234, 0.08)';
                        e.target.style.borderColor = isDarkMode ? 'rgba(76, 76, 109, 0.5)' : '#667eea';
                        e.target.style.color = isDarkMode ? '#c7d2fe' : '#667eea';
                    }
                }}
                onMouseLeave={(e) => {
                    if (!listening) {
                        e.target.style.background = isDarkMode ? 'rgba(30, 30, 50, 0.9)' : '#F9FAFB';
                        e.target.style.borderColor = isDarkMode ? 'rgba(80, 80, 120, 0.3)' : '#E5E7EB';
                        e.target.style.color = isDarkMode ? '#9ca3af' : '#64748b';
                    }
                }}
            >
                <MicIcon />
            </button>

            {/* Upload document button */}
            <button
                onClick={handleFileClick}
                disabled={uploading}
                style={{
                    width: 48,
                    height: 48,
                    borderRadius: '50%',
                    background: uploading
                        ? (isDarkMode ? 'rgba(76, 76, 109, 0.3)' : 'rgba(102, 126, 234, 0.1)')
                        : (isDarkMode ? 'rgba(30, 30, 50, 0.9)' : '#F9FAFB'),
                    border: uploading
                        ? (isDarkMode ? '2px solid rgba(76, 76, 109, 0.6)' : '2px solid #667eea')
                        : (isDarkMode ? '2px solid rgba(80, 80, 120, 0.3)' : '2px solid #E5E7EB'),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: uploading ? (isDarkMode ? '#c7d2fe' : '#667eea') : (isDarkMode ? '#9ca3af' : '#64748b'),
                    boxShadow: 'none',
                    cursor: uploading ? 'not-allowed' : 'pointer',
                    position: 'relative',
                    transition: 'all 0.2s ease',
                }}
                title={uploading ? `Uploading... ${uploadProgress}%` : 'Upload Document'}
                onMouseEnter={(e) => {
                    if (!uploading) {
                        e.target.style.background = isDarkMode ? 'rgba(40, 40, 60, 0.8)' : 'rgba(102, 126, 234, 0.08)';
                        e.target.style.borderColor = isDarkMode ? 'rgba(76, 76, 109, 0.5)' : '#667eea';
                        e.target.style.color = isDarkMode ? '#c7d2fe' : '#667eea';
                    }
                }}
                onMouseLeave={(e) => {
                    if (!uploading) {
                        e.target.style.background = isDarkMode ? 'rgba(30, 30, 50, 0.9)' : '#F9FAFB';
                        e.target.style.borderColor = isDarkMode ? 'rgba(80, 80, 120, 0.3)' : '#E5E7EB';
                        e.target.style.color = isDarkMode ? '#9ca3af' : '#64748b';
                    }
                }}
            >
                {uploading ? (
                    <div style={{
                        width: 20,
                        height: 20,
                        border: '2px solid rgba(102, 126, 234, 0.2)',
                        borderTop: '2px solid #667eea',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                    }} />
                ) : (
                    <FileIcon />
                )}
                <input
                    type="file"
                    accept=".pdf,.doc,.docx,.txt,.xls,.xlsx"
                    ref={fileInputRef}
                    style={{ display: 'none' }}
                    onChange={handleFileChange}
                    disabled={uploading}
                />
            </button>

            {/* View uploaded files button */}
            <button
                onClick={handleShowUserFiles}
                style={{
                    width: 48,
                    height: 48,
                    borderRadius: '50%',
                    background: showUserFiles
                        ? (isDarkMode ? 'rgba(76, 76, 109, 0.3)' : 'rgba(102, 126, 234, 0.1)')
                        : (isDarkMode ? 'rgba(30, 30, 50, 0.9)' : '#F9FAFB'),
                    border: showUserFiles
                        ? (isDarkMode ? '2px solid rgba(76, 76, 109, 0.6)' : '2px solid #667eea')
                        : (isDarkMode ? '2px solid rgba(80, 80, 120, 0.3)' : '2px solid #E5E7EB'),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: showUserFiles ? (isDarkMode ? '#c7d2fe' : '#667eea') : (isDarkMode ? '#9ca3af' : '#64748b'),
                    boxShadow: 'none',
                    cursor: 'pointer',
                    position: 'relative',
                    transition: 'all 0.2s ease',
                }}
                title="My Files"
                onMouseEnter={(e) => {
                    if (!showUserFiles) {
                        e.target.style.background = isDarkMode ? 'rgba(40, 40, 60, 0.8)' : 'rgba(102, 126, 234, 0.08)';
                        e.target.style.borderColor = isDarkMode ? 'rgba(76, 76, 109, 0.5)' : '#667eea';
                        e.target.style.color = isDarkMode ? '#c7d2fe' : '#667eea';
                    }
                }}
                onMouseLeave={(e) => {
                    if (!showUserFiles) {
                        e.target.style.background = isDarkMode ? 'rgba(30, 30, 50, 0.9)' : '#F9FAFB';
                        e.target.style.borderColor = isDarkMode ? 'rgba(80, 80, 120, 0.3)' : '#E5E7EB';
                        e.target.style.color = isDarkMode ? '#9ca3af' : '#64748b';
                    }
                }}
            >
                {loadingUserFiles ? (
                    <div style={{
                        width: 20,
                        height: 20,
                        border: '2px solid rgba(102, 126, 234, 0.2)',
                        borderTop: '2px solid #667eea',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                    }} />
                ) : (
                    <FolderIcon />
                )}
                {userFiles.length > 0 && !loadingUserFiles && (
                    <div style={{
                        position: 'absolute',
                        top: -4,
                        right: -4,
                        background: '#667eea',
                        color: '#fff',
                        borderRadius: '50%',
                        width: 20,
                        height: 20,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 11,
                        fontWeight: 700,
                        boxShadow: '0 2px 4px rgba(102, 126, 234, 0.3)',
                        border: '2px solid #fff',
                    }}>
                        {userFiles.length}
                    </div>
                )}
            </button>

            {/* Input box - Modern design */}
            <div style={{
                flex: 1,
                maxWidth: 600,
                height: 52,
                background: isDarkMode ? 'rgba(30, 30, 50, 0.9)' : '#F9FAFB',
                borderRadius: 26,
                display: 'flex',
                alignItems: 'center',
                padding: '0 20px',
                position: 'relative',
                border: isFocused ? (isDarkMode ? '2px solid rgba(76, 76, 109, 0.6)' : '2px solid #9146FF') : '2px solid transparent',
                boxShadow: isFocused 
                    ? (isDarkMode ? '0 0 0 4px rgba(76, 76, 109, 0.2)' : '0 0 0 4px rgba(145, 70, 255, 0.1)')
                    : (isDarkMode ? '0 2px 8px rgba(0, 0, 0, 0.3)' : '0 2px 8px rgba(0, 0, 0, 0.04)'),
                transition: 'all 0.2s ease',
            }}>
                <input
                    type="text"
                    placeholder="Type a message..."
                    value={input}
                    onChange={handleInputChange}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                    onKeyDown={e => { if (e.key === 'Enter') handleSend(); }}
                    style={{
                        flex: 1,
                        height: '100%',
                        border: 'none',
                        outline: 'none',
                        background: 'transparent',
                        color: isDarkMode ? '#e5e7eb' : '#1F2937',
                        fontSize: 15,
                        fontWeight: 400,
                        fontFamily: 'inherit',
                    }}
                />
                {/* Typing indicator */}
                {isTyping && input && (
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                        marginRight: 8,
                        color: '#9146FF',
                        fontSize: 12,
                    }}>
                        <div style={{
                            width: 4,
                            height: 4,
                            borderRadius: '50%',
                            background: '#9146FF',
                            animation: 'pulse 1s ease-in-out infinite',
                        }} />
                        <div style={{
                            width: 4,
                            height: 4,
                            borderRadius: '50%',
                            background: '#9146FF',
                            animation: 'pulse 1s ease-in-out infinite 0.2s',
                        }} />
                        <div style={{
                            width: 4,
                            height: 4,
                            borderRadius: '50%',
                            background: '#9146FF',
                            animation: 'pulse 1s ease-in-out infinite 0.4s',
                        }} />
                    </div>
                )}
                {/* Character count */}
                {input && (
                    <div style={{
                        fontSize: 11,
                        color: isDarkMode ? '#6b7280' : '#9CA3AF',
                        marginLeft: 8,
                    }}>
                        {input.length}
                    </div>
                )}
            </div>

            {/* Send button - Orange gradient */}
            <button
                onClick={handleSend}
                disabled={!input.trim()}
                style={{
                    width: 52,
                    height: 52,
                    borderRadius: '50%',
                    background: input.trim()
                        ? 'linear-gradient(135deg, #FF9A5A 0%, #FF6B4A 100%)'
                        : '#E5E7EB',
                    border: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: input.trim() ? '#fff' : '#9CA3AF',
                    boxShadow: input.trim() 
                        ? '0 4px 16px rgba(255, 107, 74, 0.3)'
                        : 'none',
                    cursor: input.trim() ? 'pointer' : 'not-allowed',
                    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                }}
                onMouseEnter={(e) => {
                    if (input.trim()) {
                        e.target.style.transform = 'translateY(-2px) scale(1.05)';
                        e.target.style.boxShadow = '0 6px 20px rgba(255, 107, 74, 0.4)';
                    }
                }}
                onMouseLeave={(e) => {
                    if (input.trim()) {
                        e.target.style.transform = 'translateY(0) scale(1)';
                        e.target.style.boxShadow = '0 4px 16px rgba(255, 107, 74, 0.3)';
                    }
                }}
                onMouseDown={(e) => {
                    if (input.trim()) {
                        e.target.style.transform = 'translateY(0) scale(0.95)';
                    }
                }}
                onMouseUp={(e) => {
                    if (input.trim()) {
                        e.target.style.transform = 'translateY(-2px) scale(1.05)';
                    }
                }}
            >
                <PaperPlaneIcon />
            </button>
        </footer>

        {/* User files list modal using Portal */}
        {showUserFiles && createPortal(
            <div style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'rgba(0, 0, 0, 0.6)',
                backdropFilter: 'blur(8px)',
                zIndex: 10000,
                animation: 'fadeIn 0.3s ease-out',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
            }} onClick={() => setShowUserFiles(false)}>
                <div style={{
                    background: '#ffffff',
                    borderRadius: 20,
                    padding: 32,
                    maxWidth: 600,
                    width: '90%',
                    maxHeight: '85vh',
                    overflow: 'auto',
                    boxShadow: '0 25px 80px rgba(0, 0, 0, 0.4), 0 0 1px rgba(0, 0, 0, 0.1)',
                    animation: 'slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                }} onClick={(e) => e.stopPropagation()}>
                        <div style={{ 
                            display: 'flex', 
                            justifyContent: 'space-between', 
                            alignItems: 'center', 
                            marginBottom: 24,
                            paddingBottom: 16,
                            borderBottom: '2px solid #F3F4F6',
                        }}>
                            <h3 style={{ 
                                margin: 0, 
                                color: '#1F2937', 
                                fontSize: 20, 
                                fontWeight: 700,
                            }}>
                                📁 My Files
                            </h3>
                            <button
                                onClick={() => setShowUserFiles(false)}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    fontSize: 28,
                                    cursor: 'pointer',
                                    color: '#9CA3AF',
                                    lineHeight: 1,
                                    transition: 'color 0.2s',
                                }}
                                onMouseEnter={(e) => e.target.style.color = '#EF4444'}
                                onMouseLeave={(e) => e.target.style.color = '#9CA3AF'}
                            >
                                ×
                            </button>
                        </div>

                        {loadingUserFiles ? (
                            <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                                <div style={{
                                    width: 40,
                                    height: 40,
                                    border: '4px solid #F3F4F6',
                                    borderTop: '4px solid #9146FF',
                                    borderRadius: '50%',
                                    animation: 'spin 1s linear infinite',
                                    margin: '0 auto 16px'
                                }}></div>
                                <div style={{ color: '#6B7280', fontSize: 15 }}>Loading...</div>
                            </div>
                        ) : userFiles.length > 0 ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                {userFiles.map((file, index) => {
                                    // Handle both string (old format) and object (new format)
                                    const filename = typeof file === 'string' ? file : (file.filename || 'Unknown file');
                                    const fileType = typeof file === 'object' ? file.file_type : 'document';
                                    const fileSize = typeof file === 'object' && file.size 
                                        ? `${(file.size / 1024).toFixed(1)} KB` 
                                        : '';
                                    
                                    return (
                                        <div key={index} style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            padding: '16px 20px',
                                            background: '#F9FAFB',
                                            borderRadius: 12,
                                            border: '1px solid #E5E7EB',
                                            transition: 'all 0.2s',
                                        }} onMouseEnter={(e) => {
                                            e.currentTarget.style.background = '#F3F4F6';
                                            e.currentTarget.style.borderColor = '#9146FF';
                                        }} onMouseLeave={(e) => {
                                            e.currentTarget.style.background = '#F9FAFB';
                                            e.currentTarget.style.borderColor = '#E5E7EB';
                                        }}>
                                            <div style={{ 
                                                marginRight: 16,
                                                fontSize: 24,
                                            }}>
                                                {fileType === 'image' ? '🖼️' : 
                                                 fileType === 'audio' ? '🎵' : 
                                                 fileType === 'document' ? '📄' : '📎'}
                                            </div>
                                            <div style={{ flex: 1 }}>
                                                <div style={{ 
                                                    fontWeight: 600, 
                                                    color: '#1F2937', 
                                                    fontSize: 14,
                                                    marginBottom: 4,
                                                }}>
                                                    {filename}
                                                </div>
                                                <div style={{ 
                                                    fontSize: 12, 
                                                    color: '#6B7280',
                                                }}>
                                                    {filename && typeof filename === 'string' 
                                                        ? filename.split('.').pop()?.toUpperCase() || 'Unknown' 
                                                        : 'Unknown'} file
                                                    {fileSize && ` • ${fileSize}`}
                                                </div>
                                            </div>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleDeleteFile(filename);
                                                }}
                                                disabled={deletingFiles.has(filename)}
                                                style={{
                                                    background: deletingFiles.has(filename) ? '#D1D5DB' : '#EF4444',
                                                    color: '#fff',
                                                    border: 'none',
                                                    borderRadius: 8,
                                                    padding: '10px 12px',
                                                    cursor: deletingFiles.has(filename) ? 'not-allowed' : 'pointer',
                                                    transition: 'all 0.2s',
                                                    marginLeft: 12,
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                }}
                                                onMouseEnter={(e) => {
                                                    if (!deletingFiles.has(filename)) {
                                                        e.target.style.background = '#DC2626';
                                                        e.target.style.transform = 'scale(1.05)';
                                                    }
                                                }}
                                                onMouseLeave={(e) => {
                                                    if (!deletingFiles.has(filename)) {
                                                        e.target.style.background = '#EF4444';
                                                        e.target.style.transform = 'scale(1)';
                                                    }
                                                }}
                                            title={deletingFiles.has(filename) ? "Deleting..." : "Delete file"}
                                        >
                                            {deletingFiles.has(filename) ? (
                                                <div style={{
                                                    width: 16,
                                                    height: 16,
                                                    border: '2px solid #fff',
                                                    borderTop: '2px solid transparent',
                                                    borderRadius: '50%',
                                                    animation: 'spin 1s linear infinite'
                                                }}></div>
                                            ) : (
                                                <DeleteIcon />
                                            )}
                                        </button>
                                    </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <div style={{ 
                                textAlign: 'center', 
                                padding: '60px 20px', 
                                color: '#6B7280' 
                            }}>
                                <div style={{ fontSize: 64, marginBottom: 20 }}>📂</div>
                                <div style={{ fontSize: 16, marginBottom: 8, fontWeight: 600, color: '#374151' }}>
                                    No files uploaded yet
                                </div>
                                <div style={{ fontSize: 14, color: '#9CA3AF' }}>
                                    Upload your first document to see it here
                                </div>
                            </div>
                        )}
                    </div>
                </div>,
            document.body
        )}
        </>
    );
}

export default HomeFooter;
