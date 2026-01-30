import React, { useState, useRef, useEffect } from 'react';
import userService from '../../services/userService';
import chatService from '../../services/chatService';
import authService from '../../services/authService';
import config from '../../config';

const BASE_URL = config.BACKEND_URL;

// 添加滚动条样式
const scrollbarStyles = `
.subject-list-scrollbar::-webkit-scrollbar {
    width: 6px;
}

.subject-list-scrollbar::-webkit-scrollbar-track {
    background: rgba(102, 126, 234, 0.05);
    border-radius: 10px;
}

.subject-list-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(102, 126, 234, 0.3);
    border-radius: 10px;
    transition: all 0.3s ease;
}

.subject-list-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(102, 126, 234, 0.5);
}

.subject-list-scrollbar {
    scrollbar-width: thin;
    scrollbar-color: rgba(102, 126, 234, 0.3) rgba(102, 126, 234, 0.05);
}
`;

// 注入样式到页面
if (typeof document !== 'undefined') {
    const styleId = 'subject-list-scrollbar-styles';
    if (!document.getElementById(styleId)) {
        const styleElement = document.createElement('style');
        styleElement.id = styleId;
        styleElement.textContent = scrollbarStyles;
        document.head.appendChild(styleElement);
    }
}

// 科技风格SVG图标组件
const BookIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 6.253L17.5 3v13l-5.5 3.25L6.5 16V3l5.5 3.253z" fill="url(#gradient-primary)" stroke="url(#gradient-primary)" strokeWidth="1.5"/>
    <defs>
      <linearGradient id="gradient-primary" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style={{ stopColor: '#667eea' }} />
        <stop offset="100%" style={{ stopColor: '#764ba2' }} />
      </linearGradient>
    </defs>
  </svg>
);

const CollapseIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M15 18l-6-6 6-6" stroke="#667eea" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M19 4v16" stroke="#667eea" strokeWidth="2" strokeLinecap="round"/>
  </svg>
);

const ExpandIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const UserIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="8" r="5" fill="currentColor"/>
    <path d="M20 21a8 8 0 0 0-16 0" fill="currentColor"/>
  </svg>
);

const ChatIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" stroke="currentColor" strokeWidth="1.5" fill="none"/>
  </svg>
);

const StarIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="#fbbf24"/>
  </svg>
);

const StarOutlineIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" stroke="#94a3b8" strokeWidth="1.5" fill="none"/>
  </svg>
);

const DeleteIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 6h18m-2 0v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6m3 0V4c0-1 1-2 2-2h4c0-1 1-2 2-2v2m-3 4v6m4-6v6" stroke="#ef4444" strokeWidth="1.5" fill="none"/>
  </svg>
);

const SunIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="12" r="5" fill="currentColor"/>
    <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" stroke="currentColor" strokeWidth="2"/>
  </svg>
);

const MoonIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" fill="currentColor"/>
  </svg>
);

const SearchIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="11" cy="11" r="8" stroke="#94a3b8" strokeWidth="2" fill="none"/>
    <path d="m21 21-4.35-4.35" stroke="#94a3b8" strokeWidth="2"/>
  </svg>
);

const PlusIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
  </svg>
);

const TrashIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 6h18M8 6V4c0-1.1.9-2 2-2h4c1.1 0 2 .9 2 2v2m3 0v14c0 1.1-.9 2-2 2H7c-1.1 0-2-.9-2-2V6h14z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

function SidebarTab({ active, label, count, onClick, themeStyles }) {
    return (
        <div
            onClick={onClick}
            style={{
                display: 'flex',
                alignItems: 'center',
                padding: '12px 20px',
                borderRadius: 12,
                background: active 
                    ? 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)'
                    : 'transparent',
                border: active ? '1px solid rgba(102, 126, 234, 0.2)' : '1px solid transparent',
                color: !active ? themeStyles?.inactiveColor || '#64748b' : 'inherit',
                marginRight: 8,
                cursor: 'pointer',
                boxShadow: active ? '0 4px 16px rgba(102, 126, 234, 0.15)' : 'none',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                transform: active ? 'translateY(-1px)' : 'none',
                fontSize: '13px',
                letterSpacing: '0.5px',
                position: 'relative',
                overflow: 'hidden',
            }}
            onMouseEnter={(e) => {
                if (!active) {
                    e.target.style.background = 'rgba(102, 126, 234, 0.05)';
                    e.target.style.transform = 'translateY(-1px)';
                }
            }}
            onMouseLeave={(e) => {
                if (!active) {
                    e.target.style.background = 'transparent';
                    e.target.style.transform = 'none';
                }
            }}
        >
            <span style={{ 
                textTransform: 'uppercase',
                background: active ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'transparent',
                WebkitBackgroundClip: active ? 'text' : 'border-box',
                WebkitTextFillColor: active ? 'transparent' : 'currentColor',
                backgroundClip: active ? 'text' : 'border-box',
                fontWeight: active ? 700 : 500,
                color: !active ? 'inherit' : 'transparent',
            }}>{label}</span>
            {typeof count === 'number' && (
                <span style={{
                    background: active 
                        ? 'rgba(102, 126, 234, 0.15)'
                        : 'rgba(100, 116, 139, 0.1)',
                    color: active ? '#667eea' : themeStyles?.inactiveCountColor || '#64748b',
                    borderRadius: 8,
                    fontSize: 10,
                    fontWeight: 700,
                    marginLeft: 'auto',
                    padding: '4px 8px',
                    minWidth: 20,
                    textAlign: 'center',
                    border: active ? '1px solid rgba(102, 126, 234, 0.2)' : 'none',
                    transition: 'all 0.3s ease',
                }}>{count}</span>
            )}
            
            {/* 活跃状态的光效 */}
            {active && (
                <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, transparent 50%)',
                    borderRadius: 12,
                    pointerEvents: 'none',
                }} />
            )}
        </div>
    );
}

function ChatGroup({ title, chats, selectedId, onSelect, onDelete, onToggleFavorite, isSavedTab = false, themeStyles }) {
    return (
        <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 13, color: themeStyles?.groupTitleColor || '#757575', fontWeight: 600, margin: '12px 0 4px 8px' }}>{title}</div>
            {chats.map(chat => (
                <div
                    key={chat.id}
                    style={{
                        background: chat.id === selectedId 
                            ? (themeStyles?.selectedBackground || '#AF52DE') 
                            : (themeStyles?.isDarkMode ? 'rgba(30, 30, 50, 0.6)' : '#fff'),
                        color: chat.id === selectedId ? themeStyles?.selectedColor || '#fff' : (themeStyles?.isDarkMode ? '#e5e7eb' : themeStyles?.inactiveColor || '#1C1C1C'),
                        borderRadius: 8,
                        padding: '10px 14px',
                        marginBottom: 6,
                        display: 'flex',
                        alignItems: 'center',
                        cursor: 'pointer',
                        boxShadow: chat.id === selectedId ? themeStyles?.selectedShadow || '0 2px 8px #AF52DE22' : 'none',
                        transition: 'all 0.2s',
                        position: 'relative',
                        border: themeStyles?.isDarkMode && chat.id !== selectedId ? '1px solid rgba(80, 80, 120, 0.2)' : 'none',
                    }}
                    onMouseEnter={(e) => {
                        e.currentTarget.querySelector('.chat-actions').style.opacity = '1';
                        if (chat.id !== selectedId && themeStyles?.isDarkMode) {
                            e.currentTarget.style.background = 'rgba(50, 50, 70, 0.8)';
                        }
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.querySelector('.chat-actions').style.opacity = '0';
                        if (chat.id !== selectedId && themeStyles?.isDarkMode) {
                            e.currentTarget.style.background = 'rgba(30, 30, 50, 0.6)';
                        }
                    }}
                >
                    <div
                        style={{ display: 'flex', alignItems: 'center', flex: 1 }}
                        onClick={() => onSelect(chat.id)}
                    >
                        <ChatIcon />
                        <div style={{ marginLeft: 10, flex: 1 }}>
                            <div style={{ fontWeight: 600 }}>{chat.title}</div>
                            {chat.subtitle && <div style={{ fontSize: 12, color: chat.id === selectedId ? themeStyles?.selectedSubtitleColor || '#fff' : themeStyles?.inactiveSubtitleColor || '#757575' }}>{chat.subtitle}</div>}
                        </div>
                    </div>
                    {/* Action buttons */}
                    <div
                        className="chat-actions"
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 4,
                            opacity: 0,
                            transition: 'opacity 0.2s',
                            marginLeft: 8
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Favorite/Unfavorite button */}
                        <div
                            style={{
                                padding: 4,
                                borderRadius: 4,
                                cursor: 'pointer',
                                background: 'rgba(255,255,255,0.1)',
                                transition: 'background 0.2s'
                            }}
                            onClick={() => onToggleFavorite(chat.id)}
                            title={isSavedTab ? 'unFavorite' : (chat.isFavorite ? 'Unfavorite' : 'Favorite')}
                        >
                            {chat.isFavorite ? <StarIcon /> : <StarOutlineIcon />}
                        </div>
                        {/* Delete button */}
                        {!isSavedTab && (
                            <div
                                style={{
                                    padding: 4,
                                    borderRadius: 4,
                                    cursor: 'pointer',
                                    background: 'rgba(255,255,255,0.1)',
                                    transition: 'background 0.2s'
                                }}
                                onClick={() => onDelete(chat.id)}
                                title="Delete conversation"
                            >
                                <DeleteIcon />
                            </div>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
}



// User profile editing modal component
function UserProfileModal({ isOpen, onClose, onLogout }) {
    const [userInfo, setUserInfo] = useState({
        name: '',
        full_name: '',
        bio: ''
    });

    const [passwordInfo, setPasswordInfo] = useState({
        newPassword: '',
        confirmPassword: '',
        code: '' // verification code field
    });
    const [sendingCode, setSendingCode] = useState(false);
    const [codeTimer, setCodeTimer] = useState(0);

    const [uploadedAvatar, setUploadedAvatar] = useState(null);
    const [activeView, setActiveView] = useState('profile'); // 'profile' or 'password'
    const fileInputRef = useRef();

    useEffect(() => {
        if (isOpen) {
            // 直接从 localStorage 获取用户信息
            const userStr = localStorage.getItem('user');
            if (userStr) {
                const user = JSON.parse(userStr);
                setUserInfo({
                    name: user.username || '',
                    full_name: user.full_name || '',
                    bio: user.bio || ''
                });
                setUploadedAvatar(user.avatar || user.avatar_url || null);
            }
        }
    }, [isOpen]);

    // 發送驗證碼
    const handleSendCode = async () => {
        if (sendingCode || codeTimer > 0) return;
        // 從 localStorage 取 email
        const userStr = localStorage.getItem('user');
        const user = userStr ? JSON.parse(userStr) : null;
        const email = user?.email;
        if (!email) {
            alert('No email found in user info!');
            return;
        }
        setSendingCode(true);
        const res = await authService.sendVerificationCode({ email, purpose: 'update_password' });
        setSendingCode(false);
        if (res.success) {
            alert('Verification code sent, please check your email!');
            setCodeTimer(60);
        } else {
            alert(res.message || 'Failed to send verification code');
        }
    };
    // 倒計時效果
    useEffect(() => {
        if (codeTimer > 0) {
            const timer = setTimeout(() => setCodeTimer(codeTimer - 1), 1000);
            return () => clearTimeout(timer);
        }
    }, [codeTimer]);

    if (!isOpen) return null;

    const handleSave = async () => {
        if (activeView === 'profile') {
            // 保存用户信息
            const res = await userService.updateProfile({
                username: userInfo.name,
                full_name: userInfo.full_name,
                bio: userInfo.bio
            });
            if (res.success) {
                // 同步本地 user 信息
                const userStr = localStorage.getItem('user');
                if (userStr) {
                    const user = JSON.parse(userStr);
                    user.username = userInfo.name;
                    user.full_name = userInfo.full_name;
                    user.bio = userInfo.bio;
                    localStorage.setItem('user', JSON.stringify(user));
                }
                alert('User information saved successfully!');
                onClose();
            } else {
                alert(res.message || 'Failed to save user information.');
            }
        } else {
            // Password validation
            if (!passwordInfo.code) {
                alert('Please enter the verification code!');
                return;
            }
            if (!passwordInfo.newPassword) {
                alert('Please enter your new password!');
                return;
            }
            // 密码复杂度验证
            const password = passwordInfo.newPassword;
            const minLength = 8;
            const hasUpperCase = /[A-Z]/.test(password);
            const hasLowerCase = /[a-z]/.test(password);
            const hasNumbers = /\d/.test(password);
            const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);

            if (password.length < minLength) {
                alert(`Password must be at least ${minLength} characters long!`);
                return;
            }
            if (!hasUpperCase) {
                alert('Password must contain at least one uppercase letter (A-Z)!');
                return;
            }
            if (!hasLowerCase) {
                alert('Password must contain at least one lowercase letter (a-z)!');
                return;
            }
            if (!hasNumbers) {
                alert('Password must contain at least one number (0-9)!');
                return;
            }
            if (!hasSpecialChar) {
                alert('Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.)!');
                return;
            }
            if (passwordInfo.newPassword !== passwordInfo.confirmPassword) {
                alert('New password and confirm password do not match!');
                return;
            }
            // 調用新接口
            const res = await authService.updatePasswordWithCode({
                code: passwordInfo.code,
                new_password: passwordInfo.newPassword
            });
            if (res.success) {
                alert('Password changed successfully! You will be logged out automatically.');
                // Clear password form
                setPasswordInfo({ newPassword: '', confirmPassword: '', code: '' });
                setActiveView('profile');
                // Close modal
                onClose();

                // Force clear all localStorage items
                console.log('Clearing localStorage...');
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                console.log('localStorage cleared. Token:', localStorage.getItem('token'), 'User:', localStorage.getItem('user'));

                // Execute complete logout logic
                await authService.logout();

                // Call parent logout handler to update app state
                if (onLogout) {
                    onLogout();
                }

                // Force redirect to login page with a small delay to ensure state updates
                setTimeout(() => {
                    // Double check that localStorage is cleared
                    if (localStorage.getItem('token') || localStorage.getItem('user')) {
                        localStorage.removeItem('token');
                        localStorage.removeItem('user');
                    }
                    console.log('Redirecting to login page...');
                    // Force page reload to ensure clean state
                    window.location.href = '/login';
                }, 200);
            } else {
                alert(res.message || 'Failed to change password');
            }
        }
    };

    const handleAvatarUpload = async (event) => {
        const file = event.target.files[0];
        if (file) {
            if (file.size > 5 * 1024 * 1024) { // 5MB limit
                alert('Image size cannot exceed 5MB!');
                return;
            }
            // 上传头像
            const res = await userService.uploadAvatar(file);
            if (res.success) {
                setUploadedAvatar(res.avatar_url);
                // 同步本地 user 信息
                const userStr = localStorage.getItem('user');
                if (userStr) {
                    const user = JSON.parse(userStr);
                    user.avatar = res.avatar_url;
                    localStorage.setItem('user', JSON.stringify(user));
                }
                alert('Avatar uploaded successfully!');
            } else {
                alert(res.message || 'Failed to upload avatar.');
            }
        }
    };

    const handleAvatarClick = () => {
        fileInputRef.current?.click();
    };

    const handleBackToProfile = () => {
        setActiveView('profile');
        setPasswordInfo({ newPassword: '', confirmPassword: '', code: '' });
    };

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
        }} onClick={onClose}>
            <div style={{
                background: '#fff',
                borderRadius: 16,
                padding: 24,
                maxWidth: 400,
                width: '90%',
                boxShadow: '0 8px 32px rgba(0,0,0,0.2)'
            }} onClick={(e) => e.stopPropagation()}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                    <h3 style={{ margin: 0, color: '#333', fontSize: 18, fontWeight: 600 }}>
                        {activeView === 'profile' ? 'User Profile' : 'Change Password'}
                    </h3>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: '#999' }}>×</button>
                </div>

                {activeView === 'profile' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                        {/* 1. Avatar upload */}
                        <div>
                            <label style={{ display: 'block', marginBottom: 12, fontSize: 14, fontWeight: 500, color: '#333' }}>Avatar</label>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <div style={{ position: 'relative' }}>
                                    <div
                                        onClick={handleAvatarClick}
                                        style={{
                                            width: 80,
                                            height: 80,
                                            borderRadius: '50%',
                                            background: uploadedAvatar ? 'transparent' : '#f0f0f0',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            cursor: 'pointer',
                                            fontSize: uploadedAvatar ? 0 : 40,
                                            border: '2px dashed #ddd',
                                            overflow: 'hidden',
                                            transition: 'all 0.2s'
                                        }}
                                        onMouseEnter={(e) => {
                                            e.target.style.borderColor = '#667eea';
                                            e.target.style.background = uploadedAvatar ? 'transparent' : '#f8f9fa';
                                        }}
                                        onMouseLeave={(e) => {
                                            e.target.style.borderColor = '#ddd';
                                            e.target.style.background = uploadedAvatar ? 'transparent' : '#f0f0f0';
                                        }}
                                    >
                                        {uploadedAvatar ? (
                                            <img
                                                src={uploadedAvatar.startsWith('http') ? uploadedAvatar : `${BASE_URL}${uploadedAvatar}`}
                                                alt="User avatar"
                                                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                            />
                                        ) : (
                                            '👤'
                                        )}
                                    </div>
                                    <div style={{
                                        position: 'absolute',
                                        bottom: 0,
                                        right: 0,
                                        background: '#667eea',
                                        color: '#fff',
                                        borderRadius: '50%',
                                        width: 24,
                                        height: 24,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        fontSize: 12,
                                        cursor: 'pointer'
                                    }} onClick={handleAvatarClick}>
                                        📷
                                    </div>
                                </div>
                            </div>
                            <input
                                type="file"
                                ref={fileInputRef}
                                accept="image/*"
                                style={{ display: 'none' }}
                                onChange={handleAvatarUpload}
                            />
                            <div style={{ fontSize: 12, color: '#666', marginTop: 8, textAlign: 'center' }}>
                                Click to upload avatar, supports JPG, PNG format, max 5MB
                            </div>
                        </div>

                        {/* 2. Username modification */}
                        <div>
                            <label style={{ display: 'block', marginBottom: 8, fontSize: 14, fontWeight: 500, color: '#333' }}>Username</label>
                            <input
                                type="text"
                                value={userInfo.name}
                                onChange={(e) => setUserInfo(prev => ({ ...prev, name: e.target.value }))}
                                placeholder="Enter username"
                                style={{
                                    width: '100%',
                                    padding: '12px 16px',
                                    borderRadius: 8,
                                    border: '1px solid #e2e8f0',
                                    fontSize: 14,
                                    transition: 'all 0.2s'
                                }}
                            />
                        </div>

                        {/* 3. Full name modification */}
                        <div>
                            <label style={{ display: 'block', marginBottom: 8, fontSize: 14, fontWeight: 500, color: '#333' }}>Full Name</label>
                            <input
                                type="text"
                                value={userInfo.full_name}
                                onChange={(e) => setUserInfo(prev => ({ ...prev, full_name: e.target.value }))}
                                placeholder="Enter your full name"
                                style={{
                                    width: '100%',
                                    padding: '12px 16px',
                                    borderRadius: 8,
                                    border: '1px solid #e2e8f0',
                                    fontSize: 14,
                                    transition: 'all 0.2s'
                                }}
                            />
                        </div>

                        {/* 4. Bio modification */}
                        <div>
                            <label style={{ display: 'block', marginBottom: 8, fontSize: 14, fontWeight: 500, color: '#333' }}>Bio</label>
                            <textarea
                                value={userInfo.bio}
                                onChange={(e) => setUserInfo(prev => ({ ...prev, bio: e.target.value }))}
                                placeholder="Tell us about yourself..."
                                rows={3}
                                style={{
                                    width: '100%',
                                    padding: '12px 16px',
                                    borderRadius: 8,
                                    border: '1px solid #e2e8f0',
                                    fontSize: 14,
                                    transition: 'all 0.2s',
                                    resize: 'vertical',
                                    fontFamily: 'inherit'
                                }}
                            />
                        </div>

                        {/* 5. Password change button */}
                        <div>
                            <button
                                onClick={() => setActiveView('password')}
                                style={{
                                    width: '100%',
                                    padding: '12px 16px',
                                    background: '#f8fafc',
                                    color: '#667eea',
                                    border: '1px solid #e2e8f0',
                                    borderRadius: 8,
                                    fontSize: 14,
                                    fontWeight: 500,
                                    cursor: 'pointer',
                                    transition: 'all 0.2s',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: 8
                                }}
                                onMouseEnter={(e) => {
                                    e.target.style.background = '#f1f5f9';
                                    e.target.style.borderColor = '#667eea';
                                }}
                                onMouseLeave={(e) => {
                                    e.target.style.background = '#f8fafc';
                                    e.target.style.borderColor = '#e2e8f0';
                                }}
                            >
                                🔒 Change Password
                            </button>
                        </div>
                    </div>
                )}

                {activeView === 'password' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                        {/* Verification code input + send button */}
                        <div>
                            <label style={{ display: 'block', marginBottom: 8, fontSize: 14, fontWeight: 500, color: '#333' }}>Verification Code</label>
                            <div style={{ display: 'flex', gap: 8 }}>
                                <input
                                    type="text"
                                    value={passwordInfo.code}
                                    onChange={(e) => setPasswordInfo(prev => ({ ...prev, code: e.target.value }))}
                                    placeholder="Enter the code sent to your email"
                                    style={{
                                        flex: 1,
                                        padding: '12px 16px',
                                        borderRadius: 8,
                                        border: '1px solid #e2e8f0',
                                        fontSize: 14,
                                        transition: 'all 0.2s'
                                    }}
                                />
                                <button
                                    type="button"
                                    onClick={handleSendCode}
                                    disabled={sendingCode || codeTimer > 0}
                                    style={{
                                        minWidth: 120,
                                        padding: '10px 12px',
                                        borderRadius: 8,
                                        border: 'none',
                                        background: (sendingCode || codeTimer > 0) ? '#e2e8f0' : '#667eea',
                                        color: (sendingCode || codeTimer > 0) ? '#aaa' : '#fff',
                                        fontWeight: 500,
                                        fontSize: 14,
                                        cursor: (sendingCode || codeTimer > 0) ? 'not-allowed' : 'pointer',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    {codeTimer > 0 ? `Resend (${codeTimer}s)` : (sendingCode ? 'Sending...' : 'Send Code')}
                                </button>
                            </div>
                        </div>
                        {/* New password */}
                        <div>
                            <label style={{ display: 'block', marginBottom: 8, fontSize: 14, fontWeight: 500, color: '#333' }}>New Password</label>
                            <input
                                type="password"
                                value={passwordInfo.newPassword}
                                onChange={(e) => setPasswordInfo(prev => ({ ...prev, newPassword: e.target.value }))}
                                placeholder="Enter new password (at least 6 characters)"
                                style={{
                                    width: '100%',
                                    padding: '12px 16px',
                                    borderRadius: 8,
                                    border: '1px solid #e2e8f0',
                                    fontSize: 14,
                                    transition: 'all 0.2s'
                                }}
                            />
                        </div>

                        {/* Confirm new password */}
                        <div>
                            <label style={{ display: 'block', marginBottom: 8, fontSize: 14, fontWeight: 500, color: '#333' }}>Confirm New Password</label>
                            <input
                                type="password"
                                value={passwordInfo.confirmPassword}
                                onChange={(e) => setPasswordInfo(prev => ({ ...prev, confirmPassword: e.target.value }))}
                                placeholder="Enter new password again"
                                style={{
                                    width: '100%',
                                    padding: '12px 16px',
                                    borderRadius: 8,
                                    border: passwordInfo.newPassword !== passwordInfo.confirmPassword && passwordInfo.confirmPassword ? '1px solid #ef4444' : '1px solid #e2e8f0',
                                    fontSize: 14,
                                    transition: 'all 0.2s'
                                }}
                            />
                            {passwordInfo.newPassword !== passwordInfo.confirmPassword && passwordInfo.confirmPassword && (
                                <div style={{ fontSize: 12, color: '#ef4444', marginTop: 4 }}>
                                    Passwords do not match
                                </div>
                            )}
                        </div>

                        {/* Password requirements hint */}
                        <div style={{
                            padding: 12,
                            background: '#f8fafc',
                            borderRadius: 8,
                            border: '1px solid #e2e8f0'
                        }}>
                            <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>Password Requirements:</div>
                            <ul style={{ fontSize: 12, color: '#666', margin: 0, paddingLeft: 16 }}>
                                <li>At least 8 characters long</li>
                                <li>At least one uppercase letter (A-Z)</li>
                                <li>At least one lowercase letter (a-z)</li>
                                <li>At least one number (0-9)</li>
                                <li>At least one special character (!@#$%^&*()_+-=[]{ }|;:,.)</li>
                                <li>Do not use the same password as current password</li>
                            </ul>
                        </div>
                    </div>
                )}

                <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
                    {activeView === 'password' && (
                        <button
                            onClick={handleBackToProfile}
                            style={{
                                flex: 1,
                                padding: '12px',
                                background: '#f1f5f9',
                                color: '#64748b',
                                border: 'none',
                                borderRadius: 8,
                                fontSize: 14,
                                fontWeight: 500,
                                cursor: 'pointer',
                                transition: 'all 0.2s'
                            }}
                            onMouseEnter={(e) => e.target.style.background = '#e2e8f0'}
                            onMouseLeave={(e) => e.target.style.background = '#f1f5f9'}
                        >
                            Back
                        </button>
                    )}
                    <button
                        onClick={handleSave}
                        style={{
                            flex: activeView === 'password' ? 1 : 1,
                            padding: '12px',
                            background: '#667eea',
                            color: '#fff',
                            border: 'none',
                            borderRadius: 8,
                            fontSize: 14,
                            fontWeight: 500,
                            cursor: 'pointer',
                            transition: 'all 0.2s'
                        }}
                        onMouseEnter={(e) => e.target.style.background = '#5a67d8'}
                        onMouseLeave={(e) => e.target.style.background = '#667eea'}
                    >
                        {activeView === 'profile' ? 'Save' : 'Confirm Change'}
                    </button>
                    <button
                        onClick={onClose}
                        style={{
                            flex: 1,
                            padding: '12px',
                            background: '#f1f5f9',
                            color: '#64748b',
                            border: 'none',
                            borderRadius: 8,
                            fontSize: 14,
                            fontWeight: 500,
                            cursor: 'pointer',
                            transition: 'all 0.2s'
                        }}
                        onMouseEnter={(e) => e.target.style.background = '#e2e8f0'}
                        onMouseLeave={(e) => e.target.style.background = '#f1f5f9'}
                    >
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    );
}

function HomeSidebar({ sessions, selectedChatId, onSelectChat, onRefreshSessions, onThemeChange, themeStyles, onLogout, selectedSubject, onSubjectChange }) {
    const [tab, setTab] = React.useState('chats');
    const [open, setOpen] = React.useState(true);
    const [showUserProfile, setShowUserProfile] = useState(false);
    const [isDarkMode, setIsDarkMode] = useState(false);

    // 科目管理
    const [subjects, setSubjects] = useState([]);
    const [showAddSubject, setShowAddSubject] = useState(false);
    const [newSubjectInput, setNewSubjectInput] = useState('');
    
    // 搜索功能
    const [searchQuery, setSearchQuery] = useState('');
    
    // 使用本地state作为fallback，如果没有传入selectedSubject
    const [localSelectedSubject, setLocalSelectedSubject] = useState('All');
    const currentSubject = selectedSubject || localSelectedSubject;
    const handleSubjectChange = onSubjectChange || setLocalSelectedSubject;

    const [userRole, setUserRole] = useState('Student');


    useEffect(() => {
        const userStr = localStorage.getItem('user');
        if (userStr) {
            const user = JSON.parse(userStr);
            // Get user role and capitalize first letter
            const role = user.role || 'student';
            setUserRole(role.charAt(0).toUpperCase() + role.slice(1));
        }
        
        // Load subject list
        const savedSubjects = localStorage.getItem('userSubjects');
        if (savedSubjects) {
            try {
                setSubjects(JSON.parse(savedSubjects));
            } catch (e) {
                // If parsing fails, use default subjects
                setSubjects(['COMP9311', 'COMP9331', 'COMP6771']);
            }
        } else {
            // Default subjects
            setSubjects(['COMP9311', 'COMP9331', 'COMP6771']);
        }
    }, []);

    function groupSessionsByTime(sessions) {
        const now = new Date();
        const today = [];
        const yesterday = [];
        const thisWeek = [];
        const earlier = [];

        sessions.forEach(s => {
            const updated = s.updated_at ? new Date(s.updated_at) : null;
            if (!updated) {
                earlier.push(s);
                return;
            }
            const diffTime = now - updated;
            const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
            if (diffDays === 0 && now.getDate() === updated.getDate()) {
                today.push(s);
            } else if (diffDays === 1 || (diffDays === 0 && now.getDate() !== updated.getDate())) {
                yesterday.push(s);
            } else if (diffDays < 7) {
                thisWeek.push(s);
            } else {
                earlier.push(s);
            }
        });
        return [
            { group: 'Today', chats: today },
            { group: 'Yesterday', chats: yesterday },
            { group: 'This Week', chats: thisWeek },
            { group: 'Earlier', chats: earlier }
        ];
    }

    // 科目管理函数
    const saveSubjectsToStorage = (subjectList) => {
        localStorage.setItem('userSubjects', JSON.stringify(subjectList));
    };

    const handleAddSubject = () => {
        const trimmed = newSubjectInput.trim().toUpperCase();
        if (!trimmed) {
            alert('Please enter a subject code');
            return;
        }
        if (subjects.includes(trimmed)) {
            alert('This subject already exists');
            return;
        }
        const newSubjects = [...subjects, trimmed];
        setSubjects(newSubjects);
        saveSubjectsToStorage(newSubjects);
        setNewSubjectInput('');
        setShowAddSubject(false);
    };

    const handleDeleteSubject = (subjectToDelete) => {
        if (window.confirm(`Are you sure you want to delete ${subjectToDelete}?`)) {
            const newSubjects = subjects.filter(s => s !== subjectToDelete);
            setSubjects(newSubjects);
            saveSubjectsToStorage(newSubjects);
            // 如果删除的是当前选中的科目，切换到"All"
            if (currentSubject === subjectToDelete) {
                handleSubjectChange('All');
            }
        }
    };

    // 根据选中的科目和搜索关键词过滤sessions
    const filteredSessions = sessions.filter(session => {
        const title = session.title || '';
        
        // 科目过滤
        let matchesSubject = false;
        if (currentSubject === 'All') {
            matchesSubject = true;
        } else {
            matchesSubject = title.includes(`[${currentSubject}]`) || title.includes(currentSubject);
        }
        
        // 搜索过滤
        let matchesSearch = true;
        if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase();
            matchesSearch = title.toLowerCase().includes(query);
        }
        
        return matchesSubject && matchesSearch;
    });

    const favoriteSessions = filteredSessions.filter(s => s.is_favorite);

    const chatGroupsData = groupSessionsByTime(filteredSessions);

    const handleToggleFavorite = async (chatId, isFav) => {
        await chatService.setSessionFavorite(chatId, !isFav);
        onRefreshSessions && onRefreshSessions();
    };
    const handleDeleteChat = async (chatId) => {
        if (window.confirm('Are you sure you want to delete this conversation?')) {
            await chatService.deleteSession(chatId);
            onRefreshSessions && onRefreshSessions();
        }
    };


    const toggleTheme = () => {
        const newMode = !isDarkMode;
        setIsDarkMode(newMode);
        if (onThemeChange) {
            onThemeChange(newMode);
        }
    };

    // 新建会话 - 根据选中的科目决定是否添加标签
    const handleNewChat = async () => {
        let chatTitle;
        if (currentSubject === 'All') {
            // 如果选择的是"All"，不添加科目标签
            chatTitle = 'New Chat';
        } else {
            // 否则添加科目标签
            chatTitle = `[${currentSubject}] New Chat`;
        }
        const res = await chatService.createSession(chatTitle);
        if (res.success) {
            onRefreshSessions && onRefreshSessions();
        } else {
            alert(res.message || 'Failed to create new chat');
        }
    };

    if (!open) {
        // Collapsed state - Clean and minimal
        const isDarkMode = themeStyles?.isDarkMode || false;
        return (
            <aside style={{
                width: 56,
                background: isDarkMode ? 'rgba(15, 15, 30, 0.98)' : 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(20px)',
                height: '100vh',
                borderRadius: '24px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                boxShadow: isDarkMode ? '0 4px 16px rgba(0, 0, 0, 0.5)' : '0 4px 16px rgba(0, 0, 0, 0.04)',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                margin: '16px 0 16px 16px',
                border: isDarkMode ? '1px solid rgba(80, 80, 120, 0.3)' : '1px solid rgba(0, 0, 0, 0.05)',
            }}>
                <div style={{
                    height: 80,
                    borderRadius: '24px 24px 0 0',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '100%',
                    borderBottom: isDarkMode ? '1px solid rgba(80, 80, 120, 0.2)' : '1px solid rgba(0, 0, 0, 0.05)',
                }}>
                    <div
                        style={{
                            width: 40,
                            height: 40,
                            borderRadius: '50%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: 'pointer',
                            transition: 'all 0.3s ease',
                            color: isDarkMode ? '#9ca3af' : '#64748b',
                        }}
                        onClick={() => setOpen(true)}
                        title="Expand Sidebar"
                        onMouseEnter={(e) => {
                            e.currentTarget.style.background = isDarkMode ? 'rgba(76, 76, 109, 0.3)' : 'rgba(102, 126, 234, 0.1)';
                            e.currentTarget.style.color = isDarkMode ? '#c7d2fe' : '#667eea';
                            e.currentTarget.style.transform = 'scale(1.1)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'transparent';
                            e.currentTarget.style.color = isDarkMode ? '#9ca3af' : '#64748b';
                            e.currentTarget.style.transform = 'scale(1)';
                        }}
                    >
                        <ExpandIcon />
                    </div>
                </div>
            </aside>
        );
    }
    return (
        <>
            <aside style={{
                width: 320,
                background: themeStyles?.isDarkMode ? 'rgba(15, 15, 30, 0.98)' : 'rgba(255, 255, 255, 0.9)',
                backdropFilter: 'blur(20px)',
                height: 'calc(100vh - 32px)',
                borderRadius: '20px',
                display: 'flex',
                flexDirection: 'column',
                boxShadow: themeStyles?.isDarkMode ? '8px 0 32px rgba(0, 0, 0, 0.7)' : '8px 0 32px rgba(37, 99, 235, 0.08)',
                transition: 'all 0.3s ease',
                border: themeStyles?.isDarkMode ? '1px solid rgba(80, 80, 120, 0.2)' : '1px solid rgba(255, 255, 255, 0.2)',
                position: 'relative',
                overflow: 'hidden',
                margin: '16px 0 16px 16px',
            }}>
                {/* 现代化装饰背景 */}
                <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: `
                        radial-gradient(circle at 20% 50%, rgba(37, 99, 235, 0.03) 0%, transparent 50%),
                        radial-gradient(circle at 80% 20%, rgba(124, 58, 237, 0.03) 0%, transparent 50%),
                        linear-gradient(135deg, rgba(37, 99, 235, 0.01) 0%, transparent 70%)
                    `,
                    pointerEvents: 'none',
                }} />
                
                {/* Top area - Logo and branding */}
                <div style={{
                    height: 80,
                    borderRadius: '20px 20px 0 0',
                    background: themeStyles?.isDarkMode ? 'rgba(20, 20, 36, 0.98)' : 'rgba(255, 255, 255, 0.95)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0 24px',
                    transition: 'all 0.3s ease',
                    backdropFilter: 'blur(20px)',
                    borderBottom: themeStyles?.isDarkMode ? '1px solid rgba(80, 80, 120, 0.2)' : '1px solid rgba(37, 99, 235, 0.1)',
                    position: 'relative',
                    zIndex: 2,
                }}>
                    {/* Left: Brand logo and welcome message */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        {/* Brand Logo */}
                        <div style={{
                            width: 40,
                            height: 40,
                            borderRadius: 10,
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            boxShadow: '0 4px 16px rgba(102, 126, 234, 0.3)',
                            transition: 'all 0.3s ease',
                            padding: 6,
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.transform = 'scale(1.05) rotate(5deg)';
                            e.currentTarget.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.4)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.transform = 'scale(1) rotate(0deg)';
                            e.currentTarget.style.boxShadow = '0 4px 16px rgba(102, 126, 234, 0.3)';
                        }}
                        >
                            <img 
                                src="/logo192.png" 
                                alt="Virtual Tutor Logo" 
                                style={{ 
                                    width: '100%', 
                                    height: '100%', 
                                    objectFit: 'contain' 
                                }} 
                            />
                        </div>
                        
                        {/* Brand name and tagline */}
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                            <div style={{
                                fontSize: 15,
                        fontWeight: 700,
                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                                backgroundClip: 'text',
                                letterSpacing: '0.5px',
                            }}>
                                Virtual Tutor
                    </div>
                            <div style={{
                                fontSize: 10,
                                color: '#64748b',
                                fontWeight: 500,
                            }}>
                                Your AI Learning Companion
                </div>
                </div>
                    </div>

                    {/* Right: Collapse button */}
                    <div 
                        style={{ 
                            cursor: 'pointer', 
                            width: 40,
                            height: 40,
                            borderRadius: '50%', 
                            transition: 'all 0.3s ease',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: '#64748b',
                        }} 
                        title="Collapse Sidebar" 
                        onClick={() => setOpen(false)}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.background = 'rgba(102, 126, 234, 0.1)';
                            e.currentTarget.style.color = '#667eea';
                            e.currentTarget.style.transform = 'scale(1.1)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'transparent';
                            e.currentTarget.style.color = '#64748b';
                            e.currentTarget.style.transform = 'scale(1)';
                        }}
                    >
                        <CollapseIcon />
                    </div>
                </div>

                {/* Subject Section Header */}
                <div style={{ 
                    padding: '20px 24px 16px 24px',
                    borderBottom: themeStyles?.isDarkMode ? '1px solid rgba(80, 80, 120, 0.2)' : '1px solid rgba(102, 126, 234, 0.1)',
                }}>
                    <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: 12,
                    }}>
                        <label style={{
                            fontSize: 14,
                            fontWeight: 700,
                            color: '#64748b',
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px',
                        }}>
                            Subject
                        </label>
                        <button
                            onClick={() => setShowAddSubject(!showAddSubject)}
                            style={{
                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                border: 'none',
                                borderRadius: 8,
                                padding: '6px 10px',
                                color: '#fff',
                                cursor: 'pointer',
                                fontSize: 11,
                                fontWeight: 600,
                                display: 'flex',
                                alignItems: 'center',
                                gap: 4,
                                transition: 'all 0.3s ease',
                                boxShadow: '0 2px 8px rgba(102, 126, 234, 0.2)',
                            }}
                            onMouseEnter={(e) => {
                                e.target.style.transform = 'scale(1.05)';
                                e.target.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.3)';
                            }}
                            onMouseLeave={(e) => {
                                e.target.style.transform = 'scale(1)';
                                e.target.style.boxShadow = '0 2px 8px rgba(102, 126, 234, 0.2)';
                            }}
                        >
                            <PlusIcon />
                            Add
                        </button>
                    </div>

                    {/* Add Subject Input */}
                    {showAddSubject && (
                        <div style={{
                            marginBottom: 12,
                            background: 'rgba(102, 126, 234, 0.05)',
                            padding: 12,
                            borderRadius: 10,
                            border: '1px solid rgba(102, 126, 234, 0.15)',
                        }}>
                    <input
                                type="text"
                                value={newSubjectInput}
                                onChange={(e) => setNewSubjectInput(e.target.value)}
                                onKeyPress={(e) => {
                                    if (e.key === 'Enter') {
                                        handleAddSubject();
                                    }
                                }}
                                placeholder="e.g., COMP9417"
                        style={{
                            width: '100%',
                            padding: '8px 12px',
                            borderRadius: 8,
                                    border: '1px solid rgba(102, 126, 234, 0.2)',
                                    fontSize: 13,
                                    marginBottom: 8,
                                    outline: 'none',
                                    fontFamily: 'inherit',
                                }}
                            />
                            <div style={{ display: 'flex', gap: 8 }}>
                                <button
                                    onClick={handleAddSubject}
                                    style={{
                                        flex: 1,
                                        padding: '6px 12px',
                                        background: '#667eea',
                                        color: '#fff',
                                        border: 'none',
                                        borderRadius: 6,
                                        fontSize: 12,
                                        fontWeight: 600,
                                        cursor: 'pointer',
                                        transition: 'all 0.2s ease',
                                    }}
                                    onMouseEnter={(e) => e.target.style.background = '#5568d3'}
                                    onMouseLeave={(e) => e.target.style.background = '#667eea'}
                                >
                                    Add Subject
                                </button>
                                <button
                                    onClick={() => {
                                        setShowAddSubject(false);
                                        setNewSubjectInput('');
                                    }}
                                    style={{
                                        padding: '6px 12px',
                                        background: 'transparent',
                                        color: '#64748b',
                                        border: '1px solid rgba(100, 116, 139, 0.2)',
                                        borderRadius: 6,
                                        fontSize: 12,
                                        fontWeight: 600,
                                        cursor: 'pointer',
                                        transition: 'all 0.2s ease',
                                    }}
                                    onMouseEnter={(e) => e.target.style.background = 'rgba(100, 116, 139, 0.05)'}
                                    onMouseLeave={(e) => e.target.style.background = 'transparent'}
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Subject List Scrollable Area */}
                <div 
                    className="subject-list-scrollbar"
                    style={{ 
                        display: 'flex', 
                        flexDirection: 'column', 
                        gap: 8,
                        maxHeight: 280,
                        overflowY: 'auto',
                        padding: '8px 24px 16px 24px',
                    }}
                >
                        {/* "All" option */}
                        <div
                            onClick={() => handleSubjectChange('All')}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 12,
                                padding: '12px 16px',
                                borderRadius: 12,
                                background: currentSubject === 'All'
                                    ? (themeStyles?.isDarkMode ? 'linear-gradient(135deg, #4c4c6d 0%, #3a3a5c 100%)' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)')
                                    : (themeStyles?.isDarkMode ? 'rgba(30, 30, 50, 0.6)' : 'rgba(255, 255, 255, 0.6)'),
                                border: currentSubject === 'All'
                                    ? (themeStyles?.isDarkMode ? '1px solid rgba(76, 76, 109, 0.4)' : '1px solid rgba(102, 126, 234, 0.3)')
                                    : (themeStyles?.isDarkMode ? '1px solid rgba(80, 80, 120, 0.3)' : '1px solid rgba(148, 163, 184, 0.2)'),
                                cursor: 'pointer',
                                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                boxShadow: currentSubject === 'All'
                                    ? (themeStyles?.isDarkMode ? '0 4px 16px rgba(76, 76, 109, 0.6)' : '0 4px 16px rgba(102, 126, 234, 0.25)')
                                    : (themeStyles?.isDarkMode ? '0 2px 6px rgba(0, 0, 0, 0.2)' : '0 2px 6px rgba(0, 0, 0, 0.04)'),
                            }}
                            onMouseEnter={(e) => {
                                if (currentSubject !== 'All') {
                                    e.currentTarget.style.background = themeStyles?.isDarkMode ? 'rgba(50, 50, 70, 0.8)' : 'rgba(102, 126, 234, 0.08)';
                                    e.currentTarget.style.transform = 'translateX(2px)';
                                    e.currentTarget.style.boxShadow = themeStyles?.isDarkMode ? '0 4px 12px rgba(76, 76, 109, 0.4)' : '0 4px 12px rgba(102, 126, 234, 0.12)';
                                }
                            }}
                            onMouseLeave={(e) => {
                                if (currentSubject !== 'All') {
                                    e.currentTarget.style.background = themeStyles?.isDarkMode ? 'rgba(30, 30, 50, 0.6)' : 'rgba(255, 255, 255, 0.6)';
                                    e.currentTarget.style.transform = 'translateX(0)';
                                    e.currentTarget.style.boxShadow = themeStyles?.isDarkMode ? '0 2px 6px rgba(0, 0, 0, 0.2)' : '0 2px 6px rgba(0, 0, 0, 0.04)';
                                }
                            }}
                        >
                            {/* Globe icon for "All" */}
                            <div style={{
                                width: 32,
                                height: 32,
                                borderRadius: 8,
                                background: currentSubject === 'All'
                                    ? 'rgba(255, 255, 255, 0.15)'
                                    : 'rgba(102, 126, 234, 0.1)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                transition: 'all 0.3s ease',
                            }}>
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <circle cx="12" cy="12" r="10" stroke={currentSubject === 'All' ? '#ffffff' : '#667eea'} strokeWidth="2"/>
                                    <path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z" stroke={currentSubject === 'All' ? '#ffffff' : '#667eea'} strokeWidth="2"/>
                                </svg>
                            </div>

                            <span style={{
                            fontSize: 14,
                                fontWeight: currentSubject === 'All' ? 600 : 500,
                                color: currentSubject === 'All' ? '#ffffff' : '#1e293b',
                                letterSpacing: '0.3px',
                                transition: 'all 0.3s ease',
                                flex: 1,
                            }}>
                                All Subjects
                            </span>
                        </div>

                        {/* User's subjects */}
                        {subjects.map((subject) => (
                            <div
                                key={subject}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 12,
                                    padding: '12px 16px',
                                    borderRadius: 12,
                                    background: currentSubject === subject
                                        ? (themeStyles?.isDarkMode ? 'linear-gradient(135deg, #4c4c6d 0%, #3a3a5c 100%)' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)')
                                        : (themeStyles?.isDarkMode ? 'rgba(30, 30, 50, 0.6)' : 'rgba(255, 255, 255, 0.6)'),
                                    border: currentSubject === subject
                                        ? (themeStyles?.isDarkMode ? '1px solid rgba(76, 76, 109, 0.4)' : '1px solid rgba(102, 126, 234, 0.3)')
                                        : (themeStyles?.isDarkMode ? '1px solid rgba(80, 80, 120, 0.3)' : '1px solid rgba(148, 163, 184, 0.2)'),
                                    cursor: 'pointer',
                                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                    boxShadow: currentSubject === subject
                                        ? (themeStyles?.isDarkMode ? '0 4px 16px rgba(76, 76, 109, 0.6)' : '0 4px 16px rgba(102, 126, 234, 0.25)')
                                        : (themeStyles?.isDarkMode ? '0 2px 6px rgba(0, 0, 0, 0.2)' : '0 2px 6px rgba(0, 0, 0, 0.04)'),
                                }}
                                onMouseEnter={(e) => {
                                    if (currentSubject !== subject) {
                                        e.currentTarget.style.background = themeStyles?.isDarkMode ? 'rgba(50, 50, 70, 0.8)' : 'rgba(102, 126, 234, 0.08)';
                                        e.currentTarget.style.transform = 'translateX(2px)';
                                        e.currentTarget.style.boxShadow = themeStyles?.isDarkMode ? '0 4px 12px rgba(76, 76, 109, 0.4)' : '0 4px 12px rgba(102, 126, 234, 0.12)';
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    if (currentSubject !== subject) {
                                        e.currentTarget.style.background = themeStyles?.isDarkMode ? 'rgba(30, 30, 50, 0.6)' : 'rgba(255, 255, 255, 0.6)';
                                        e.currentTarget.style.transform = 'translateX(0)';
                                        e.currentTarget.style.boxShadow = themeStyles?.isDarkMode ? '0 2px 6px rgba(0, 0, 0, 0.2)' : '0 2px 6px rgba(0, 0, 0, 0.04)';
                                    }
                                }}
                            >
                                {/* Book icon */}
                                <div
                                    onClick={() => handleSubjectChange(subject)}
                                    style={{
                                        width: 32,
                                        height: 32,
                                        borderRadius: 8,
                                        background: currentSubject === subject
                                            ? 'rgba(255, 255, 255, 0.15)'
                                            : 'rgba(102, 126, 234, 0.1)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        transition: 'all 0.3s ease',
                                    }}
                                >
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path 
                                            d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2zm20 0h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" 
                                            fill={currentSubject === subject ? '#ffffff' : '#667eea'}
                                        />
                                    </svg>
                                </div>

                                {/* Subject name */}
                                <span
                                    onClick={() => handleSubjectChange(subject)}
                                    style={{
                                        fontSize: 14,
                                        fontWeight: currentSubject === subject ? 600 : 500,
                                        color: currentSubject === subject ? '#ffffff' : '#1e293b',
                                        letterSpacing: '0.3px',
                                        transition: 'all 0.3s ease',
                                        flex: 1,
                                    }}
                                >
                                    {subject}
                                </span>

                                {/* Delete button */}
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleDeleteSubject(subject);
                                    }}
                                    style={{
                                        background: 'transparent',
                                        border: 'none',
                                        cursor: 'pointer',
                                        padding: 6,
                                        borderRadius: 6,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        color: currentSubject === subject ? '#ffffff' : '#ef4444',
                                        opacity: 0.7,
                                        transition: 'all 0.2s ease',
                                    }}
                                    onMouseEnter={(e) => {
                                        e.target.style.opacity = '1';
                                        e.target.style.background = currentSubject === subject 
                                            ? 'rgba(255, 255, 255, 0.15)' 
                                            : 'rgba(239, 68, 68, 0.1)';
                                    }}
                                    onMouseLeave={(e) => {
                                        e.target.style.opacity = '0.7';
                                        e.target.style.background = 'transparent';
                                    }}
                                >
                                    <TrashIcon />
                                </button>
                            </div>
                        ))}
                </div>

                {/* Tab area - Pill style */}
                <div style={{ padding: '24px 24px 0 24px' }}>
                    <div style={{
                        display: 'flex',
                        flexDirection: 'row',
                        background: themeStyles?.isDarkMode ? 'rgba(30, 30, 50, 0.8)' : 'rgba(241, 245, 249, 0.8)',
                        borderRadius: 20,
                        padding: 4,
                        gap: 4,
                    }}>
                        <div
                            onClick={() => setTab('chats')}
                            style={{
                                flex: 1,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                padding: '10px 16px',
                                borderRadius: 16,
                                background: tab === 'chats' 
                                    ? (themeStyles?.isDarkMode ? 'rgba(50, 50, 70, 0.9)' : '#ffffff')
                                    : 'transparent',
                                cursor: 'pointer',
                                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                boxShadow: tab === 'chats' 
                                    ? (themeStyles?.isDarkMode ? '0 2px 8px rgba(76, 76, 109, 0.5)' : '0 2px 8px rgba(0, 0, 0, 0.08)')
                                    : 'none',
                            }}
                        >
                            <span style={{
                                fontSize: 13,
                                fontWeight: tab === 'chats' ? 700 : 500,
                                color: tab === 'chats' ? (themeStyles?.isDarkMode ? '#e5e7eb' : '#1e293b') : (themeStyles?.isDarkMode ? '#9ca3af' : '#64748b'),
                                textTransform: 'uppercase',
                                letterSpacing: '0.5px',
                                transition: 'all 0.3s ease',
                            }}>
                                CHATS
                            </span>
                            {filteredSessions.length > 0 && (
                                <span style={{
                                    marginLeft: 8,
                                    background: tab === 'chats' 
                                        ? (themeStyles?.isDarkMode ? 'rgba(100, 100, 140, 0.3)' : 'rgba(102, 126, 234, 0.1)')
                                        : (themeStyles?.isDarkMode ? 'rgba(80, 80, 100, 0.2)' : 'rgba(100, 116, 139, 0.1)'),
                                    color: tab === 'chats' ? (themeStyles?.isDarkMode ? '#c7d2fe' : '#667eea') : (themeStyles?.isDarkMode ? '#9ca3af' : '#64748b'),
                                    borderRadius: 8,
                                    fontSize: 10,
                                    fontWeight: 700,
                                    padding: '3px 7px',
                                    minWidth: 20,
                                    textAlign: 'center',
                                    transition: 'all 0.3s ease',
                                }}>
                                    {filteredSessions.length}
                                </span>
                            )}
                        </div>
                        <div
                            onClick={() => setTab('saved')}
                            style={{
                                flex: 1,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                padding: '10px 16px',
                                borderRadius: 16,
                                background: tab === 'saved' 
                                    ? (themeStyles?.isDarkMode ? 'rgba(50, 50, 70, 0.9)' : '#ffffff')
                                    : 'transparent',
                                cursor: 'pointer',
                                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                boxShadow: tab === 'saved' 
                                    ? (themeStyles?.isDarkMode ? '0 2px 8px rgba(76, 76, 109, 0.5)' : '0 2px 8px rgba(0, 0, 0, 0.08)')
                                    : 'none',
                            }}
                        >
                            <span style={{
                                fontSize: 13,
                                fontWeight: tab === 'saved' ? 700 : 500,
                                color: tab === 'saved' ? (themeStyles?.isDarkMode ? '#e5e7eb' : '#1e293b') : (themeStyles?.isDarkMode ? '#9ca3af' : '#64748b'),
                                textTransform: 'uppercase',
                                letterSpacing: '0.5px',
                                transition: 'all 0.3s ease',
                            }}>
                                SAVED
                            </span>
                            {favoriteSessions.length > 0 && (
                                <span style={{
                                    marginLeft: 8,
                                    background: tab === 'saved' 
                                        ? (themeStyles?.isDarkMode ? 'rgba(100, 100, 140, 0.3)' : 'rgba(102, 126, 234, 0.1)')
                                        : (themeStyles?.isDarkMode ? 'rgba(80, 80, 100, 0.2)' : 'rgba(100, 116, 139, 0.1)'),
                                    color: tab === 'saved' ? (themeStyles?.isDarkMode ? '#c7d2fe' : '#667eea') : (themeStyles?.isDarkMode ? '#9ca3af' : '#64748b'),
                                    borderRadius: 8,
                                    fontSize: 10,
                                    fontWeight: 700,
                                    padding: '3px 7px',
                                    minWidth: 20,
                                    textAlign: 'center',
                                    transition: 'all 0.3s ease',
                                }}>
                                    {favoriteSessions.length}
                                </span>
                            )}
                        </div>
                    </div>
                </div>
                {/* 优化的搜索框 */}
                <div style={{ padding: '20px 24px' }}>
                    <div style={{ 
                        position: 'relative',
                        background: themeStyles?.isDarkMode ? 'rgba(30, 30, 50, 0.9)' : 'rgba(255, 255, 255, 0.95)',
                        borderRadius: 14,
                        border: themeStyles?.isDarkMode ? '2px solid rgba(80, 80, 120, 0.3)' : '2px solid rgba(102, 126, 234, 0.15)',
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                        backdropFilter: 'blur(10px)',
                        boxShadow: themeStyles?.isDarkMode ? '0 2px 8px rgba(0, 0, 0, 0.3)' : '0 2px 8px rgba(102, 126, 234, 0.08)',
                    }}>
                        <div style={{ 
                            position: 'absolute', 
                            left: 14, 
                            top: '50%', 
                            transform: 'translateY(-50%)',
                            zIndex: 1,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            pointerEvents: 'none',
                        }}>
                            <SearchIcon />
                        </div>
                        <input
                            placeholder="Search conversations..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '13px 16px 13px 42px',
                                borderRadius: 14,
                                border: 'none',
                                fontSize: 14,
                                fontWeight: 500,
                                background: 'transparent',
                                color: themeStyles?.isDarkMode ? '#e5e7eb' : '#1e293b',
                                outline: 'none',
                                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                fontFamily: 'inherit',
                            }}
                            onFocus={(e) => {
                                e.target.parentElement.style.border = themeStyles?.isDarkMode ? '2px solid #6b7280' : '2px solid #667eea';
                                e.target.parentElement.style.boxShadow = themeStyles?.isDarkMode ? '0 4px 20px rgba(107, 114, 128, 0.3)' : '0 4px 20px rgba(102, 126, 234, 0.2)';
                                e.target.parentElement.style.background = themeStyles?.isDarkMode ? 'rgba(40, 40, 60, 1)' : 'rgba(255, 255, 255, 1)';
                                e.target.parentElement.style.transform = 'translateY(-1px)';
                            }}
                            onBlur={(e) => {
                                e.target.parentElement.style.border = themeStyles?.isDarkMode ? '2px solid rgba(80, 80, 120, 0.3)' : '2px solid rgba(102, 126, 234, 0.15)';
                                e.target.parentElement.style.boxShadow = themeStyles?.isDarkMode ? '0 2px 8px rgba(0, 0, 0, 0.3)' : '0 2px 8px rgba(102, 126, 234, 0.08)';
                                e.target.parentElement.style.background = themeStyles?.isDarkMode ? 'rgba(30, 30, 50, 0.9)' : 'rgba(255, 255, 255, 0.95)';
                                e.target.parentElement.style.transform = 'translateY(0)';
                            }}
                        />
                    </div>
                </div>
                {/* Conversation list grouping */}
                <div style={{ flex: 1, overflowY: 'auto', padding: '0 24px' }}>
                    {tab === 'chats' && chatGroupsData.map(g => (
                        g.chats.length > 0 && (
                            <ChatGroup
                                key={g.group}
                                title={g.group}
                                chats={g.chats.map(s => ({
                                    id: s.id,
                                    title: s.title,
                                    subtitle: s.updated_at ? new Date(s.updated_at).toLocaleString() : '',
                                    isFavorite: s.is_favorite
                                }))}
                                selectedId={selectedChatId}
                                onSelect={onSelectChat}
                                onDelete={handleDeleteChat}
                                onToggleFavorite={(id) => handleToggleFavorite(id, sessions.find(s => s.id === id)?.is_favorite)}
                                isSavedTab={false}
                                themeStyles={themeStyles}
                            />
                        )
                    ))}
                    {tab === 'saved' && (
                        favoriteSessions.length > 0 ? (
                            <ChatGroup
                                title="Favorites"
                                chats={favoriteSessions.map(s => ({
                                    id: s.id,
                                    title: s.title,
                                    subtitle: s.updated_at ? new Date(s.updated_at).toLocaleString() : '',
                                    isFavorite: true
                                }))}
                                selectedId={selectedChatId}
                                onSelect={onSelectChat}
                                onToggleFavorite={(id) => handleToggleFavorite(id, true)}
                                isSavedTab={true}
                                themeStyles={themeStyles}
                            />
                        ) : (
                            <div style={{ color: themeStyles?.placeholderColor || '#aaa', textAlign: 'center', marginTop: 40 }}>No favorites yet</div>
                        )
                    )}
                </div>
                {/* 现代化底部功能区 */}
                <div style={{ 
                    padding: '16px', 
                            display: 'flex',
                    flexDirection: 'row', 
                            alignItems: 'center',
                            justifyContent: 'center',
                    gap: 24,
                    marginTop: 'auto',
                    borderTop: themeStyles?.isDarkMode ? '1px solid rgba(80, 80, 120, 0.2)' : '1px solid rgba(37, 99, 235, 0.1)',
                    background: themeStyles?.isDarkMode ? 'rgba(15, 15, 30, 0.98)' : 'rgba(255, 255, 255, 0.9)',
                    backdropFilter: 'blur(20px)',
                    position: 'relative',
                    zIndex: 2,
                    borderRadius: '0 0 20px 20px',
                }}>
                    {/* 主题切换按钮 */}
                    <div
                        style={{
                            position: 'relative',
                            padding: 8,
                            cursor: 'pointer',
                            transition: 'all 0.3s ease',
                            color: '#64748b',
                        }}
                        title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
                        onClick={toggleTheme}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.color = '#3b82f6';
                            e.currentTarget.style.transform = 'scale(1.1)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.color = '#64748b';
                            e.currentTarget.style.transform = 'scale(1)';
                        }}
                    >
                            {isDarkMode ? <SunIcon /> : <MoonIcon />}
                    </div>

                    {/* 用户资料按钮 */}
                    <div
                        style={{
                            position: 'relative',
                            padding: 8,
                            cursor: 'pointer',
                            transition: 'all 0.3s ease',
                            color: '#64748b',
                        }}
                        title="User Profile"
                        onClick={() => setShowUserProfile(true)}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.color = '#3b82f6';
                            e.currentTarget.style.transform = 'scale(1.1)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.color = '#64748b';
                            e.currentTarget.style.transform = 'scale(1)';
                        }}
                    >
                        <UserIcon />
                    </div>
                </div>
            </aside>

            {/* Modal */}
            <UserProfileModal isOpen={showUserProfile} onClose={() => setShowUserProfile(false)} onLogout={onLogout} />
        </>
    );
}

export default HomeSidebar; 