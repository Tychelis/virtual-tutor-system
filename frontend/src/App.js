import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import AuthPage from './components/AuthPage';
import HomePage from './components/HomePage';
import UserAdminPage from './components/UserAdminPage';
import TokenExpiryModal from './components/TokenExpiryModal';
import '@fontsource/roboto/300.css';
import '@fontsource/roboto/400.css';
import '@fontsource/roboto/500.css';
import '@fontsource/roboto/700.css';
import authService from './services/authService';
import tokenService from './services/tokenService';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// 创建现代化设计主题
const createModernTheme = (mode = 'light') => createTheme({
  palette: {
    mode,
    primary: {
      main: '#2563eb',
      light: '#3b82f6',
      dark: '#1d4ed8',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#7c3aed',
      light: '#8b5cf6',
      dark: '#6d28d9',
      contrastText: '#ffffff',
    },
    background: {
      default: mode === 'dark' ? '#0f0f23' : '#fafbfc',
      paper: mode === 'dark' ? '#1a1a2e' : '#ffffff',
    },
    text: {
      primary: mode === 'dark' ? '#f8fafc' : '#0f172a',
      secondary: mode === 'dark' ? '#94a3b8' : '#64748b',
    },
    success: {
      main: '#059669',
      light: '#10b981',
      dark: '#047857',
    },
    warning: {
      main: '#d97706',
      light: '#f59e0b',
      dark: '#b45309',
    },
    error: {
      main: '#dc2626',
      light: '#ef4444',
      dark: '#b91c1c',
    },
    info: {
      main: '#0284c7',
      light: '#0ea5e9',
      dark: '#0369a1',
    },
    grey: {
      50: '#f8fafc',
      100: '#f1f5f9',
      200: '#e2e8f0',
      300: '#cbd5e1',
      400: '#94a3b8',
      500: '#64748b',
      600: '#475569',
      700: '#334155',
      800: '#1e293b',
      900: '#0f172a',
    },
  },
  typography: {
    fontFamily: '"Inter", "SF Pro Display", "Segoe UI", "Roboto", sans-serif',
    h1: {
      fontSize: '2.5rem',
      lineHeight: 1.2,
      fontWeight: 700,
      letterSpacing: '-0.025em',
    },
    h2: {
      fontSize: '2rem',
      lineHeight: 1.25,
      fontWeight: 600,
      letterSpacing: '-0.025em',
    },
    h3: {
      fontSize: '1.5rem',
      lineHeight: 1.3,
      fontWeight: 600,
      letterSpacing: '-0.025em',
    },
    h4: {
      fontSize: '1.25rem',
      lineHeight: 1.35,
      fontWeight: 600,
    },
    h5: {
      fontSize: '1.125rem',
      lineHeight: 1.4,
      fontWeight: 600,
    },
    h6: {
      fontSize: '1rem',
      lineHeight: 1.5,
      fontWeight: 600,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
      fontWeight: 400,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
      fontWeight: 400,
    },
    caption: {
      fontSize: '0.75rem',
      lineHeight: 1.4,
      fontWeight: 400,
    },
    button: {
      fontSize: '0.875rem',
      fontWeight: 500,
      textTransform: 'none',
    },
  },
  shape: {
    borderRadius: 12,
  },
  shadows: [
    'none',
    '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  ],
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          background: mode === 'dark' 
            ? 'rgba(26, 26, 46, 0.8)' 
            : 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(20px)',
          border: mode === 'dark'
            ? '1px solid rgba(148, 163, 184, 0.1)'
            : '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: mode === 'dark'
            ? '0 8px 32px rgba(0, 0, 0, 0.3)'
            : '0 8px 32px rgba(37, 99, 235, 0.08)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: mode === 'dark'
              ? '0 12px 40px rgba(0, 0, 0, 0.4)'
              : '0 12px 40px rgba(37, 99, 235, 0.12)',
          }
        }
      }
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          textTransform: 'none',
          fontWeight: 500,
          fontSize: '0.875rem',
          padding: '10px 20px',
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'translateY(-1px)',
          }
        },
        contained: {
          background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
          boxShadow: '0 4px 14px rgba(37, 99, 235, 0.3)',
          '&:hover': {
            background: 'linear-gradient(135deg, #1d4ed8 0%, #6d28d9 100%)',
            boxShadow: '0 6px 20px rgba(37, 99, 235, 0.4)',
          }
        },
        outlined: {
          borderColor: mode === 'dark' ? '#374151' : '#e5e7eb',
          color: mode === 'dark' ? '#f8fafc' : '#374151',
          '&:hover': {
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37, 99, 235, 0.04)',
          }
        }
      }
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: '#2563eb',
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: '#2563eb',
              borderWidth: 2,
            }
          }
        }
      }
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: 'transparent',
          backdropFilter: 'blur(20px)',
          boxShadow: 'none',
          borderBottom: mode === 'dark'
            ? '1px solid rgba(148, 163, 184, 0.1)'
            : '1px solid rgba(226, 232, 240, 0.8)',
        }
      }
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 500,
        }
      }
    }
  }
});

const theme = createModernTheme('light');

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('token'));
  const [userRole, setUserRole] = useState(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const user = JSON.parse(userStr);
      return user.role;
    }
    return null;
  });
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [tokenModalData, setTokenModalData] = useState({
    isExpired: false,
    remainingTime: 0
  });

  const handleLoginSuccess = (userData) => {
    setIsLoggedIn(true);
    setUserRole(userData.role);
    // 登录成功后开始token监控
    tokenService.startTokenMonitoring(handleTokenExpired, handleTokenWarning);
  };

  const handleLogout = () => {
    authService.logout();
    tokenService.stopTokenMonitoring();
    setIsLoggedIn(false);
    setUserRole(null);
  };

  // Token过期处理
  const handleTokenExpired = async (message) => {
    setTokenModalData({
      isExpired: true,
      remainingTime: 0
    });
    setShowTokenModal(true);
  };

  // Token即将过期警告
  const handleTokenWarning = async (message) => {
    const remainingTime = await tokenService.getTokenRemainingTime();
    setTokenModalData({
      isExpired: false,
      remainingTime: remainingTime
    });
    setShowTokenModal(true);
  };

  // 延长会话
  const handleExtendSession = () => {
    setShowTokenModal(false);
    // 这里可以调用后端接口延长token有效期
    console.log('Session extended');
  };

  // 关闭token模态框
  const handleCloseTokenModal = () => {
    setShowTokenModal(false);
  };

  // Listen for localStorage changes to ensure state is in sync
  useEffect(() => {
    const checkAuthStatus = () => {
      const token = localStorage.getItem('token');
      const userStr = localStorage.getItem('user');

      if (!token) {
        setIsLoggedIn(false);
        setUserRole(null);
        tokenService.stopTokenMonitoring();
      } else if (userStr) {
        try {
          const user = JSON.parse(userStr);
          setUserRole(user.role);
          // 开始token监控
          tokenService.startTokenMonitoring(handleTokenExpired, handleTokenWarning);
        } catch (e) {
          console.error('Error parsing user data:', e);
          setIsLoggedIn(false);
          setUserRole(null);
          tokenService.stopTokenMonitoring();
        }
      }
    };

    // Check on mount
    checkAuthStatus();

    // Listen for storage events (when localStorage changes in other tabs)
    const handleStorageChange = (e) => {
      if (e.key === 'token' || e.key === 'user') {
        checkAuthStatus();
      }
    };

    window.addEventListener('storage', handleStorageChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      tokenService.stopTokenMonitoring();
    };
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={
            isLoggedIn ? <Navigate to="/" /> : <AuthPage onLoginSuccess={handleLoginSuccess} />
          } />
          <Route path="/" element={
            isLoggedIn ? (
              userRole === 'tutor' ? (
                <UserAdminPage onLogout={handleLogout} />
              ) : (
                <HomePage onLogout={handleLogout} />
              )
            ) : <Navigate to="/login" />
          } />

        </Routes>

        {/* Token过期提示模态框 */}
        <TokenExpiryModal
          isOpen={showTokenModal}
          onClose={handleCloseTokenModal}
          onExtend={handleExtendSession}
          onLogout={handleLogout}
          remainingTime={tokenModalData.remainingTime}
          isExpired={tokenModalData.isExpired}
        />
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
