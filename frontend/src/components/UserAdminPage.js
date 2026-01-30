import React, { useState, useEffect } from 'react';
import AdminSidebar from './AdminSidebar';
import UserTable from './UserTable';

function UserAdminPage({ onLogout }) {
    const [selectedMenu, setSelectedMenu] = useState('user');
    
    // 统一管理主题状态
    const [isDarkMode, setIsDarkMode] = useState(() => {
        const saved = localStorage.getItem('darkMode');
        return saved ? JSON.parse(saved) : false;
    });

    // 主题切换处理函数
    const handleThemeToggle = () => {
        const newMode = !isDarkMode;
        setIsDarkMode(newMode);
        localStorage.setItem('darkMode', JSON.stringify(newMode));
        document.body.style.background = newMode ? '#0f0f23' : '#ffffff';
        document.body.style.color = newMode ? '#e5e5e5' : '#0f172a';
        document.body.style.transition = 'all 0.3s ease';
    };

    // 初始化body样式
    useEffect(() => {
        document.body.style.background = isDarkMode ? '#0f0f23' : '#ffffff';
        document.body.style.color = isDarkMode ? '#e5e5e5' : '#0f172a';
    }, [isDarkMode]);

    return (
        <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
            {/* 左側導航欄 */}
            <AdminSidebar
                selectedMenu={selectedMenu}
                onSelectMenu={setSelectedMenu}
                onLogout={onLogout}
                isDarkMode={isDarkMode}
                onThemeToggle={handleThemeToggle}
            />

            {/* 主工作區域 */}
            <UserTable
                selectedMenu={selectedMenu}
                onLogout={onLogout}
                isDarkMode={isDarkMode}
            />
        </div>
    );
}

export default UserAdminPage; 