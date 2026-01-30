import React, { useState } from 'react';
import HomeSidebar from './HomeSidebar';
import HomeHeader from './HomeHeader';
import HomeChatList from './HomeChatList';
import HomeChatWindow from './HomeChatWindow';
import HomeFooter from './HomeFooter';
import chatService from '../services/chatService';
import config from '../config';

// Chat mock data
const initialChatMessages = {
    chat1: [
        { id: 1, from: 'user', text: 'Hello, mentor!' },
        { id: 2, from: 'mentor', text: 'Hello, how can I help you?' },
        {
            id: 3,
            from: 'user',
            file: {
                name: 'example-document.pdf',
                size: 1024000,
                type: 'application/pdf',
                url: '#'
            }
        },
        { id: 4, from: 'mentor', text: 'I can see you uploaded a PDF document. How can I help you with it?' },
    ],
    chat2: [
        { id: 1, from: 'user', text: 'This is Chat2 message.' },
        { id: 2, from: 'mentor', text: 'Received, this is Chat2.' },
    ],
    chat3: [
        { id: 1, from: 'user', text: 'Yesterday\'s conversation.' },
        { id: 2, from: 'mentor', text: 'This is yesterday\'s message.' },
    ],
};

// Chat metadata, including favorite status
const initialChatMetadata = {
    chat1: { title: 'Chat 1', subtitle: 'Recent conversation', isFavorite: false },
    chat2: { title: 'Chat 2', subtitle: 'Important conversation', isFavorite: true },
    chat3: { title: 'Chat 3', subtitle: 'Yesterday\'s conversation', isFavorite: false },
};

function HomePage(props) {
    const [sessions, setSessions] = useState([]);
    const [selectedChatId, setSelectedChatId] = useState(null);
    // 从 localStorage 读取主题设置 - 默认使用浅色主题
    const [isDarkMode, setIsDarkMode] = useState(() => {
        const saved = localStorage.getItem('darkMode');
        return saved ? JSON.parse(saved) : false;
    });
    const [sessionMessages, setSessionMessages] = useState({}); // { sessionId: [msg, ...] }
    const [messages, setMessages] = useState([]);
    const [selectedSubject, setSelectedSubject] = useState('All'); // 管理选中的科目，默认显示所有

    const fetchMessages = async (session_id) => {
        // Prefer rendering from local cache if available
        if (sessionMessages[session_id]) {
            setMessages(sessionMessages[session_id]);
        } else {
            setMessages([]);
        }
        // Sync with backend
        const res = await chatService.getMessages(session_id);
        if (res.success && Array.isArray(res.data)) {
            const msgs = res.data.map((msg, idx) => ({
                id: idx,
                from: msg.role === 'user' ? 'user' : 'mentor',
                text: msg.content,
                image: msg.file_type && msg.file_type.startsWith('image') ? msg.file_path : undefined
            }));
            setSessionMessages(prev => ({ ...prev, [session_id]: msgs }));
            setMessages(msgs);
        }
    };

    // Load sessions on initial mount
    React.useEffect(() => {
        refreshSessions();
    }, []);
    const refreshSessions = async (autoSelectId) => {
        const res = await chatService.listSessions();
        console.log('listSessions response', res);
        if (res.success && Array.isArray(res.data)) {
            setSessions(res.data);
            if (autoSelectId) {
                setSelectedChatId(autoSelectId);
                fetchMessages(autoSelectId); // Fetch messages when auto-selecting
            } else if (!selectedChatId && res.data.length > 0) {
                setSelectedChatId(res.data[0].id);
                fetchMessages(res.data[0].id); // Fetch messages on first load
            }
        } else {
            setSessions([]);
        }
    };
    // Create new session - 根据选中的科目决定是否添加标签
    const handleNewChat = async () => {
        let chatTitle;
        if (selectedSubject === 'All') {
            // 如果选择的是"All"，不添加科目标签
            chatTitle = 'New Chat';
        } else {
            // 否则添加科目标签
            chatTitle = `[${selectedSubject}] New Chat`;
        }
        const res = await chatService.createSession(chatTitle);
        console.log('createSession response', res);
        if (res.success && res.data && res.data.session_id) {
            await refreshSessions(res.data.session_id);
        } else {
            alert(res.message || 'Failed to create new session');
        }
    };
    // Select session
    const handleSelectChat = (id) => {
        setSelectedChatId(id);
        if (sessionMessages[id]) {
            setMessages(sessionMessages[id]);
        } else {
            setMessages([]);
        }
        fetchMessages(id);
    };

    // Send message with streaming support
    const handleSendMessage = async (text) => {
        if (!selectedChatId || !text) return;
        
        const userMsgId = Date.now();
        const aiMsgId = Date.now() + 1;
        
        // 1. Insert user message locally
        setSessionMessages(prev => {
            const prevMsgs = prev[selectedChatId] || [];
            const newMsgs = [
                ...prevMsgs,
                { id: userMsgId, from: 'user', text }
            ];
            setMessages(newMsgs);
            return { ...prev, [selectedChatId]: newMsgs };
        });
        
        // 2. Create placeholder for AI response
        setSessionMessages(prev => {
            const prevMsgs = prev[selectedChatId] || [];
            const newMsgs = [
                ...prevMsgs,
                { id: aiMsgId, from: 'mentor', text: '', streaming: true }
            ];
            setMessages(newMsgs);
            return { ...prev, [selectedChatId]: newMsgs };
        });
        
        // 3. Call backend with streaming
        const formData = new FormData();
        formData.append('message', text);
        formData.append('session_id', selectedChatId);
        
        await chatService.chatStream(
            formData,
            // onChunk: 每次收到新内容时更新
            (chunk, fullText) => {
                setSessionMessages(prev => {
                    const prevMsgs = prev[selectedChatId] || [];
                    const newMsgs = prevMsgs.map(m => 
                        m.id === aiMsgId 
                            ? { ...m, text: fullText, streaming: true }
                            : m
                    );
                    setMessages(newMsgs);
                    return { ...prev, [selectedChatId]: newMsgs };
                });
            },
            // onComplete: 完成时移除streaming标记
            (fullText) => {
                setSessionMessages(prev => {
                    const prevMsgs = prev[selectedChatId] || [];
                    const newMsgs = prevMsgs.map(m => 
                        m.id === aiMsgId 
                            ? { ...m, text: fullText, streaming: false }
                            : m
                    );
                    setMessages(newMsgs);
                    return { ...prev, [selectedChatId]: newMsgs };
                });
            },
            // onError: 错误处理
            (error) => {
                console.error('Stream error:', error);
                setSessionMessages(prev => {
                    const prevMsgs = prev[selectedChatId] || [];
                    const newMsgs = prevMsgs.map(m => 
                        m.id === aiMsgId 
                            ? { ...m, text: '抱歉，回复时出现错误。请重试。', streaming: false, error: true }
                            : m
                    );
                    setMessages(newMsgs);
                    return { ...prev, [selectedChatId]: newMsgs };
                });
            }
        );
    };

    // 發送文件
    const handleSendFile = async (fileData) => {
        if (!selectedChatId || !fileData) return;

        console.log('Process file upload data:', fileData);

        // 1. Insert file message locally immediately
        const fileMessage = {
            id: Date.now(),
            from: 'user',
            file: {
                name: fileData.fileInfo.name,
                size: fileData.fileInfo.size,
                type: fileData.fileInfo.type,
                // 根据实际后端响应构建下载URL
                url: fileData.file.file_path ?
                    `${config.BACKEND_URL}/api/download/${fileData.file.file_id}` :
                    '#', // 临时占位符
                file_id: fileData.file.file_id,
                file_path: fileData.file.file_path,
                chunk_count: fileData.file.chunk_count
            },
            pending: true
        };

        setSessionMessages(prev => {
            const prevMsgs = prev[selectedChatId] || [];
            const newMsgs = [...prevMsgs, fileMessage];
            setMessages(newMsgs);
            return { ...prev, [selectedChatId]: newMsgs };
        });

        // 2. Remove pending status and complete file message display
        setTimeout(() => {
            setSessionMessages(prev => {
                const prevMsgs = prev[selectedChatId] || [];
                // 移除 pending
                const filtered = prevMsgs.filter(m => !m.pending);
                const newMsgs = [
                    ...filtered,
                    { ...fileMessage, pending: false },
                ];

                setMessages(newMsgs);
                return { ...prev, [selectedChatId]: newMsgs };
            });
        }, 500); // 短暂延迟以显示上传状态
    };

    // Handle theme switching
    const handleThemeChange = (newMode) => {
        setIsDarkMode(newMode);
        localStorage.setItem('darkMode', JSON.stringify(newMode));
        document.body.style.background = newMode ? '#0f0f23' : '#ffffff';
        document.body.style.color = newMode ? '#e5e5e5' : '#0f172a';
        document.body.style.transition = 'all 0.3s ease';
    };

    // 初始化body样式
    React.useEffect(() => {
        document.body.style.background = isDarkMode ? '#0f0f23' : '#ffffff';
        document.body.style.color = isDarkMode ? '#e5e5e5' : '#0f172a';
    }, [isDarkMode]);


    // Enhanced Theme styles - 深色主题配色
    const themeStyles = {
        // 基础颜色
        background: isDarkMode ? '#0f0f23' : '#ffffff',
        color: isDarkMode ? '#e5e7eb' : '#0f172a',
        
        // 侧边栏
        sidebarBackground: isDarkMode ? 'rgba(15, 15, 30, 0.98)' : 'rgba(255, 255, 255, 0.9)',
        sidebarHeaderBackground: isDarkMode ? 'rgba(20, 20, 36, 0.98)' : 'rgba(255, 255, 255, 0.95)',
        sidebarHeaderColor: isDarkMode ? '#e5e7eb' : '#667eea',
        
        // 聊天列表
        chatListBackground: isDarkMode ? 'rgba(15, 15, 25, 0.9)' : 'rgba(247, 249, 251, 0.8)',
        chatItemBackground: isDarkMode ? 'rgba(30, 30, 50, 0.8)' : 'rgba(255, 255, 255, 0.9)',
        chatItemSelectedBackground: isDarkMode ? 'linear-gradient(135deg, #4c4c6d 0%, #3a3a5c 100%)' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        chatItemColor: isDarkMode ? '#e5e7eb' : '#1e293b',
        chatItemSubtitleColor: isDarkMode ? '#9ca3af' : '#64748b',
        
        // 输入框
        inputBackground: isDarkMode ? 'rgba(30, 30, 50, 0.9)' : 'rgba(255, 255, 255, 0.95)',
        inputBorder: isDarkMode ? 'rgba(80, 80, 120, 0.3)' : 'rgba(102, 126, 234, 0.15)',
        inputColor: isDarkMode ? '#e5e7eb' : '#0f172a',
        placeholderColor: isDarkMode ? '#6b7280' : '#94a3b8',
        
        // 按钮
        buttonBackground: isDarkMode ? 'rgba(30, 30, 50, 0.9)' : 'rgba(255, 255, 255, 0.95)',
        buttonColor: isDarkMode ? '#e5e7eb' : '#0f172a',
        
        // 阴影
        shadow: isDarkMode ? '0 8px 32px rgba(0, 0, 0, 0.7)' : '0 8px 32px rgba(37, 99, 235, 0.08)',
        
        // Tab 激活状态
        activeBackground: isDarkMode ? 'rgba(76, 76, 109, 0.4)' : 'rgba(102, 126, 234, 0.1)',
        activeColor: isDarkMode ? '#e5e7eb' : '#667eea',
        inactiveColor: isDarkMode ? '#6b7280' : '#64748b',
        activeShadow: isDarkMode ? '0 4px 16px rgba(76, 76, 109, 0.5)' : '0 2px 8px rgba(102, 126, 234, 0.12)',
        
        // 计数徽章
        activeCountBackground: isDarkMode ? 'rgba(100, 100, 140, 0.3)' : 'rgba(102, 126, 234, 0.15)',
        inactiveCountBackground: isDarkMode ? 'rgba(80, 80, 100, 0.2)' : 'rgba(100, 116, 139, 0.1)',
        activeCountColor: isDarkMode ? '#c7d2fe' : '#667eea',
        inactiveCountColor: isDarkMode ? '#9ca3af' : '#64748b',
        
        // 分组标题
        groupTitleColor: isDarkMode ? '#6b7280' : '#64748b',
        
        // 选中状态
        selectedBackground: isDarkMode ? 'linear-gradient(135deg, #4c4c6d 0%, #3a3a5c 100%)' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        selectedColor: '#ffffff',
        selectedShadow: isDarkMode ? '0 8px 24px rgba(76, 76, 109, 0.6)' : '0 4px 16px rgba(102, 126, 234, 0.25)',
        selectedSubtitleColor: 'rgba(255, 255, 255, 0.8)',
        inactiveSubtitleColor: isDarkMode ? '#6b7280' : '#64748b',
        
        // 页脚
        footerBackground: isDarkMode ? 'rgba(15, 15, 30, 0.98)' : 'rgba(255, 255, 255, 0.95)',
        barColor: isDarkMode ? 'rgba(80, 80, 120, 0.3)' : 'rgba(226, 232, 240, 0.8)',
        
        // 黑夜模式标识
        isDarkMode: isDarkMode
    };

    return (
        <div style={{
            display: 'flex',
            height: '100vh',
            minHeight: 0,
            background: isDarkMode 
                ? 'linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%)'
                : 'linear-gradient(135deg, #fafbfc 0%, #f1f5f9 100%)',
            color: isDarkMode ? '#e5e7eb' : '#0f172a',
            transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
            position: 'relative',
            overflow: 'hidden',
        }}>
            {/* 现代化装饰背景 */}
            <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: isDarkMode
                    ? `
                        radial-gradient(circle at 20% 20%, rgba(76, 76, 109, 0.15) 0%, transparent 50%),
                        radial-gradient(circle at 80% 80%, rgba(58, 58, 92, 0.15) 0%, transparent 50%),
                        linear-gradient(135deg, rgba(76, 76, 109, 0.08) 0%, transparent 30%, rgba(58, 58, 92, 0.08) 100%)
                    `
                    : `
                        radial-gradient(circle at 20% 20%, rgba(37, 99, 235, 0.02) 0%, transparent 50%),
                        radial-gradient(circle at 80% 80%, rgba(124, 58, 237, 0.02) 0%, transparent 50%),
                        linear-gradient(135deg, rgba(37, 99, 235, 0.01) 0%, transparent 30%, rgba(124, 58, 237, 0.01) 100%)
                    `,
                pointerEvents: 'none',
                zIndex: 0,
                transition: 'all 0.5s ease',
            }} />

            {/* 网格背景 */}
            <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundImage: isDarkMode
                    ? `
                        linear-gradient(rgba(80, 80, 120, 0.08) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(80, 80, 120, 0.08) 1px, transparent 1px)
                    `
                    : `
                        linear-gradient(rgba(37, 99, 235, 0.01) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(37, 99, 235, 0.01) 1px, transparent 1px)
                    `,
                backgroundSize: '40px 40px',
                opacity: isDarkMode ? 0.4 : 0.5,
                pointerEvents: 'none',
                zIndex: 1,
                transition: 'all 0.5s ease',
            }} />

            {/* 主要布局容器 */}
            <div style={{
                display: 'flex',
                width: '100%',
                height: '100%',
                position: 'relative',
                zIndex: 10,
            }}>
                <HomeSidebar
                    sessions={sessions}
                    selectedChatId={selectedChatId}
                    onSelectChat={handleSelectChat}
                    onRefreshSessions={refreshSessions}
                    onThemeChange={handleThemeChange}
                    themeStyles={themeStyles}
                    onLogout={props.onLogout}
                    selectedSubject={selectedSubject}
                    onSubjectChange={setSelectedSubject}
                />
                
                {/* 主内容区 */}
                <div style={{ 
                    flex: 1, 
                    display: 'flex', 
                    flexDirection: 'column',
                    minHeight: 0,
                    background: isDarkMode 
                        ? 'rgba(20, 20, 36, 0.9)' 
                        : 'rgba(255, 255, 255, 0.8)',
                    backdropFilter: 'blur(20px)',
                    borderRadius: '20px',
                    margin: '16px',
                    overflow: 'hidden',
                    boxShadow: isDarkMode 
                        ? '0 8px 32px rgba(0, 0, 0, 0.7)' 
                        : '0 8px 32px rgba(37, 99, 235, 0.08)',
                    border: isDarkMode 
                        ? '1px solid rgba(80, 80, 120, 0.3)' 
                        : '1px solid rgba(255, 255, 255, 0.2)',
                    transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
                }}>
                    <HomeHeader 
                        themeStyles={themeStyles} 
                        onLogout={props.onLogout} 
                    />
                    
                    {/* 内容主体区域 */}
                    <div style={{ 
                        display: 'flex', 
                        flex: 1, 
                        minHeight: 0,
                        position: 'relative',
                    }}>
                        <HomeChatList themeStyles={themeStyles} />
                        
                        {/* 聊天窗口容器 */}
                        <div style={{
                            flex: '1 1 auto',
                            display: 'flex',
                            flexDirection: 'column',
                            minHeight: 0,
                            background: isDarkMode 
                                ? 'rgba(15, 15, 30, 0.9)' 
                                : 'rgba(255, 255, 255, 0.9)',
                            margin: '16px 16px 16px 0',
                            borderRadius: 16,
                            overflow: 'hidden',
                            border: isDarkMode 
                                ? '1px solid rgba(80, 80, 120, 0.3)' 
                                : '1px solid rgba(37, 99, 235, 0.1)',
                            boxShadow: isDarkMode 
                                ? '0 4px 16px rgba(0, 0, 0, 0.5)' 
                                : '0 4px 16px rgba(37, 99, 235, 0.05)',
                            minWidth: 0,
                            transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
                        }}>
                            <HomeChatWindow 
                                key={selectedChatId} 
                                chatId={selectedChatId} 
                                messages={messages} 
                                themeStyles={themeStyles}
                                onSendMessage={handleSendMessage}
                            />
                        </div>
                    </div>
                    
                    {/* 底部输入区 */}
                    <div style={{
                        background: isDarkMode 
                            ? 'rgba(15, 15, 30, 0.98)' 
                            : 'rgba(255, 255, 255, 0.95)',
                        backdropFilter: 'blur(20px)',
                        borderTop: isDarkMode 
                            ? '1px solid rgba(80, 80, 120, 0.3)' 
                            : '1px solid rgba(37, 99, 235, 0.1)',
                        padding: '20px',
                        borderRadius: '0 0 20px 20px',
                        transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
                    }}>
                        <HomeFooter 
                            onSendMessage={handleSendMessage} 
                            onSendFile={handleSendFile} 
                            chatId={selectedChatId} 
                            onNewChat={handleNewChat} 
                            themeStyles={themeStyles} 
                        />
                    </div>
                </div>
            </div>

            {/* 现代化样式 */}
            <style jsx>{`
                /* 滚动条样式 */
                ::-webkit-scrollbar {
                    width: 6px;
                    height: 6px;
                }

                ::-webkit-scrollbar-track {
                    background: rgba(37, 99, 235, 0.05);
                    border-radius: 3px;
                }

                ::-webkit-scrollbar-thumb {
                    background: linear-gradient(135deg, rgba(37, 99, 235, 0.3) 0%, rgba(124, 58, 237, 0.3) 100%);
                    border-radius: 3px;
                }

                ::-webkit-scrollbar-thumb:hover {
                    background: linear-gradient(135deg, rgba(37, 99, 235, 0.5) 0%, rgba(124, 58, 237, 0.5) 100%);
                }

                /* 响应式设计 */
                @media (max-width: 1024px) {
                    .sidebar-collapse {
                        width: 60px;
                    }
                }

                @media (max-width: 768px) {
                    .mobile-layout {
                        flex-direction: column;
                    }
                }
            `}</style>
        </div>
    );
}

export default HomePage; 