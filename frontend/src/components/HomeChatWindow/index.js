import React, { useEffect, useRef } from 'react';

function HomeChatWindow({ chatId, messages, onSendMessage, themeStyles }) {
    const isDarkMode = themeStyles?.isDarkMode || false;
    const messagesWrapperRef = useRef(null);

    useEffect(() => {
        if (messagesWrapperRef.current) {
            messagesWrapperRef.current.scrollTop = messagesWrapperRef.current.scrollHeight;
        }
    }, [messages, chatId]);

    return (
        <div style={{
            flex: '1 1 auto',
            background: isDarkMode ? 'rgba(15, 15, 30, 0.95)' : 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(20px)',
            borderRadius: 16,
            margin: 8,
            padding: 0,
            minWidth: 550,
            minHeight: 0,
            display: 'flex',
            flexDirection: 'column',
            position: 'relative',
            boxShadow: isDarkMode ? '0 8px 32px rgba(0, 0, 0, 0.7)' : '0 8px 32px rgba(37, 99, 235, 0.08)',
            border: isDarkMode ? '1px solid rgba(80, 80, 120, 0.3)' : '1px solid rgba(255, 255, 255, 0.2)',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        }}>
            {/* History messages */}
            <div 
                ref={messagesWrapperRef}
                style={{ 
                flex: 1, 
                overflowY: 'auto', 
                msOverflowStyle: 'thin',
                WebkitOverflowScrolling: 'touch',
                scrollbarWidth: 'thin',
                scrollBehavior: 'smooth',
                height: '100%',
                padding: 24, 
                display: 'flex', 
                flexDirection: 'column', 
                gap: 16,
                background: isDarkMode 
                    ? 'linear-gradient(180deg, rgba(20, 20, 36, 0.5) 0%, rgba(15, 15, 30, 0.8) 100%)'
                    : 'linear-gradient(180deg, rgba(248, 250, 252, 0.5) 0%, rgba(255, 255, 255, 0.8) 100%)',
            }}>
                {!chatId ? (
                    <div style={{ 
                        textAlign: 'center',
                        padding: '80px 48px',
                        background: isDarkMode 
                            ? 'linear-gradient(135deg, rgba(76, 76, 109, 0.15) 0%, rgba(58, 58, 92, 0.15) 100%)'
                            : 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)',
                        borderRadius: 20,
                        border: isDarkMode ? '2px solid rgba(80, 80, 120, 0.3)' : '2px solid rgba(102, 126, 234, 0.1)',
                        position: 'relative',
                        overflow: 'hidden',
                    }}>
                        {/* 装饰性背景 */}
                        <div style={{
                            position: 'absolute',
                            top: -50,
                            right: -50,
                            width: 200,
                            height: 200,
                            borderRadius: '50%',
                            background: 'radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, transparent 70%)',
                            pointerEvents: 'none',
                        }} />
                        <div style={{
                            position: 'absolute',
                            bottom: -30,
                            left: -30,
                            width: 150,
                            height: 150,
                            borderRadius: '50%',
                            background: 'radial-gradient(circle, rgba(118, 75, 162, 0.1) 0%, transparent 70%)',
                            pointerEvents: 'none',
                        }} />
                        
                        <div style={{ 
                            fontSize: 72, 
                            marginBottom: 24,
                            filter: 'drop-shadow(0 4px 8px rgba(102, 126, 234, 0.2))',
                        }}>
                            🚀
                        </div>
                        <div style={{ 
                            fontSize: 24, 
                            fontWeight: 700, 
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            backgroundClip: 'text',
                            marginBottom: 12,
                        }}>
                            Ready to Learn
                        </div>
                        <div style={{ 
                            fontSize: 15, 
                            color: isDarkMode ? '#9ca3af' : '#64748b', 
                            lineHeight: 1.6,
                            maxWidth: 360,
                            margin: '0 auto',
                        }}>
                            Click the <strong style={{ color: isDarkMode ? '#c7d2fe' : '#667eea' }}>+ New Chat</strong> button in the sidebar to begin your AI-powered learning journey.
                        </div>
                    </div>
                ) : messages.length === 0 ? (
                    <div style={{ 
                        textAlign: 'center',
                        padding: '80px 48px',
                        background: isDarkMode 
                            ? 'linear-gradient(135deg, rgba(76, 76, 109, 0.15) 0%, rgba(58, 58, 92, 0.15) 100%)'
                            : 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)',
                        borderRadius: 20,
                        border: isDarkMode ? '2px solid rgba(80, 80, 120, 0.3)' : '2px solid rgba(102, 126, 234, 0.1)',
                        position: 'relative',
                        overflow: 'hidden',
                    }}>
                        {/* 装饰性背景 */}
                        <div style={{
                            position: 'absolute',
                            top: -40,
                            left: '50%',
                            transform: 'translateX(-50%)',
                            width: 180,
                            height: 180,
                            borderRadius: '50%',
                            background: 'radial-gradient(circle, rgba(102, 126, 234, 0.12) 0%, transparent 70%)',
                            pointerEvents: 'none',
                        }} />
                        
                        <div style={{ 
                            fontSize: 72, 
                            marginBottom: 24,
                            filter: 'drop-shadow(0 4px 8px rgba(102, 126, 234, 0.2))',
                        }}>
                            💬
                        </div>
                        <div style={{ 
                            fontSize: 24, 
                            fontWeight: 700, 
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            backgroundClip: 'text',
                            marginBottom: 12,
                        }}>
                            Start Your Conversation
                        </div>
                        <div style={{ 
                            fontSize: 15, 
                            color: isDarkMode ? '#9ca3af' : '#64748b', 
                            lineHeight: 1.6,
                            maxWidth: 380,
                            margin: '0 auto 32px',
                        }}>
                            Type your question below and let our AI tutor guide you through your learning experience.
                        </div>
                        
                        {/* 快速提示 */}
                        <div style={{
                            display: 'flex',
                            gap: 12,
                            justifyContent: 'center',
                            flexWrap: 'wrap',
                            marginTop: 24,
                        }}>
                            {[
                                { label: 'Explain a concept', message: 'Can you explain a concept for me?' },
                                { label: 'Solve a problem', message: 'Can you help me solve a problem?' },
                                { label: 'Review materials', message: 'Can you help me review some materials?' }
                            ].map((tip, i) => (
                                <div 
                                    key={i} 
                                    style={{
                                        padding: '8px 16px',
                                        background: isDarkMode ? 'rgba(30, 30, 50, 0.8)' : 'rgba(255, 255, 255, 0.8)',
                                        border: isDarkMode ? '1px solid rgba(80, 80, 120, 0.3)' : '1px solid rgba(102, 126, 234, 0.2)',
                                        borderRadius: 20,
                                        fontSize: 13,
                                        color: isDarkMode ? '#c7d2fe' : '#667eea',
                                        fontWeight: 600,
                                        cursor: 'pointer',
                                        transition: 'all 0.3s ease',
                                    }}
                                    onClick={() => {
                                        if (onSendMessage && chatId) {
                                            onSendMessage(tip.message);
                                        }
                                    }}
                                    onMouseEnter={(e) => {
                                        e.currentTarget.style.background = isDarkMode ? 'rgba(40, 40, 60, 0.9)' : 'rgba(102, 126, 234, 0.1)';
                                        e.currentTarget.style.transform = 'translateY(-2px)';
                                        e.currentTarget.style.boxShadow = isDarkMode ? '0 4px 12px rgba(76, 76, 109, 0.3)' : '0 4px 12px rgba(102, 126, 234, 0.15)';
                                    }}
                                    onMouseLeave={(e) => {
                                        e.currentTarget.style.background = isDarkMode ? 'rgba(30, 30, 50, 0.8)' : 'rgba(255, 255, 255, 0.8)';
                                        e.currentTarget.style.transform = 'translateY(0)';
                                        e.currentTarget.style.boxShadow = 'none';
                                    }}
                                >
                                    {tip.label}
                                </div>
                            ))}
                        </div>
                    </div>
                ) : (
                    messages
                        .filter(msg => msg.text || msg.image)
                        .map((msg, idx) => (
                            <div key={msg.id || idx} style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: msg.from === 'user' ? 'flex-end' : 'flex-start',
                                gap: 4,
                                animation: 'fadeInUp 0.3s ease-out',
                            }}>
                                {/* 发送者标签 */}
                                <div style={{
                                    fontSize: 11,
                                    color: isDarkMode ? '#6b7280' : '#94a3b8',
                                    fontWeight: 600,
                                    padding: '0 12px',
                                    letterSpacing: '0.5px',
                                    textTransform: 'uppercase',
                                }}>
                                    {msg.from === 'user' ? 'You' : 'AI Tutor'}
                                </div>
                                
                                {/* 消息气泡 */}
                                <div style={{
                                    background: msg.from === 'user' 
                                        ? (isDarkMode ? 'linear-gradient(135deg, #4c4c6d 0%, #3a3a5c 100%)' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)')
                                        : (isDarkMode ? 'rgba(30, 30, 50, 0.9)' : '#FFFFFF'),
                                    color: msg.from === 'user' ? '#FFFFFF' : (isDarkMode ? '#e5e7eb' : '#1e293b'),
                                    borderRadius: msg.from === 'user' ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
                                    padding: '16px 20px',
                                    maxWidth: '75%',
                                    fontSize: '15px',
                                    lineHeight: 1.7,
                                    boxShadow: msg.from === 'user' 
                                        ? (isDarkMode ? '0 4px 20px rgba(76, 76, 109, 0.5)' : '0 4px 20px rgba(102, 126, 234, 0.3)')
                                        : (isDarkMode ? '0 2px 16px rgba(0, 0, 0, 0.5)' : '0 2px 16px rgba(15, 23, 42, 0.08)'),
                                    wordBreak: 'break-word',
                                    border: msg.from === 'user' 
                                        ? 'none' 
                                        : (isDarkMode ? '1px solid rgba(80, 80, 120, 0.3)' : '1px solid rgba(226, 232, 240, 0.8)'),
                                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                    position: 'relative',
                                }}
                                onMouseEnter={(e) => {
                                    if (msg.from === 'user') {
                                        e.currentTarget.style.boxShadow = isDarkMode 
                                            ? '0 8px 28px rgba(76, 76, 109, 0.6)' 
                                            : '0 8px 28px rgba(102, 126, 234, 0.4)';
                                        e.currentTarget.style.transform = 'translateY(-2px)';
                                    } else {
                                        e.currentTarget.style.boxShadow = isDarkMode 
                                            ? '0 4px 20px rgba(0, 0, 0, 0.6)' 
                                            : '0 4px 20px rgba(15, 23, 42, 0.12)';
                                        e.currentTarget.style.transform = 'translateY(-1px)';
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    if (msg.from === 'user') {
                                        e.currentTarget.style.boxShadow = isDarkMode 
                                            ? '0 4px 20px rgba(76, 76, 109, 0.5)' 
                                            : '0 4px 20px rgba(102, 126, 234, 0.3)';
                                    } else {
                                        e.currentTarget.style.boxShadow = isDarkMode 
                                            ? '0 2px 16px rgba(0, 0, 0, 0.5)' 
                                            : '0 2px 16px rgba(15, 23, 42, 0.08)';
                                    }
                                    e.currentTarget.style.transform = 'translateY(0)';
                                }}
                            >
                                {msg.image ? (
                                    <img 
                                        src={msg.image} 
                                        alt="Message attachment" 
                                        style={{ 
                                            maxWidth: 240, 
                                            maxHeight: 240, 
                                            borderRadius: 12,
                                            marginBottom: 8,
                                            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                                        }} 
                                    />
                                ) : msg.text ? (
                                    <div style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
                                ) : null}
                                </div>
                            </div>
                        ))
                )}
            </div>
            
            {/* 添加动画 */}
            <style jsx>{`
                @keyframes fadeInUp {
                    from {
                        opacity: 0;
                        transform: translateY(10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
            `}</style>
        </div>
    );
}

export default HomeChatWindow; 