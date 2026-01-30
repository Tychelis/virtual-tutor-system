import React, { useState, useEffect, useRef } from 'react';
import adminService from '../../services/adminService';
import config from '../../config';

// 添加旋转动画样式
const spinAnimation = `
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
`;

// 注入样式到页面
if (typeof document !== 'undefined') {
    const styleId = 'video-button-spin-animation';
    if (!document.getElementById(styleId)) {
        const styleElement = document.createElement('style');
        styleElement.id = styleId;
        styleElement.textContent = spinAnimation;
        document.head.appendChild(styleElement);
    }
}

// 默认AI模型选项（作为备用）
const defaultAiModels = [
    { id: 'tutor-model-1', name: 'Tutor Model 1', description: 'Basic teaching model, suitable for beginners' },
    { id: 'tutor-model-2', name: 'Tutor Model 2', description: 'Advanced teaching model, suitable for learners with foundation' },
    { id: 'tutor-model-3', name: 'Tutor Model 3', description: 'Professional teaching model, suitable for deep learning' },
    { id: 'tutor-model-4', name: 'Tutor Model 4', description: 'Expert-level teaching model, suitable for advanced users' }
];

// WebRTC Video Avatar Component (Square, with connection button in bottom right)
const VideoAvatar = React.forwardRef(({ style }, ref) => {
    const videoRef = useRef(null);
    const pcRef = useRef(null);
    const [connected, setConnected] = useState(false);
    const [loading, setLoading] = useState(false);
    const tabIdRef = useRef(`${Date.now()}_${Math.random().toString(36).slice(2, 8)}`);
    const heartbeatRef = useRef(null);

    // 单标签占用锁，避免多页面争抢 8615
    const LOCK_KEY = 'avatar_connection_lock';
    const LOCK_TTL_MS = 12000; // 12s 视为过期
    const HEARTBEAT_MS = 5000;

    const getLock = () => {
        try {
            const raw = localStorage.getItem(LOCK_KEY);
            if (!raw) return null;
            const data = JSON.parse(raw);
            return data;
        } catch {
            return null;
        }
    };

    const isLockStale = (lock) => {
        if (!lock || !lock.ts) return true;
        return Date.now() - lock.ts > LOCK_TTL_MS;
    };

    const acquireLock = () => {
        const existing = getLock();
        if (existing && !isLockStale(existing) && existing.owner !== tabIdRef.current) {
            return false;
        }
        localStorage.setItem(LOCK_KEY, JSON.stringify({ owner: tabIdRef.current, ts: Date.now() }));
        return true;
    };

    const refreshLock = () => {
        const existing = getLock();
        if (existing && existing.owner === tabIdRef.current) {
            localStorage.setItem(LOCK_KEY, JSON.stringify({ owner: tabIdRef.current, ts: Date.now() }));
        }
    };

    const releaseLock = () => {
        const existing = getLock();
        if (existing && existing.owner === tabIdRef.current) {
            localStorage.removeItem(LOCK_KEY);
        }
    };

    // ⭐ 新增：暴露控制方法给父组件（用于avatar切换时重连）
    React.useImperativeHandle(ref, () => ({
        startConnection: async () => {
            await startConnection();
        },
        stopConnection: () => {
            stopConnection();
        },
        isConnected: () => connected,
    }));

    // 啟動 WebRTC 連接
    const startConnection = async () => {
        // 页面隐藏时不允许连接，避免后台页抢占
        if (document.hidden) {
            alert('当前页面处于后台，已阻止占用视频通道。请切回本页再连接。');
            return;
        }
        // 争抢控制：尝试获取连接锁
        if (!acquireLock()) {
            setLoading(false);
            alert('另一个页面正在使用视频通道。本页已阻止占用。如需切换，请先在另一页断开连接或关闭它。');
            return;
        }
        setLoading(true);
        
        // 🆕 在建立 WebRTC 连接前，先确保 avatar 实例已启动
        try {
            const token = localStorage.getItem('token');
            
            // 检查是否有已选择的 avatar
            const selectedAvatarId = localStorage.getItem('selectedAvatarModel');
            if (!selectedAvatarId) {
                console.warn('No avatar selected, will use default avatar');
            }
            
            // 尝试启动 avatar（如果已经启动则会复用现有实例）
            const avatarToStart = selectedAvatarId || 'test_yongen'; // 使用选中的或默认的
            console.log(`🚀 Ensuring avatar '${avatarToStart}' is running...`);
            
            const startResponse = await fetch(`${config.BACKEND_URL}/api/avatar/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': `Bearer ${token}`
                },
                body: new URLSearchParams({
                    avatar_name: avatarToStart
                })
            });
            
            if (!startResponse.ok) {
                const errorData = await startResponse.json();
                throw new Error(errorData.msg || `Failed to start avatar: ${startResponse.status}`);
            }
            
            const startResult = await startResponse.json();
            console.log('✅ Avatar instance ready:', startResult);
            
            // 如果是新启动的实例，给它一点时间完成初始化
            if (startResult.is_new_instance) {
                console.log('⏳ New instance started, waiting for initialization...');
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
            
        } catch (avatarStartError) {
            console.error('❌ Failed to ensure avatar is running:', avatarStartError);
            setLoading(false);
            releaseLock();
            alert(`无法启动 Avatar 实例：${avatarStartError.message}\n\n请检查服务是否正常运行。`);
            return;
        }
        
        // 继续建立 WebRTC 连接
        let pc;
        let stopped = false;
        const rtcConfig = {
            sdpSemantics: 'unified-plan',
            iceServers: [{ urls: ['stun:stun.l.google.com:19302'] }]
        };
        pc = new window.RTCPeerConnection(rtcConfig);
        pcRef.current = pc;

        pc.addTransceiver('video', { direction: 'recvonly' });
        pc.addTransceiver('audio', { direction: 'recvonly' });

        pc.addEventListener('track', (evt) => {
            if (evt.track.kind === 'video' && videoRef.current) {
                videoRef.current.srcObject = evt.streams[0];
            } else if (evt.track.kind === 'audio') {
                const audio = new Audio();
                audio.srcObject = evt.streams[0];
                audio.autoplay = true;
            }
        });

        await pc.setLocalDescription(await pc.createOffer());
        await new Promise((resolve) => {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                const checkState = () => {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                };
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });

        const offer = pc.localDescription;
        const token = localStorage.getItem('token'); // 获取token用于代理和session
        const response = await fetch(`${config.BACKEND_URL}/api/webrtc/offer`, {
            body: JSON.stringify({ sdp: offer.sdp, type: offer.type }),
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}` // 添加token以支持多用户路由
            },
            method: 'POST'
        });
        const answer = await response.json();
        if (answer.sessionid) {
            await fetch(`${config.BACKEND_URL}/api/sessionid`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'sessionid': answer.sessionid,
                    'Authorization': `Bearer ${token}` // 加入 token
                },
                body: JSON.stringify({ sessionid: answer.sessionid })
            });
        }
        if (!stopped) {
            await pc.setRemoteDescription(answer);
            setConnected(true);
        }
        setLoading(false);
        // 心跳维持占用权
        if (heartbeatRef.current) clearInterval(heartbeatRef.current);
        heartbeatRef.current = setInterval(refreshLock, HEARTBEAT_MS);
    };

    // 關閉 WebRTC 連接
    const stopConnection = () => {
        if (pcRef.current) {
            pcRef.current.close();
            pcRef.current = null;
        }
        if (videoRef.current) {
            videoRef.current.srcObject = null;
        }
        setConnected(false);
        if (heartbeatRef.current) {
            clearInterval(heartbeatRef.current);
            heartbeatRef.current = null;
        }
        releaseLock();
    };

    // 卸載時自動關閉
    useEffect(() => {
        const onVisibility = () => {
            // 页面切走时释放占用，避免其它页连接被抢
            if (document.hidden && connected) {
                stopConnection();
            }
        };
        document.addEventListener('visibilitychange', onVisibility);
        return () => {
            document.removeEventListener('visibilitychange', onVisibility);
            stopConnection();
        };
    }, []);

    return (
        <div style={{
            width: '100%',
            height: '100%',
            borderRadius: 12,
            overflow: 'hidden',
            background: '#000',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 16px #4F378A22',
            position: 'relative',
            ...style
        }}>
            <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 0 }}
            />
            {/* 中间連接/斷開按鈕 */}
            <button
                onClick={connected ? stopConnection : startConnection}
                disabled={loading}
                style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: 64,
                    height: 64,
                    borderRadius: '50%',
                    background: 'rgba(255, 255, 255, 0.95)',
                    border: 'none',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 2px 12px rgba(0, 0, 0, 0.1)',
                    color: '#334155',
                    fontSize: 24,
                    fontWeight: 500,
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    opacity: loading ? 0.6 : (connected ? 0 : 1),
                    backdropFilter: 'blur(10px)',
                    zIndex: 10,
                }}
                onMouseEnter={(e) => {
                    if (!loading && !connected) {
                        e.currentTarget.style.transform = 'translate(-50%, -50%) scale(1.05)';
                        e.currentTarget.style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.15)';
                        e.currentTarget.style.background = 'rgba(255, 255, 255, 1)';
                    }
                }}
                onMouseLeave={(e) => {
                    if (!loading && !connected) {
                        e.currentTarget.style.transform = 'translate(-50%, -50%) scale(1)';
                        e.currentTarget.style.boxShadow = '0 2px 12px rgba(0, 0, 0, 0.1)';
                        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.95)';
                    }
                }}
                title={connected ? 'Disconnect Video' : 'Connect Video'}
            >
                {loading ? (
                    <div style={{
                        width: 20,
                        height: 20,
                        border: '3px solid rgba(148, 163, 184, 0.2)',
                        borderTop: '3px solid #64748b',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite',
                    }} />
                ) : (
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M8 5v14l11-7z" fill="currentColor" />
                    </svg>
                )}
            </button>
            
            {/* 連接後的斷開按鈕（右下角小圖標）*/}
            {connected && (
                <button
                    onClick={stopConnection}
                    disabled={loading}
                    style={{
                        position: 'absolute',
                        right: 16,
                        bottom: 16,
                        width: 40,
                        height: 40,
                        borderRadius: '50%',
                        background: 'rgba(255, 255, 255, 0.95)',
                        border: 'none',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
                        color: '#64748b',
                        fontSize: 16,
                        fontWeight: 500,
                        transition: 'all 0.3s ease',
                        zIndex: 10,
                    }}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'scale(1.05)';
                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
                        e.currentTarget.style.background = 'rgba(255, 255, 255, 1)';
                        e.currentTarget.style.color = '#334155';
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'scale(1)';
                        e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.1)';
                        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.95)';
                        e.currentTarget.style.color = '#64748b';
                    }}
                    title="Disconnect Video"
                >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect x="6" y="6" width="12" height="12" fill="currentColor" />
                    </svg>
                </button>
            )}
        </div>
    );
});

// 设置display name用于调试
VideoAvatar.displayName = 'VideoAvatar';

function HomeChatList({ themeStyles }) {
    // ⭐ 新增：创建ref以控制VideoAvatar组件
    const videoAvatarRef = useRef(null);

    // 从 localStorage 读取保存的模型选择
    const [selectedModel, setSelectedModel] = useState(() => {
        return localStorage.getItem('selectedAvatarModel') || '';
    });
    const [availableAvatars, setAvailableAvatars] = useState([]);
    const [loadingAvatars, setLoadingAvatars] = useState(false);
    const [switchingModel, setSwitchingModel] = useState(false);
    const [showModelGrid, setShowModelGrid] = useState(false);

    // 获取可用Avatar列表
    const fetchAvailableAvatars = async () => {
        setLoadingAvatars(true);
        try {
            const result = await adminService.getAvailableAvatars();
            if (result.success && result.data) {
                // 转换API响应格式
                let avatarList = [];
                if (typeof result.data === 'object' && !Array.isArray(result.data)) {
                    avatarList = Object.entries(result.data).map(([key, avatar]) => ({
                        id: key,
                        name: key,
                        description: avatar.description || `Avatar: ${key}`,
                        status: avatar.status || 'active'
                    }));
                } else if (Array.isArray(result.data)) {
                    avatarList = result.data.map(avatar => ({
                        id: avatar.name || avatar.id,
                        name: avatar.name || avatar.id,
                        description: avatar.description || `Avatar: ${avatar.name || avatar.id}`,
                        status: avatar.status || 'active'
                    }));
                }

                setAvailableAvatars(avatarList);

                // 设置默认选中的模型
                if (avatarList.length > 0 && !selectedModel) {
                    setSelectedModel(avatarList[0].id);
                }
            } else {
                console.warn('Failed to fetch available avatars:', result.message);
                // 使用默认模型
                setAvailableAvatars(defaultAiModels);
                if (!selectedModel) {
                    setSelectedModel(defaultAiModels[0].id);
                }
            }
        } catch (error) {
            console.error('Error fetching available avatars:', error);
            // 使用默认模型
            setAvailableAvatars(defaultAiModels);
            if (!selectedModel) {
                setSelectedModel(defaultAiModels[0].id);
            }
        } finally {
            setLoadingAvatars(false);
        }
    };

    // 切换Avatar模型
    const handleModelSwitch = async (modelId) => {
        if (modelId === selectedModel) return;

        setSwitchingModel(true);
        try {
            // ⭐ 第1步：如果已连接，断开旧的WebRTC连接
            const wasConnected = videoAvatarRef.current?.isConnected?.();
            if (wasConnected) {
                console.log('Avatar switching: disconnecting old connection...');
                videoAvatarRef.current?.stopConnection?.();
                // 等待连接完全断开
                await new Promise(resolve => setTimeout(resolve, 500));
            }

            // ⭐ 第2步：启动新的Avatar实例
            console.log(`Starting new avatar: ${modelId}`);
            const result = await adminService.startAvatar(modelId);

            if (result.success) {
                setSelectedModel(modelId);
                localStorage.setItem('selectedAvatarModel', modelId);
                setShowModelGrid(false);
                console.log(`Avatar started successfully: ${modelId}`);

                // ⭐ 第3步：如果原来是连接状态，自动重新连接
                if (wasConnected) {
                    // 等待后端完全完成avatar切换
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    console.log('Reconnecting to new avatar...');
                    await videoAvatarRef.current?.startConnection?.();
                    console.log('Reconnected to new avatar successfully');
                }
            } else {
                console.error('Failed to switch avatar:', result.message);
                alert(`Failed to switch avatar: ${result.message || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error switching avatar:', error);
            alert(`Error switching avatar: ${error.message || 'Network error'}`);
        } finally {
            setSwitchingModel(false);
        }
    };

    // 组件加载时获取Avatar列表
    useEffect(() => {
        fetchAvailableAvatars();
    }, []);

    return (
        <div style={{
            flex: '0 0 40%',
            minWidth: 450,
            maxWidth: 700,
            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.03) 0%, rgba(118, 75, 162, 0.03) 100%)',
            backdropFilter: 'blur(10px)',
            borderRadius: 16,
            margin: 8,
            padding: 20,
            display: 'flex',
            flexDirection: 'column',
            position: 'relative',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            border: '1px solid rgba(102, 126, 234, 0.1)',
            boxShadow: '0 4px 20px rgba(102, 126, 234, 0.08)',
        }}>
            {/* Avatar切换加载覆盖层 */}
            {switchingModel && (
                <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'rgba(0, 0, 0, 0.85)',
                    backdropFilter: 'blur(10px)',
                    borderRadius: 16,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 1000,
                }}>
                    <div style={{
                        width: 60,
                        height: 60,
                        border: '4px solid rgba(102, 126, 234, 0.2)',
                        borderTop: '4px solid #667eea',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite',
                        marginBottom: 24,
                    }} />
                    <h2 style={{
                        color: 'white',
                        fontSize: 24,
                        fontWeight: 600,
                        marginBottom: 12,
                    }}>Switching Avatar...</h2>
                    <p style={{
                        color: '#cbd5e1',
                        fontSize: 14,
                        marginBottom: 4,
                    }}>Stopping old service and starting new service</p>
                    <p style={{
                        color: '#94a3b8',
                        fontSize: 12,
                    }}>This may take 5-10 seconds, please wait</p>
                    <p style={{
                        color: '#94a3b8',
                        fontSize: 12,
                        fontStyle: 'italic',
                    }}>Video will automatically reconnect when complete</p>
                    <style>{`
                        @keyframes spin {
                            0% { transform: rotate(0deg); }
                            100% { transform: rotate(360deg); }
                        }
                    `}</style>
                </div>
            )}
            {/* 紧凑的AI模型选择器 */}
            <div style={{ marginBottom: 12, zIndex: 10 }}>
                <div style={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 8,
                }}>
                    {/* 紧凑的标签和状态 */}
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        flex: 1,
                    }}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 15a3 3 0 100-6 3 3 0 000 6z" fill="#667eea"/>
                            <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z" stroke="#667eea" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                        <span style={{ 
                            fontSize: 12, 
                            fontWeight: 600, 
                            color: '#475569',
                        }}>
                            Avatar
                        </span>
                        {/* 状态指示器 */}
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 4,
                        }}>
                            <div style={{
                                width: 4,
                                height: 4,
                                borderRadius: '50%',
                                background: '#10b981',
                                boxShadow: '0 0 4px rgba(16, 185, 129, 0.6)',
                            }} />
                            <span style={{
                                fontSize: 10,
                                color: '#10b981',
                                fontWeight: 500,
                            }}>Ready</span>
                        </div>
                    </div>
                </div>

                {/* 紧凑的模型选择下拉框容器 */}
                <div style={{ position: 'relative' }}>
                    <div 
                        onClick={() => setShowModelGrid(!showModelGrid)}
                        style={{
                            padding: '8px 12px',
                            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%)',
                            border: '1px solid rgba(102, 126, 234, 0.2)',
                            borderRadius: 8,
                            cursor: 'pointer',
                            transition: 'all 0.2s ease',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            minHeight: 32,
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.12) 0%, rgba(118, 75, 162, 0.12) 100%)';
                            e.currentTarget.style.borderColor = 'rgba(102, 126, 234, 0.3)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%)';
                            e.currentTarget.style.borderColor = 'rgba(102, 126, 234, 0.2)';
                        }}
                    >
                        {/* 模型名称 */}
                        <span style={{ 
                            fontSize: 12, 
                            fontWeight: 500, 
                            color: '#1e293b',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                        }}>
                            {selectedModel || 'Select model...'}
                        </span>
                        <svg 
                            width="14" 
                            height="14" 
                            viewBox="0 0 24 24" 
                            fill="none" 
                            xmlns="http://www.w3.org/2000/svg"
                            style={{
                                transition: 'transform 0.2s ease',
                                transform: showModelGrid ? 'rotate(180deg)' : 'rotate(0deg)',
                                flexShrink: 0,
                            }}
                        >
                            <path d="M6 9l6 6 6-6" stroke="#667eea" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                    </div>

                    {/* 紧凑的模型选择列表 */}
                    {showModelGrid && (
                        <div style={{
                            position: 'absolute',
                            top: '100%',
                            left: 0,
                            right: 0,
                            marginTop: 4,
                            padding: 8,
                            background: '#ffffff',
                            borderRadius: 8,
                            border: '1px solid rgba(102, 126, 234, 0.2)',
                            maxHeight: 200,
                            overflowY: 'auto',
                            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.15)',
                            zIndex: 100,
                        }}>
                            {loadingAvatars ? (
                                <div style={{ 
                                    padding: 12, 
                                    textAlign: 'center',
                                    color: '#64748b',
                                }}>
                                    <div style={{
                                        width: 20,
                                        height: 20,
                                        border: '2px solid #e5e7eb',
                                        borderTop: '2px solid #667eea',
                                        borderRadius: '50%',
                                        margin: '0 auto 8px',
                                        animation: 'spin 1s linear infinite',
                                    }} />
                                    <div style={{ fontSize: 11 }}>Loading...</div>
                                </div>
                            ) : availableAvatars.length > 0 ? (
                                availableAvatars.map(model => (
                                    <div
                                        key={model.id}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleModelSwitch(model.id);
                                        }}
                                        style={{
                                            padding: '8px 10px',
                                            background: selectedModel === model.id 
                                                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                                                : 'transparent',
                                            borderRadius: 6,
                                            cursor: switchingModel ? 'not-allowed' : 'pointer',
                                            transition: 'all 0.2s ease',
                                            opacity: switchingModel ? 0.6 : 1,
                                            marginBottom: 2,
                                        }}
                                        onMouseEnter={(e) => {
                                            if (!switchingModel && selectedModel !== model.id) {
                                                e.currentTarget.style.background = 'rgba(102, 126, 234, 0.08)';
                                            }
                                        }}
                                        onMouseLeave={(e) => {
                                            if (!switchingModel && selectedModel !== model.id) {
                                                e.currentTarget.style.background = 'transparent';
                                            }
                                        }}
                                    >
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'space-between' }}>
                                            <div style={{ 
                                                fontSize: 11, 
                                                fontWeight: 500, 
                                                color: selectedModel === model.id ? '#fff' : '#1e293b',
                                                overflow: 'hidden',
                                                textOverflow: 'ellipsis',
                                                whiteSpace: 'nowrap',
                                            }}>
                                                {model.name}
                                            </div>
                                            {selectedModel === model.id && (
                                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                    <path d="M20 6L9 17l-5-5" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                                                </svg>
                                            )}
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div style={{ 
                                    padding: 12, 
                                    textAlign: 'center',
                                    color: '#94a3b8',
                                    fontSize: 11,
                                }}>
                                    No models available
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>



            {/* 虛擬導師視頻區域 */}
            <div style={{
                flex: 1,
                borderRadius: 16,
                overflow: 'hidden',
                border: '2px solid rgba(102, 126, 234, 0.15)',
                boxShadow: '0 8px 32px rgba(102, 126, 234, 0.15)',
                background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)',
                position: 'relative',
                minHeight: 0,
                minWidth: 0,
            }}>
                {/* ⭐ 修改：添加ref以支持avatar切换时自动重连 */}
                <VideoAvatar ref={videoAvatarRef} />
            </div>
            
            {/* 添加动画样式 */}
            <style jsx>{`
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
            `}</style>
        </div>
    );
}

export default HomeChatList; 