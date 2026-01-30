import React from 'react';

const LoadingSpinner = ({ message = 'Loading...', size = 'medium' }) => {
    const sizeMap = {
        small: { width: 20, height: 20 },
        medium: { width: 40, height: 40 },
        large: { width: 60, height: 60 }
    };

    const spinnerSize = sizeMap[size] || sizeMap.medium;

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
            gap: '16px'
        }}>
            {/* 旋转的圆圈 */}
            <div style={{
                width: spinnerSize.width,
                height: spinnerSize.height,
                border: '3px solid #f3f3f3',
                borderTop: '3px solid #1976d2',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
                margin: '0 auto'
            }} />

            {/* 加载文字 */}
            <div style={{
                fontSize: '16px',
                color: '#666',
                textAlign: 'center',
                fontWeight: 500
            }}>
                {message}
            </div>

            {/* CSS动画 */}
            <style>
                {`
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                `}
            </style>
        </div>
    );
};

export default LoadingSpinner; 