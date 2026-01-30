import React, { useState, useEffect } from 'react';

function TokenExpiryModal({ isOpen, onClose, onExtend, onLogout, remainingTime, isExpired = false }) {
    const [timeLeft, setTimeLeft] = useState(remainingTime || 0);

    useEffect(() => {
        if (!isOpen || isExpired) return;

        const timer = setInterval(() => {
            setTimeLeft(prev => {
                if (prev <= 1) {
                    clearInterval(timer);
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);

        return () => clearInterval(timer);
    }, [isOpen, isExpired]);

    useEffect(() => {
        setTimeLeft(remainingTime || 0);
    }, [remainingTime]);

    if (!isOpen) return null;

    const formatTime = (seconds) => {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    };

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999
        }}>
            <div style={{
                background: '#fff',
                borderRadius: 16,
                padding: 32,
                maxWidth: 400,
                width: '90%',
                textAlign: 'center',
                boxShadow: '0 8px 32px rgba(0,0,0,0.3)'
            }}>
                <div style={{ fontSize: 48, marginBottom: 16 }}>
                    {isExpired ? '⏰' : '⚠️'}
                </div>

                <h3 style={{
                    margin: '0 0 16px 0',
                    color: isExpired ? '#ef4444' : '#f59e0b',
                    fontSize: 20,
                    fontWeight: 600
                }}>
                    {isExpired ? 'Session Expired' : 'Session Expiring Soon'}
                </h3>

                <p style={{
                    margin: '0 0 24px 0',
                    color: '#666',
                    fontSize: 16,
                    lineHeight: 1.5
                }}>
                    {isExpired
                        ? 'Your session has expired. Please login again to continue.'
                        : `Your session will expire in ${formatTime(timeLeft)}. Please save your work.`
                    }
                </p>

                {!isExpired && (
                    <div style={{
                        background: '#f8fafc',
                        padding: 16,
                        borderRadius: 8,
                        marginBottom: 24,
                        border: '1px solid #e2e8f0'
                    }}>
                        <div style={{ fontSize: 14, color: '#666', marginBottom: 4 }}>
                            Time remaining:
                        </div>
                        <div style={{
                            fontSize: 24,
                            fontWeight: 700,
                            color: timeLeft <= 60 ? '#ef4444' : '#14b48d'
                        }}>
                            {formatTime(timeLeft)}
                        </div>
                    </div>
                )}

                <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                    {!isExpired && (
                        <button
                            onClick={onExtend}
                            style={{
                                padding: '12px 24px',
                                background: '#14b48d',
                                color: '#fff',
                                border: 'none',
                                borderRadius: 8,
                                fontSize: 14,
                                fontWeight: 500,
                                cursor: 'pointer',
                                transition: 'all 0.2s'
                            }}
                            onMouseEnter={(e) => e.target.style.background = '#0d9488'}
                            onMouseLeave={(e) => e.target.style.background = '#14b48d'}
                        >
                            Stay Logged In
                        </button>
                    )}
                    <button
                        onClick={onLogout}
                        style={{
                            padding: '12px 24px',
                            background: isExpired ? '#ef4444' : '#f1f5f9',
                            color: isExpired ? '#fff' : '#64748b',
                            border: 'none',
                            borderRadius: 8,
                            fontSize: 14,
                            fontWeight: 500,
                            cursor: 'pointer',
                            transition: 'all 0.2s'
                        }}
                        onMouseEnter={(e) => {
                            if (isExpired) {
                                e.target.style.background = '#dc2626';
                            } else {
                                e.target.style.background = '#e2e8f0';
                            }
                        }}
                        onMouseLeave={(e) => {
                            if (isExpired) {
                                e.target.style.background = '#ef4444';
                            } else {
                                e.target.style.background = '#f1f5f9';
                            }
                        }}
                    >
                        {isExpired ? 'Login Again' : 'Logout Now'}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default TokenExpiryModal; 