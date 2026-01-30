import React, { useState, useRef } from 'react';
import { IconButton } from '@mui/material';
import { Brightness4, Brightness7, Person, Settings, School, Psychology, Science, Notifications, SmartToy } from '@mui/icons-material';
import userService from '../../services/userService';
import authService from '../../services/authService';
import config from '../../config';

// SVG图标组件（与HomeSidebar一致）
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

const BASE_URL = config.BACKEND_URL;

const menuItems = [
    { key: 'avatar', label: 'Avatar', icon: <SmartToy style={{ fontSize: 20 }} /> },
    { key: 'user', label: 'User', icon: <Person style={{ fontSize: 20 }} /> },
    { key: 'model', label: 'Model', icon: <Psychology style={{ fontSize: 20 }} /> },
    { key: 'knowledge', label: 'Knowledge background', icon: <Science style={{ fontSize: 20 }} /> },
    { key: 'logs', label: 'User Action Logs', icon: <Notifications style={{ fontSize: 20 }} /> }
];

// User profile editing modal component
function UserProfileModal({ isOpen, onClose, onLogout }) {
    const [userInfo, setUserInfo] = useState({
        name: '',
        full_name: '',
        bio: ''
    });

    const [passwordInfo, setPasswordInfo] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
        code: '' // verification code field
    });
    const [sendingCode, setSendingCode] = useState(false);
    const [codeTimer, setCodeTimer] = useState(0);

    const [uploadedAvatar, setUploadedAvatar] = useState(null);
    const [activeView, setActiveView] = useState('profile'); // 'profile' or 'password'
    const fileInputRef = useRef();

    React.useEffect(() => {
        if (isOpen) {
            // 直接從 localStorage 取用戶信息
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

    // Send verification code
    const handleSendCode = async () => {
        if (sendingCode || codeTimer > 0) return;
        // Get email from localStorage
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
    // Countdown effect
    React.useEffect(() => {
        if (codeTimer > 0) {
            const timer = setTimeout(() => setCodeTimer(codeTimer - 1), 1000);
            return () => clearTimeout(timer);
        }
    }, [codeTimer]);

    if (!isOpen) return null;

    const handleSave = async () => {
        if (activeView === 'profile') {
            // 保存用戶信息
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
                alert('Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)!');
                return;
            }
            if (passwordInfo.newPassword !== passwordInfo.confirmPassword) {
                alert('New password and confirm password do not match!');
                return;
            }
            // Call new API
            const res = await authService.updatePasswordWithCode({
                code: passwordInfo.code,
                new_password: passwordInfo.newPassword
            });
            if (res.success) {
                alert('Password changed successfully! You will be logged out automatically.');
                // Clear password form
                setPasswordInfo({ currentPassword: '', newPassword: '', confirmPassword: '', code: '' });
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
            // 上傳頭像
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
        setPasswordInfo({ currentPassword: '', newPassword: '', confirmPassword: '', code: '' });
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
                        {activeView === 'profile' ? 'Admin Profile' : 'Change Password'}
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

function AdminSidebar({ selectedMenu, onSelectMenu, onLogout, isDarkMode, onThemeToggle }) {
    const [open, setOpen] = useState(true);
    const [showUserProfile, setShowUserProfile] = useState(false);
    const [logoHovered, setLogoHovered] = useState(false);
    const [collapseHovered, setCollapseHovered] = useState(false);
    const [expandHovered, setExpandHovered] = useState(false);

    // 当折叠栏收起或展开时，重置所有hover状态
    React.useEffect(() => {
        setLogoHovered(false);
        setCollapseHovered(false);
        setExpandHovered(false);
    }, [open]);

    // 统一的主题样式配置
    const themeStyles = {
        sidebarBg: isDarkMode ? 'rgba(15, 15, 25, 0.95)' : 'rgba(255, 255, 255, 0.95)',
        sidebarHeaderBackground: isDarkMode ? 'rgba(20, 20, 36, 0.98)' : 'rgba(255, 255, 255, 0.98)',
        sidebarHeaderColor: isDarkMode ? '#e5e7eb' : '#667eea',
        sidebarActive: isDarkMode ? 'linear-gradient(135deg, #4c4c6d 0%, #3a3a5c 100%)' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        sidebarActiveText: '#ffffff',
        sidebarText: isDarkMode ? '#e5e7eb' : '#1e293b',
        shadow: isDarkMode ? '0 8px 32px rgba(0, 0, 0, 0.7)' : '0 8px 32px rgba(37, 99, 235, 0.08)',
        buttonBackground: isDarkMode ? 'rgba(30, 30, 50, 0.9)' : 'rgba(255, 255, 255, 0.95)',
    };

    if (!open) {
        // Collapsed state - 与 HomeSidebar 保持一致，应用主题样式
        return (
            <aside style={{
                width: 56,
                background: themeStyles.sidebarBg,
                backdropFilter: 'blur(20px)',
                height: '100vh',
                borderRadius: '24px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                boxShadow: themeStyles.shadow,
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                margin: '16px 0 16px 16px',
                border: isDarkMode ? '1px solid rgba(80, 80, 120, 0.3)' : '1px solid rgba(0, 0, 0, 0.05)',
            }}>
                <div style={{
                    height: 80,
                    borderRadius: '24px 24px 0 0',
                    background: themeStyles.sidebarHeaderBackground,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '100%',
                    borderBottom: isDarkMode ? '1px solid rgba(80, 80, 120, 0.2)' : '1px solid rgba(0, 0, 0, 0.05)',
                    transition: 'all 0.3s ease',
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
                            color: expandHovered ? '#667eea' : (isDarkMode ? '#94a3b8' : '#64748b'),
                            background: expandHovered ? 'rgba(102, 126, 234, 0.1)' : 'transparent',
                            transform: expandHovered ? 'scale(1.1)' : 'scale(1)',
                        }}
                        onClick={() => setOpen(true)}
                        title="Expand Sidebar"
                        onMouseEnter={() => setExpandHovered(true)}
                        onMouseLeave={() => setExpandHovered(false)}
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
                width: 294,
                background: themeStyles.sidebarBg,
                backdropFilter: 'blur(20px)',
                height: '100vh',
                borderRadius: '0',
                display: 'flex',
                flexDirection: 'column',
                boxShadow: themeStyles.shadow,
                transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
                border: isDarkMode ? '1px solid rgba(80, 80, 120, 0.3)' : '1px solid rgba(255, 255, 255, 0.2)',
            }}>
                {/* Top area - Logo and branding (与 HomeSidebar 保持一致) */}
                <div style={{
                    height: 80,
                    borderRadius: '20px 20px 0 0',
                    background: themeStyles.sidebarHeaderBackground,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0 24px',
                    transition: 'all 0.3s ease',
                    backdropFilter: 'blur(20px)',
                    borderBottom: isDarkMode ? '1px solid rgba(80, 80, 120, 0.2)' : '1px solid rgba(37, 99, 235, 0.1)',
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
                            boxShadow: logoHovered ? '0 6px 20px rgba(102, 126, 234, 0.4)' : '0 4px 16px rgba(102, 126, 234, 0.3)',
                            transition: 'all 0.3s ease',
                            padding: 6,
                            transform: logoHovered ? 'scale(1.05) rotate(5deg)' : 'scale(1) rotate(0deg)',
                            cursor: 'pointer',
                        }}
                        onMouseEnter={() => setLogoHovered(true)}
                        onMouseLeave={() => setLogoHovered(false)}
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
                                Admin Panel
                            </div>
                            <div style={{
                                fontSize: 10,
                                color: isDarkMode ? '#94a3b8' : '#64748b',
                                fontWeight: 500,
                                transition: 'color 0.3s ease',
                            }}>
                                System Management
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
                            color: collapseHovered ? '#667eea' : (isDarkMode ? '#94a3b8' : '#64748b'),
                            background: collapseHovered ? 'rgba(102, 126, 234, 0.1)' : 'transparent',
                            transform: collapseHovered ? 'scale(1.1)' : 'scale(1)',
                        }} 
                        title="Collapse Sidebar" 
                        onClick={() => setOpen(false)}
                        onMouseEnter={() => setCollapseHovered(true)}
                        onMouseLeave={() => setCollapseHovered(false)}
                    >
                        <CollapseIcon />
                    </div>
                </div>

                {/* Menu items */}
                <div style={{ flex: 1, padding: '24px 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {menuItems.map(item => (
                        <div
                            key={item.key}
                            onClick={() => onSelectMenu(item.key)}
                            style={{
                                padding: '14px 20px',
                                background: selectedMenu === item.key ? themeStyles.sidebarActive : 'transparent',
                                color: selectedMenu === item.key ? themeStyles.sidebarActiveText : themeStyles.sidebarText,
                                fontWeight: selectedMenu === item.key ? 700 : 500,
                                fontSize: 16,
                                borderRadius: selectedMenu === item.key ? '12px' : '12px',
                                cursor: 'pointer',
                                transition: 'all 0.3s ease',
                                display: 'flex',
                                alignItems: 'center',
                                gap: 12,
                                boxShadow: selectedMenu === item.key 
                                    ? (isDarkMode ? '0 4px 16px rgba(76, 76, 109, 0.5)' : '0 4px 16px rgba(102, 126, 234, 0.25)') 
                                    : 'none',
                            }}
                            onMouseEnter={(e) => {
                                if (selectedMenu !== item.key) {
                                    e.currentTarget.style.background = isDarkMode ? 'rgba(40, 40, 60, 0.6)' : 'rgba(237, 242, 247, 0.9)';
                                }
                            }}
                            onMouseLeave={(e) => {
                                if (selectedMenu !== item.key) {
                                    e.currentTarget.style.background = 'transparent';
                                }
                            }}
                        >
                            <span style={{
                                color: selectedMenu === item.key ? themeStyles.sidebarActiveText : themeStyles.sidebarText,
                                display: 'flex',
                                alignItems: 'center',
                                transition: 'color 0.3s ease',
                            }}>
                                {item.icon}
                            </span>
                            {item.label}
                        </div>
                    ))}
                </div>

                {/* 底部功能区 - 与 HomeSidebar 保持一致的简洁样式 */}
                <div style={{ 
                    padding: '16px', 
                    display: 'flex',
                    flexDirection: 'row', 
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 24,
                    marginTop: 'auto',
                    borderTop: isDarkMode ? '1px solid rgba(80, 80, 120, 0.2)' : '1px solid rgba(37, 99, 235, 0.1)',
                    background: isDarkMode ? 'rgba(15, 15, 30, 0.98)' : 'rgba(255, 255, 255, 0.9)',
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
                        onClick={onThemeToggle}
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

export default AdminSidebar; 