import React, { useState } from 'react';

// 科技风格图标组件
const HomeIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="currentColor" strokeWidth="2" fill="none"/>
        <polyline points="9,22 9,12 15,12 15,22" stroke="currentColor" strokeWidth="2" fill="none"/>
    </svg>
);

const UserIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" strokeWidth="2" fill="none"/>
        <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2" fill="none"/>
    </svg>
);

const LoginIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" stroke="currentColor" strokeWidth="2" fill="none"/>
        <polyline points="10,17 15,12 10,7" stroke="currentColor" strokeWidth="2" fill="none"/>
        <line x1="15" y1="12" x2="3" y2="12" stroke="currentColor" strokeWidth="2"/>
    </svg>
);

const SettingsIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2" fill="none"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" stroke="currentColor" strokeWidth="2" fill="none"/>
    </svg>
);

function PreviewNavigator({ currentPage, onPageChange, userRole }) {
    const [isExpanded, setIsExpanded] = useState(false);

    const pages = [
        { id: 'login', name: 'Login Page', icon: LoginIcon, description: 'Authentication interface' },
        { id: 'student', name: 'Student Dashboard', icon: HomeIcon, description: 'Student main interface' },
        { id: 'tutor', name: 'Tutor Dashboard', icon: SettingsIcon, description: 'Tutor admin interface' },
    ];

    const handlePageChange = (pageId) => {
        onPageChange(pageId);
        setIsExpanded(false);
    };

    return (
        <div style={{
            position: 'fixed',
            top: 20,
            right: 20,
            zIndex: 1000,
            background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.9) 100%)',
            backdropFilter: 'blur(20px)',
            borderRadius: 16,
            border: '1px solid rgba(102, 126, 234, 0.2)',
            boxShadow: '0 8px 32px rgba(102, 126, 234, 0.15)',
            overflow: 'hidden',
            transition: 'all 0.3s ease',
            minWidth: isExpanded ? 280 : 60,
        }}>
            {/* Header */}
            <div style={{
                padding: '16px',
                background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
                borderBottom: '1px solid rgba(102, 126, 234, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
            }} onClick={() => setIsExpanded(!isExpanded)}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{
                        width: 32,
                        height: 32,
                        borderRadius: 8,
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontSize: 14,
                        fontWeight: 600,
                    }}>
                        {isExpanded ? '👁️' : '📱'}
                    </div>
                    {isExpanded && (
                        <div>
                            <div style={{ fontSize: 14, fontWeight: 600, color: '#1e293b' }}>
                                Page Preview
                            </div>
                            <div style={{ fontSize: 12, color: '#64748b' }}>
                                Current: {pages.find(p => p.id === currentPage)?.name || 'Unknown'}
                            </div>
                        </div>
                    )}
                </div>
                <div style={{
                    transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 0.3s ease',
                    color: '#667eea',
                }}>
                    ▼
                </div>
            </div>

            {/* Page List */}
            {isExpanded && (
                <div style={{ padding: '8px' }}>
                    {pages.map((page) => {
                        const IconComponent = page.icon;
                        const isActive = currentPage === page.id;
                        
                        return (
                            <div
                                key={page.id}
                                onClick={() => handlePageChange(page.id)}
                                style={{
                                    padding: '12px 16px',
                                    borderRadius: 12,
                                    background: isActive 
                                        ? 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)'
                                        : 'transparent',
                                    border: isActive ? '1px solid rgba(102, 126, 234, 0.2)' : '1px solid transparent',
                                    cursor: 'pointer',
                                    transition: 'all 0.3s ease',
                                    marginBottom: 4,
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 12,
                                }}
                                onMouseEnter={(e) => {
                                    if (!isActive) {
                                        e.target.style.background = 'rgba(102, 126, 234, 0.05)';
                                        e.target.style.border = '1px solid rgba(102, 126, 234, 0.1)';
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    if (!isActive) {
                                        e.target.style.background = 'transparent';
                                        e.target.style.border = '1px solid transparent';
                                    }
                                }}
                            >
                                <div style={{
                                    width: 24,
                                    height: 24,
                                    borderRadius: 6,
                                    background: isActive 
                                        ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                                        : 'rgba(102, 126, 234, 0.1)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    color: isActive ? 'white' : '#667eea',
                                }}>
                                    <IconComponent />
                                </div>
                                <div style={{ flex: 1 }}>
                                    <div style={{ 
                                        fontSize: 14, 
                                        fontWeight: isActive ? 600 : 500,
                                        color: isActive ? '#667eea' : '#1e293b',
                                    }}>
                                        {page.name}
                                    </div>
                                    <div style={{ 
                                        fontSize: 12, 
                                        color: '#64748b',
                                        marginTop: 2,
                                    }}>
                                        {page.description}
                                    </div>
                                </div>
                                {isActive && (
                                    <div style={{
                                        width: 6,
                                        height: 6,
                                        borderRadius: '50%',
                                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                    }} />
                                )}
                            </div>
                        );
                    })}
                    
                    {/* Current Role Indicator */}
                    <div style={{
                        marginTop: 12,
                        padding: '8px 12px',
                        background: 'rgba(16, 185, 129, 0.1)',
                        borderRadius: 8,
                        border: '1px solid rgba(16, 185, 129, 0.2)',
                        fontSize: 12,
                        color: '#059669',
                        textAlign: 'center',
                    }}>
                        Current Role: <strong>{userRole === 'tutor' ? 'Tutor' : 'Student'}</strong>
                    </div>
                </div>
            )}
        </div>
    );
}

export default PreviewNavigator;
