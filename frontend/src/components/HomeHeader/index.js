import React, { useState, useRef, useEffect } from 'react';
import notificationService from '../../services/notificationService';
import config from '../../config';

const BASE_URL = config.BACKEND_URL;
const DEFAULT_AVATAR = 'https://cdn.jsdelivr.net/gh/edent/SuperTinyIcons/images/svg/user.svg';

// Modern icon components
const BellIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" fill="none" stroke="currentColor" strokeWidth="2"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0" fill="none" stroke="currentColor" strokeWidth="2"/>
    </svg>
);

const LogoutIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" fill="none" stroke="currentColor" strokeWidth="2"/>
        <polyline points="16,17 21,12 16,7" fill="none" stroke="currentColor" strokeWidth="2"/>
        <line x1="21" y1="12" x2="9" y2="12" fill="none" stroke="currentColor" strokeWidth="2"/>
    </svg>
);

const CheckIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <polyline points="20,6 9,17 4,12" fill="none" stroke="currentColor" strokeWidth="2"/>
    </svg>
);

function HomeHeader({ onLogout, themeStyles }) {
    const [showMenu, setShowMenu] = useState(false);
    const [imgError, setImgError] = useState(false);
    const [showNotifications, setShowNotifications] = useState(false);
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [loadingNotifications, setLoadingNotifications] = useState(false);
    const menuRef = useRef(null);
    const notificationRef = useRef(null);
    
    const handleLogoutClick = () => {
        if (window.confirm('Are you sure you want to log out?')) {
            onLogout();
        }
        setShowMenu(false);
    };

    // Fetch notifications list
    const fetchNotifications = async () => {
        setLoadingNotifications(true);
        try {
            const result = await notificationService.getNotifications({ page: 1, limit: 20 });
            if (result.success && result.data) {
                setNotifications(result.data.notifications || []);
                setUnreadCount(result.data.unread_count || 0);
            }
        } catch (error) {
            console.error('Failed to fetch notifications:', error);
        } finally {
            setLoadingNotifications(false);
        }
    };

    // Mark notification as read
    const handleMarkAsRead = async (notificationId) => {
        try {
            const result = await notificationService.markAsRead(notificationId);
            if (result.success) {
                // Update local state
                setNotifications(prev =>
                    prev.map(n =>
                        n.id === notificationId ? { ...n, is_read: true } : n
                    )
                );
                setUnreadCount(prev => Math.max(0, prev - 1));
            }
        } catch (error) {
            console.error('Failed to mark notification as read:', error);
        }
    };

    // Handle notification icon click
    const handleNotificationClick = () => {
        setShowNotifications(!showNotifications);
        if (!showNotifications && notifications.length === 0) {
            fetchNotifications();
        }
    };

    // Load unread count on initial mount
    useEffect(() => {
        const fetchUnreadCount = async () => {
            const result = await notificationService.getUnreadCount();
            if (result.success) {
                setUnreadCount(result.count);
            }
        };
        fetchUnreadCount();

        // Refresh unread count every minute
        const interval = setInterval(fetchUnreadCount, 60000);
        return () => clearInterval(interval);
    }, []);
    
    // Close menu and notifications when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setShowMenu(false);
            }
            if (notificationRef.current && !notificationRef.current.contains(event.target)) {
                setShowNotifications(false);
            }
        };
        
        if (showMenu || showNotifications) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [showMenu, showNotifications]);

    // Get user information
    let user = null;
    const userStr = localStorage.getItem('user');
    if (userStr) {
        user = JSON.parse(userStr);
    }
    
    const avatarSrc = imgError || !user?.avatar ? DEFAULT_AVATAR : (user.avatar.startsWith('http') ? user.avatar : `${BASE_URL}${user.avatar}`);

    return (
        <header style={{ 
            height: 80, 
            background: themeStyles?.isDarkMode ? 'rgba(15, 15, 30, 0.98)' : 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(20px)',
            borderBottom: themeStyles?.isDarkMode ? '1px solid rgba(80, 80, 120, 0.2)' : '1px solid rgba(145, 70, 255, 0.1)', 
            display: 'flex', 
            alignItems: 'center', 
            padding: '0 32px', 
            justifyContent: 'flex-end', 
            position: 'relative',
            boxShadow: themeStyles?.isDarkMode ? '0 2px 16px rgba(0, 0, 0, 0.3)' : '0 2px 16px rgba(0, 0, 0, 0.04)',
            zIndex: 100,
            borderRadius: '20px 20px 0 0',
        }}>
            {/* Right: Notifications and user area */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
                {/* Notifications */}
                <div 
                    ref={notificationRef}
                    style={{ position: 'relative' }}
                >
                    <div 
                        onClick={handleNotificationClick}
                        style={{
                            position: 'relative',
                            padding: 8,
                            cursor: 'pointer',
                            transition: 'all 0.3s ease',
                            color: showNotifications ? '#3b82f6' : '#64748b',
                        }} 
                        title="Notifications"
                        onMouseEnter={(e) => {
                            e.currentTarget.style.color = '#3b82f6';
                            e.currentTarget.style.transform = 'scale(1.1)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.color = showNotifications ? '#3b82f6' : '#64748b';
                            e.currentTarget.style.transform = 'scale(1)';
                        }}
                    >
                        <BellIcon />
                        {/* Unread count badge */}
                        {unreadCount > 0 && (
                            <div style={{
                                position: 'absolute',
                                top: 6,
                                right: 6,
                                minWidth: 18,
                                height: 18,
                                borderRadius: '9px',
                                background: '#ef4444',
                                border: '2px solid white',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: 10,
                                fontWeight: 700,
                                color: 'white',
                                padding: '0 4px',
                            }}>
                                {unreadCount > 99 ? '99+' : unreadCount}
                            </div>
                        )}
                    </div>

                    {/* Notification dropdown list */}
                    {showNotifications && (
                        <div
                            style={{
                                position: 'absolute',
                                top: 'calc(100% + 8px)',
                                right: 0,
                                background: 'rgba(255, 255, 255, 0.98)',
                                backdropFilter: 'blur(20px)',
                                border: '1px solid rgba(102, 126, 234, 0.15)',
                                borderRadius: 12,
                                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
                                width: 400,
                                maxHeight: 500,
                                overflow: 'hidden',
                                zIndex: 1000,
                                animation: 'slideIn 0.2s ease-out',
                                display: 'flex',
                                flexDirection: 'column',
                            }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            {/* Notification header */}
                            <div style={{
                                padding: '16px 20px',
                                borderBottom: '1px solid rgba(102, 126, 234, 0.1)',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                            }}>
                                <h3 style={{
                                    margin: 0,
                                    fontSize: 16,
                                    fontWeight: 700,
                                    color: '#1e293b',
                                }}>
                                    Notifications
                                </h3>
                                {unreadCount > 0 && (
                                    <span style={{
                                        fontSize: 12,
                                        color: '#64748b',
                                        background: 'rgba(59, 130, 246, 0.1)',
                                        padding: '4px 8px',
                                        borderRadius: 12,
                                        fontWeight: 600,
                                    }}>
                                        {unreadCount} unread
                                    </span>
                                )}
                            </div>

                            {/* Notification list */}
                            <div style={{
                                flex: 1,
                                overflowY: 'auto',
                                maxHeight: 400,
                            }}>
                                {loadingNotifications ? (
                                    <div style={{
                                        padding: 40,
                                        textAlign: 'center',
                                        color: '#94a3b8',
                                    }}>
                                        <div style={{
                                            width: 30,
                                            height: 30,
                                            border: '3px solid #f3f4f6',
                                            borderTop: '3px solid #3b82f6',
                                            borderRadius: '50%',
                                            animation: 'spin 1s linear infinite',
                                            margin: '0 auto 12px',
                                        }} />
                                        Loading...
                                    </div>
                                ) : notifications.length === 0 ? (
                                    <div style={{
                                        padding: 40,
                                        textAlign: 'center',
                                        color: '#94a3b8',
                                    }}>
                                        <div style={{ fontSize: 48, marginBottom: 12 }}>🔔</div>
                                        <div style={{ fontSize: 14, fontWeight: 600 }}>No notifications</div>
                                    </div>
                                ) : (
                                    notifications.map((notification) => (
                                        <div
                                            key={notification.id}
                                            style={{
                                                padding: '16px 20px',
                                                borderBottom: '1px solid rgba(102, 126, 234, 0.08)',
                                                background: notification.is_read ? 'transparent' : 'rgba(59, 130, 246, 0.04)',
                                                cursor: 'pointer',
                                                transition: 'all 0.2s ease',
                                            }}
                                            onMouseEnter={(e) => {
                                                e.currentTarget.style.background = 'rgba(102, 126, 234, 0.08)';
                                            }}
                                            onMouseLeave={(e) => {
                                                e.currentTarget.style.background = notification.is_read ? 'transparent' : 'rgba(59, 130, 246, 0.04)';
                                            }}
                                            onClick={() => !notification.is_read && handleMarkAsRead(notification.id)}
                                        >
                                            <div style={{
                                                display: 'flex',
                                                justifyContent: 'space-between',
                                                alignItems: 'flex-start',
                                                gap: 12,
                                            }}>
                                                <div style={{ flex: 1 }}>
                                                    <div style={{
                                                        fontSize: 14,
                                                        fontWeight: notification.is_read ? 500 : 700,
                                                        color: '#1e293b',
                                                        marginBottom: 6,
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        gap: 8,
                                                    }}>
                                                        {notification.title}
                                                        {!notification.is_read && (
                                                            <span style={{
                                                                width: 8,
                                                                height: 8,
                                                                borderRadius: '50%',
                                                                background: '#3b82f6',
                                                                flexShrink: 0,
                                                            }} />
                                                        )}
                                                    </div>
                                                    <div style={{
                                                        fontSize: 13,
                                                        color: '#64748b',
                                                        lineHeight: 1.5,
                                                        marginBottom: 8,
                                                    }}>
                                                        {notification.message}
                                                    </div>
                                                    <div style={{
                                                        fontSize: 11,
                                                        color: '#94a3b8',
                                                    }}>
                                                        {new Date(notification.created_at).toLocaleString('zh-CN')}
                                                    </div>
                                                </div>
                                                {!notification.is_read && (
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleMarkAsRead(notification.id);
                                                        }}
                                                        style={{
                                                            padding: '6px 10px',
                                                            background: 'rgba(59, 130, 246, 0.1)',
                                                            border: 'none',
                                                            borderRadius: 6,
                                                            color: '#3b82f6',
                                                            fontSize: 11,
                                                            fontWeight: 600,
                                                            cursor: 'pointer',
                                                            transition: 'all 0.2s ease',
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            gap: 4,
                                                            flexShrink: 0,
                                                        }}
                                                        onMouseEnter={(e) => {
                                                            e.target.style.background = 'rgba(59, 130, 246, 0.2)';
                                                        }}
                                                        onMouseLeave={(e) => {
                                                            e.target.style.background = 'rgba(59, 130, 246, 0.1)';
                                                        }}
                                                        title="Mark as read"
                                                    >
                                                        <CheckIcon />
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* User information area - ChatGPT style */}
                <div
                    ref={menuRef}
                style={{ position: 'relative', display: 'inline-block' }}
                >
                    <div 
                        onClick={() => setShowMenu(!showMenu)}
                        style={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: 12, 
                            cursor: 'pointer',
                            padding: '8px 12px',
                            borderRadius: 12,
                            transition: 'all 0.2s ease',
                            background: 'transparent',
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.background = 'rgba(102, 126, 234, 0.08)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'transparent';
                        }}
                    >
                        {/* Avatar on the left */}
                <img
                    src={avatarSrc}
                    alt="User avatar"
                            style={{ 
                                width: 40, 
                                height: 40, 
                                borderRadius: '50%', 
                                objectFit: 'cover', 
                                border: '2px solid rgba(102, 126, 234, 0.2)', 
                                transition: 'all 0.3s ease', 
                                background: '#f8fafc',
                                flexShrink: 0,
                            }}
                    onError={() => setImgError(true)}
                />
                        
                        {/* User info on the right */}
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                            <div style={{ 
                                fontSize: 14, 
                                fontWeight: 600, 
                                color: '#1e293b',
                                lineHeight: 1.2,
                            }}>
                                {user?.full_name || user?.username || 'User'}
                            </div>
                            <div style={{ 
                                fontSize: 12, 
                                color: '#94a3b8',
                                lineHeight: 1.2,
                                marginTop: 2,
                            }}>
                                {user?.role === 'tutor' ? 'Tutor' : 'Student'}
                            </div>
                        </div>
                    </div>
                    
                    {/* Dropdown menu - Click to display */}
                {showMenu && (
                        <div 
                            className="user-menu"
                            style={{
                        position: 'absolute',
                                top: 'calc(100% + 8px)',
                        right: 0,
                                background: 'rgba(255, 255, 255, 0.98)',
                                backdropFilter: 'blur(20px)',
                                border: '1px solid rgba(102, 126, 234, 0.15)',
                                borderRadius: 12,
                                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
                                minWidth: 200,
                                zIndex: 1000,
                                padding: '8px',
                                animation: 'slideIn 0.2s ease-out',
                            }}
                            onClick={(e) => e.stopPropagation()}
                        >
                        <button
                            onClick={handleLogoutClick}
                            style={{
                                width: '100%',
                                    padding: '10px 14px',
                                    background: 'transparent',
                                    color: '#ef4444',
                                border: 'none',
                                    borderRadius: 8,
                                cursor: 'pointer',
                                fontWeight: 500,
                                    fontSize: 14,
                                    transition: 'all 0.2s ease',
                                    outline: 'none',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 10,
                                    textAlign: 'left',
                                }}
                                onMouseEnter={(e) => {
                                    e.target.style.background = 'rgba(239, 68, 68, 0.08)';
                                }}
                                onMouseLeave={(e) => {
                                    e.target.style.background = 'transparent';
                                }}
                            >
                                <LogoutIcon />
                                Log out
                        </button>
                    </div>
                )}
            </div>
            </div>
            
            {/* Animation keyframes */}
            <style jsx>{`
                @keyframes slideIn {
                    from {
                        opacity: 0;
                        transform: translateY(-10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                
                @keyframes pulse {
                    0%, 100% {
                        opacity: 1;
                        transform: scale(1);
                    }
                    50% {
                        opacity: 0.5;
                        transform: scale(1.1);
                    }
                }

                @keyframes spin {
                    0% {
                        transform: rotate(0deg);
                    }
                    100% {
                        transform: rotate(360deg);
                    }
                }
            `}</style>
        </header>
    );
}

export default HomeHeader; 