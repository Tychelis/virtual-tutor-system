import React, { useState, useEffect } from 'react';
import { Button, IconButton, Dialog, DialogTitle, DialogContent, DialogActions, TextField, MenuItem } from '@mui/material';
import { Edit, Delete } from '@mui/icons-material';
import adminService from '../../services/adminService';
import { FILE_TYPES, validateFile } from '../../utils/fileTypes';
import LoadingSpinner from '../LoadingSpinner';
import apiConfig from '../../config';

// 添加CSS动画样式
const spinAnimation = `
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
`;

// 注入CSS样式
if (!document.getElementById('avatar-table-styles')) {
    const style = document.createElement('style');
    style.id = 'avatar-table-styles';
    style.textContent = spinAnimation;
    document.head.appendChild(style);
}

const tagColorMap = {
    blue: '#2196f3',
    yellow: '#FFD600',
    green: '#4ADE80',
    pink: '#F06292',
    red: '#FF5252',
    gray: '#BDBDBD'
};

// 狀態標籤顏色映射
const statusTagColorMap = {
    active: '#4ADE80', // 綠色
    inactive: '#FFD600', // 黃色
    banned: '#FF5252' // 紅色
};

// Avatar狀態顏色映射
const avatarStatusColorMap = {
    // Avatar Blur
    'Yes': '#4ADE80', // 綠色 - 啟用
    'No': '#FFD600',  // 黃色 - 未啟用

    // Support Clone
    'Yes': '#4ADE80', // 綠色 - 支持
    'No': '#FF5252',  // 紅色 - 不支持

    // Status
    'active': '#4ADE80', // 綠色
    'inactive': '#FFD600', // 黃色
    'banned': '#FF5252' // 紅色
};

const tableConfig = {
    user: {
        title: 'UserAdmin',
        columns: [
            { key: 'email', label: 'Email' },
            { key: 'username', label: 'Username' },
            { key: 'role', label: 'Role', isTag: true },
            { key: 'status', label: 'Status', isTag: true },
            { key: 'phone', label: 'Phone' },
            { key: 'created_at', label: 'Created At' },
            { key: 'last_login', label: 'Last Login' }
        ],
        dataKey: 'userTableData'
    },
    model: {
        title: 'ModelAdmin',
        columns: [
            { key: 'id', label: 'ID' },
            { key: 'name', label: 'Model Name' },
            { key: 'type', label: 'Type' },
            { key: 'status', label: 'Status', isTag: true },
            { key: 'version', label: 'Version' },
            { key: 'owner', label: 'Owner' },
            { key: 'created_at', label: 'Created At' }
        ],
        dataKey: 'modelTableData'
    },
    avatar: {
        title: 'AvatarAdmin',
        columns: [
            { key: 'avatarImage', label: 'Avatar Image' },
            { key: 'name', label: 'Avatar Name' },
            { key: 'avatar_blur', label: 'Avatar Blur', isTag: true },
            { key: 'support_clone', label: 'Support Clone', isTag: true },
            { key: 'tts_model', label: 'TTS Model' },
            { key: 'timbre', label: 'Timbre' },
            { key: 'ref_text', label: 'Reference Text' },
            { key: 'avatar_model', label: 'Avatar Model' },
            { key: 'prompt_face', label: 'Prompt Face' },
            { key: 'prompt_voice', label: 'Prompt Voice' },
            { key: 'created_at', label: 'Created At' }
        ],
        dataKey: 'avatarTableData'
    },
    knowledge: {
        title: 'KnowledgeAdmin',
        columns: [
            { key: 'filename', label: 'File Name' },
            { key: 'file_type', label: 'File Type' }
        ],
        dataKey: 'knowledgeTableData'
    },
    logs: {
        title: 'UserActionLogs',
        columns: [
            { key: 'id', label: 'ID' },
            { key: 'operator_email', label: 'Operator Email' },
            { key: 'action', label: 'Action', isTag: true },
            { key: 'target_user_id', label: 'Target User ID' },
            { key: 'target_user_email', label: 'Target User Email' },
            { key: 'reason', label: 'Reason' },
            { key: 'details', label: 'Details' },
            { key: 'timestamp', label: 'Timestamp' }
        ],
        dataKey: 'logsTableData'
    }
};

function CreateEditModal({ open, onClose, onSave, columns, initialData, isEdit, selectedMenu }) {
    const [form, setForm] = useState(initialData || {});
    const [avatarFile, setAvatarFile] = useState(null);
    const [avatarPreview, setAvatarPreview] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [promptFaceFile, setPromptFaceFile] = useState(null);
    const [promptVoiceFile, setPromptVoiceFile] = useState(null);
    const [ttsModels, setTtsModels] = useState([]);
    const [loadingModels, setLoadingModels] = useState(false);

    React.useEffect(() => {
        if (initialData) {
            setForm(initialData);
        } else {
            setForm({});
        }
        setAvatarFile(null);
        setAvatarPreview(null);
        setUploading(false);
        setUploadProgress(0);
        setPromptFaceFile(null);
        setPromptVoiceFile(null);
    }, [initialData, open]);

    // 获取TTS模型列表
    React.useEffect(() => {
        console.log('TTS Models useEffect triggered:', { open, selectedMenu, isEdit });
        if (open && selectedMenu === 'avatar' && !isEdit) {
            console.log('Conditions met, calling fetchTtsModels');
            fetchTtsModels();
        }
    }, [open, selectedMenu, isEdit]);

    // 当TTS模型改变时，清空timbre选择
    React.useEffect(() => {
        if (form.tts_model && form.timbre) {
            const selectedModel = ttsModels.find(model => model.name === form.tts_model);
            if (selectedModel && selectedModel.timbres && Array.isArray(selectedModel.timbres)) {
                if (!selectedModel.timbres.includes(form.timbre)) {
                    console.log('TTS model changed, clearing timbre selection');
                    setForm(prev => ({ ...prev, timbre: '' }));
                }
            } else {
                console.log('TTS model changed, clearing timbre selection (no timbres available)');
                setForm(prev => ({ ...prev, timbre: '' }));
            }
        }
    }, [form.tts_model, ttsModels]);

    const fetchTtsModels = async () => {
        setLoadingModels(true);
        try {
            console.log('Fetching TTS models...');
            const result = await adminService.getTtsModels();
            console.log('TTS models API result:', result);

            if (result.success && result.data) {
                // API返回的是对象格式，需要转换为数组
                if (typeof result.data === 'object' && !Array.isArray(result.data)) {
                    const modelsArray = Object.entries(result.data).map(([key, model]) => ({
                        id: key,
                        name: model.full_name || key,
                        clone: model.clone,
                        cur_timbre: model.cur_timbre,
                        license: model.license,
                        status: model.status,
                        timbres: model.timbres
                    }));
                    console.log('Converted TTS models array:', modelsArray);
                    setTtsModels(modelsArray);
                } else if (Array.isArray(result.data)) {
                    setTtsModels(result.data);
                } else {
                    console.warn('TTS models data format is unexpected:', result.data);
                    setTtsModels([]);
                }
            } else {
                console.warn('TTS models data is not available:', result.data);
                setTtsModels([]);
            }
        } catch (error) {
            console.error('Failed to fetch TTS models:', error);
            setTtsModels([]);
        } finally {
            setLoadingModels(false);
        }
    };

    // 處理文本輸入的頭像預覽
    React.useEffect(() => {
        if (typeof form.avatar === 'string') {
            setAvatarPreview(form.avatar.startsWith('http') ? form.avatar : `${BASE_URL}${form.avatar}`);
        } else {
            setAvatarPreview(null);
        }
    }, [form.avatar]);

    // 用戶創建時顯示密碼欄
    const showPassword = !isEdit && columns.some(col => col.key === 'email');

    // 下拉選項
    const roleOptions = [
        { value: 'tutor', label: 'Tutor' },
        { value: 'student', label: 'Student' }
    ];
    const statusOptions = [
        { value: 'active', label: 'Active' },
        { value: 'inactive', label: 'Inactive' },
        { value: 'banned', label: 'Banned' }
    ];

    // Avatar related options
    const supportCloneOptions = [
        { value: true, label: 'Yes' },
        { value: false, label: 'No' }
    ];

    // 从API获取的模型选项
    const ttsModelOptions = Array.isArray(ttsModels) ? ttsModels.map(model => ({
        value: model.name || model.id,
        label: model.name || model.id
    })) : [];

    // 调试信息
    console.log('TTS Models:', ttsModels);
    console.log('TTS Model Options:', ttsModelOptions);
    console.log('Current form state:', form);

    const avatarModelOptions = [
        { value: 'MuseTalk', label: 'MuseTalk' },
        { value: 'Wav2Lip', label: 'Wav2Lip' },
        { value: 'SyncNet', label: 'SyncNet' }
    ];

    // 获取音色选项（从TTS模型中提取）
    const timbreOptions = React.useMemo(() => {
        const timbres = [];
        if (Array.isArray(ttsModels) && form.tts_model) {
            const selectedModel = ttsModels.find(model => model.name === form.tts_model);
            if (selectedModel && selectedModel.timbres && Array.isArray(selectedModel.timbres)) {
                selectedModel.timbres.forEach(timbre => {
                    timbres.push({
                        value: timbre,
                        label: timbre,
                        modelId: selectedModel.name || selectedModel.id
                    });
                });
            }
        }
        return timbres;
    }, [ttsModels, form.tts_model]);

    // Avatar upload handler function
    const handleAvatarUpload = async (file, fieldType = 'avatar') => {
        // 使用统一的文件验证
        try {
            validateFile(file, 'IMAGE');
        } catch (error) {
            alert(error.message);
            return;
        }

        setUploading(true);
        setUploadProgress(0);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const token = localStorage.getItem('token');
            if (!token) {
                throw new Error('No authentication token found');
            }

            const response = await fetch(`${apiConfig.BACKEND_URL}/api/upload`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
                body: formData
            });

            const responseText = await response.text();

            let result;
            if (response.ok) {
                try {
                    const data = JSON.parse(responseText);
                    result = {
                        success: true,
                        data: data
                    };
                } catch (e) {
                    result = {
                        success: false,
                        message: 'Invalid JSON response from server'
                    };
                }
            } else {
                try {
                    const errorData = JSON.parse(responseText);
                    result = {
                        success: false,
                        message: errorData.msg || errorData.message || `Server error: ${response.status}`
                    };
                } catch (e) {
                    result = {
                        success: false,
                        message: `Server error: ${response.status} - ${responseText}`
                    };
                }
            }

            if (result.success) {
                const uploadedUrl = result.data.file_path || result.data.url;

                // Update different fields based on field type
                if (fieldType === 'avatar') {
                    setForm(prev => ({ ...prev, avatar: uploadedUrl }));
                    setAvatarPreview(uploadedUrl);
                } else if (fieldType === 'image') {
                    setForm(prev => ({ ...prev, image: uploadedUrl }));
                }

                alert('Image uploaded successfully!');
            } else {
                alert(`Upload failed: ${result.message}`);
            }
        } catch (error) {
            console.error('Image upload error:', error);
            alert('Image upload failed, please try again');
        } finally {
            setUploading(false);
            setUploadProgress(0);
        }
    };

    const handleAvatarFileChange = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        handleAvatarUpload(file);
    };

    return (
        <Dialog
            open={open}
            onClose={onClose}
            maxWidth="sm"
            fullWidth
            PaperProps={{
                style: {
                    borderRadius: 16,
                    boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
                    overflow: 'hidden'
                }
            }}
        >
            <DialogTitle
                style={{
                    background: '#f8f9fa',
                    borderBottom: '1px solid #e9ecef',
                    padding: '20px 24px',
                    margin: 0,
                    fontSize: 18,
                    fontWeight: 600,
                    color: '#333'
                }}
            >
                {isEdit ? `Edit ${selectedMenu === 'avatar' ? 'Avatar' : 'User'}` : `Create New ${selectedMenu === 'avatar' ? 'Avatar' : 'User'}`}
            </DialogTitle>
            <DialogContent
                style={{
                    padding: '24px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 20,
                    minHeight: '300px',
                    maxHeight: '500px',
                    overflowY: 'auto'
                }}
            >
                {columns.map(col => {
                    if (selectedMenu === 'avatar' && !isEdit && col.key === 'avatarImage') {
                        return null;
                    }
                    if (col.key === 'avatar') {
                        // Avatar upload interface
                        return (
                            <div key={col.key} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                <label style={{ fontSize: 14, fontWeight: 500, color: '#333', marginBottom: 4 }}>{col.label}</label>

                                {/* Avatar preview area */}
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 16,
                                    padding: '16px',
                                    border: '2px dashed #e0e0e0',
                                    borderRadius: 8,
                                    background: '#f8f9fa',
                                    transition: 'all 0.2s'
                                }}>
                                    {/* Avatar preview */}
                                    <div style={{ position: 'relative' }}>
                                        <img
                                            src={avatarPreview || (form.avatar ? (form.avatar.startsWith('http') ? form.avatar : `${BASE_URL}${form.avatar}`) : DEFAULT_AVATAR)}
                                            alt="Avatar preview"
                                            style={{
                                                width: 80,
                                                height: 80,
                                                borderRadius: '50%',
                                                objectFit: 'cover',
                                                border: '2px solid #e0e0e0',
                                                background: '#f0f0f0'
                                            }}
                                        />
                                        {uploading && (
                                            <div style={{
                                                position: 'absolute',
                                                top: 0,
                                                left: 0,
                                                right: 0,
                                                bottom: 0,
                                                background: 'rgba(0,0,0,0.5)',
                                                borderRadius: '50%',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center'
                                            }}>
                                                <div style={{ color: '#fff', fontSize: 12 }}>Uploading...</div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Upload button and info */}
                                    <div style={{ flex: 1 }}>
                                        <input
                                            type="file"
                                            accept="image/*"
                                            onChange={handleAvatarFileChange}
                                            style={{ display: 'none' }}
                                            id="avatar-upload"
                                            disabled={uploading}
                                        />
                                        <label
                                            htmlFor="avatar-upload"
                                            style={{
                                                display: 'inline-block',
                                                padding: '8px 16px',
                                                background: uploading ? '#e0e0e0' : '#1976d2',
                                                color: '#fff',
                                                borderRadius: 6,
                                                cursor: uploading ? 'not-allowed' : 'pointer',
                                                fontSize: 14,
                                                fontWeight: 500,
                                                transition: 'all 0.2s'
                                            }}
                                        >
                                            {uploading ? 'Uploading...' : 'Select Avatar'}
                                        </label>

                                        <div style={{
                                            fontSize: 12,
                                            color: '#666',
                                            marginTop: 8
                                        }}>
                                            {FILE_TYPES.IMAGE.description}
                                        </div>

                                        {form.avatar && (
                                            <div style={{
                                                fontSize: 12,
                                                color: '#1976d2',
                                                marginTop: 4
                                            }}>
                                                Current Avatar: {form.avatar}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    }
                    if (col.key === 'image' && selectedMenu === 'avatar') {
                        // Avatar image upload
                        return (
                            <div key={col.key} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                <label style={{ fontSize: 14, fontWeight: 500, color: '#333', marginBottom: 4 }}>{col.label}</label>

                                {/* Avatar image preview area */}
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 16,
                                    padding: '16px',
                                    border: '2px dashed #e0e0e0',
                                    borderRadius: 8,
                                    background: '#f8f9fa',
                                    transition: 'all 0.2s'
                                }}>
                                    {/* Image preview */}
                                    <div style={{ position: 'relative' }}>
                                        <img
                                            src={form.image || DEFAULT_AVATAR}
                                            alt="Avatar image preview"
                                            style={{
                                                width: 80,
                                                height: 106,
                                                borderRadius: 8,
                                                objectFit: 'cover',
                                                border: '2px solid #e0e0e0',
                                                background: '#f0f0f0'
                                            }}
                                        />
                                        {uploading && (
                                            <div style={{
                                                position: 'absolute',
                                                top: 0,
                                                left: 0,
                                                right: 0,
                                                bottom: 0,
                                                background: 'rgba(0,0,0,0.5)',
                                                borderRadius: 8,
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center'
                                            }}>
                                                <div style={{ color: '#fff', fontSize: 12 }}>Uploading...</div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Upload button and info */}
                                    <div style={{ flex: 1 }}>
                                        <input
                                            type="file"
                                            accept="image/*"
                                            onChange={(e) => {
                                                const file = e.target.files[0];
                                                if (!file) return;
                                                handleAvatarUpload(file, 'image');
                                            }}
                                            style={{ display: 'none' }}
                                            id="avatar-image-upload"
                                            disabled={uploading}
                                        />
                                        <label
                                            htmlFor="avatar-image-upload"
                                            style={{
                                                display: 'inline-block',
                                                padding: '8px 16px',
                                                background: uploading ? '#e0e0e0' : '#1976d2',
                                                color: '#fff',
                                                borderRadius: 6,
                                                cursor: uploading ? 'not-allowed' : 'pointer',
                                                fontSize: 14,
                                                fontWeight: 500,
                                                transition: 'all 0.2s'
                                            }}
                                        >
                                            {uploading ? 'Uploading...' : 'Select Image'}
                                        </label>

                                        <div style={{
                                            fontSize: 12,
                                            color: '#666',
                                            marginTop: 8
                                        }}>
                                            {FILE_TYPES.IMAGE.description}
                                        </div>

                                        {form.image && (
                                            <div style={{
                                                fontSize: 12,
                                                color: '#1976d2',
                                                marginTop: 4
                                            }}>
                                                Current Image: {form.image}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    }
                    if (col.key === 'created_at' || col.key === 'last_login') {
                        // 創建/編輯時不可編輯
                        return null;
                    }
                    if (col.key === 'role') {
                        return (
                            <div key={col.key} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                <label style={{ fontSize: 14, fontWeight: 500, color: '#333', marginBottom: 4 }}>{col.label}</label>
                                <TextField
                                    select
                                    value={form.role || ''}
                                    onChange={e => setForm({ ...form, role: e.target.value })}
                                    fullWidth
                                    variant="outlined"
                                    size="medium"
                                    InputProps={{ style: { borderRadius: 8, fontSize: 14 } }}
                                    sx={{ '& .MuiOutlinedInput-root': { '& fieldset': { borderColor: '#e0e0e0' }, '&:hover fieldset': { borderColor: '#bdbdbd' }, '&.Mui-focused fieldset': { borderColor: '#1976d2' } } }}
                                >
                                    {roleOptions.map(opt => <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>)}
                                </TextField>
                            </div>
                        );
                    }
                    if (col.key === 'status') {
                        return (
                            <div key={col.key} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                <label style={{ fontSize: 14, fontWeight: 500, color: '#333', marginBottom: 4 }}>{col.label}</label>
                                <TextField
                                    select
                                    value={form.status || ''}
                                    onChange={e => setForm({ ...form, status: e.target.value })}
                                    fullWidth
                                    variant="outlined"
                                    size="medium"
                                    InputProps={{ style: { borderRadius: 8, fontSize: 14 } }}
                                    sx={{ '& .MuiOutlinedInput-root': { '& fieldset': { borderColor: '#e0e0e0' }, '&:hover fieldset': { borderColor: '#bdbdbd' }, '&.Mui-focused fieldset': { borderColor: '#1976d2' } } }}
                                >
                                    {statusOptions.map(opt => <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>)}
                                </TextField>
                            </div>
                        );
                    }
                    if (col.key === 'avatar_blur' && selectedMenu === 'avatar') {
                        return (
                            <div key={col.key} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                <label style={{ fontSize: 14, fontWeight: 500, color: '#333', marginBottom: 4 }}>Enable Avatar Blur Effect</label>
                                <TextField
                                    select
                                    value={form.avatar_blur !== undefined ? form.avatar_blur.toString() : 'false'}
                                    onChange={e => setForm({ ...form, avatar_blur: e.target.value === 'true' })}
                                    fullWidth
                                    variant="outlined"
                                    size="medium"
                                    InputProps={{ style: { borderRadius: 8, fontSize: 14 } }}
                                    sx={{ '& .MuiOutlinedInput-root': { '& fieldset': { borderColor: '#e0e0e0' }, '&:hover fieldset': { borderColor: '#bdbdbd' }, '&.Mui-focused fieldset': { borderColor: '#1976d2' } } }}
                                >
                                    <MenuItem value="true">Yes</MenuItem>
                                    <MenuItem value="false">No</MenuItem>
                                </TextField>
                            </div>
                        );
                    }
                    if (col.key === 'support_clone' && selectedMenu === 'avatar') {
                        return (
                            <div key={col.key} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                <label style={{ fontSize: 14, fontWeight: 500, color: '#333', marginBottom: 4 }}>{col.label}</label>
                                <TextField
                                    select
                                    value={form.support_clone !== undefined ? form.support_clone.toString() : ''}
                                    onChange={e => {
                                        const newValue = e.target.value === 'true';
                                        console.log('Support Clone changed:', { oldValue: form.support_clone, newValue, eventValue: e.target.value });
                                        setForm({ ...form, support_clone: newValue });
                                    }}
                                    fullWidth
                                    variant="outlined"
                                    size="medium"
                                    InputProps={{ style: { borderRadius: 8, fontSize: 14 } }}
                                    sx={{ '& .MuiOutlinedInput-root': { '& fieldset': { borderColor: '#e0e0e0' }, '&:hover fieldset': { borderColor: '#bdbdbd' }, '&.Mui-focused fieldset': { borderColor: '#1976d2' } } }}
                                >
                                    {supportCloneOptions.map(opt => <MenuItem key={opt.value} value={opt.value.toString()}>{opt.label}</MenuItem>)}
                                </TextField>
                            </div>
                        );
                    }
                    if (col.key === 'tts_model' && selectedMenu === 'avatar') {
                        return (
                            <div key={col.key} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                <label style={{ fontSize: 14, fontWeight: 500, color: '#333', marginBottom: 4 }}>{col.label}</label>
                                <TextField
                                    select
                                    value={form.tts_model || ''}
                                    onChange={e => setForm({ ...form, tts_model: e.target.value })}
                                    fullWidth
                                    variant="outlined"
                                    size="medium"
                                    InputProps={{ style: { borderRadius: 8, fontSize: 14 } }}
                                    sx={{ '& .MuiOutlinedInput-root': { '& fieldset': { borderColor: '#e0e0e0' }, '&:hover fieldset': { borderColor: '#bdbdbd' }, '&.Mui-focused fieldset': { borderColor: '#1976d2' } } }}
                                >
                                    {ttsModelOptions.length > 0 ? (
                                        ttsModelOptions.map(opt => <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>)
                                    ) : (
                                        <MenuItem value="" disabled>Loading TTS models...</MenuItem>
                                    )}
                                </TextField>
                            </div>
                        );
                    }
                    if (col.key === 'avatar_model' && selectedMenu === 'avatar') {
                        return (
                            <div key={col.key} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                <label style={{ fontSize: 14, fontWeight: 500, color: '#333', marginBottom: 4 }}>{col.label}</label>
                                <TextField
                                    select
                                    value={form.avatar_model || ''}
                                    onChange={e => setForm({ ...form, avatar_model: e.target.value })}
                                    fullWidth
                                    variant="outlined"
                                    size="medium"
                                    InputProps={{ style: { borderRadius: 8, fontSize: 14 } }}
                                    sx={{ '& .MuiOutlinedInput-root': { '& fieldset': { borderColor: '#e0e0e0' }, '&:hover fieldset': { borderColor: '#bdbdbd' }, '&.Mui-focused fieldset': { borderColor: '#1976d2' } } }}
                                >
                                    {avatarModelOptions.map(opt => <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>)}
                                </TextField>
                            </div>
                        );
                    }
                    if (col.key === 'timbre' && selectedMenu === 'avatar') {
                        return (
                            <div key={col.key} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                <label style={{ fontSize: 14, fontWeight: 500, color: '#333', marginBottom: 4 }}>
                                    {col.label} {form.support_clone === false ? '(Required when support_clone is false)' : '(Disabled when support_clone is true)'}
                                </label>
                                <TextField
                                    select
                                    value={form.timbre || ''}
                                    onChange={e => setForm({ ...form, timbre: e.target.value })}
                                    fullWidth
                                    variant="outlined"
                                    size="medium"
                                    disabled={form.support_clone === true || !form.tts_model}
                                    InputProps={{ style: { borderRadius: 8, fontSize: 14 } }}
                                    sx={{ '& .MuiOutlinedInput-root': { '& fieldset': { borderColor: '#e0e0e0' }, '&:hover fieldset': { borderColor: '#bdbdbd' }, '&.Mui-focused fieldset': { borderColor: '#1976d2' } } }}
                                >
                                    {timbreOptions.length > 0 ? (
                                        timbreOptions.map(opt => <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>)
                                    ) : (
                                        <MenuItem value="" disabled>
                                            {!form.tts_model ? 'Please select TTS model first' : 'No timbres available for selected model'}
                                        </MenuItem>
                                    )}
                                </TextField>
                            </div>
                        );
                    }

                    // Add prompt face file upload for avatar creation
                    if (col.key === 'prompt_face' && selectedMenu === 'avatar' && !isEdit) {
                        return (
                            <div key={col.key} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                <label style={{ fontSize: 14, fontWeight: 500, color: '#333', marginBottom: 4 }}>Prompt Face Video (MP4)</label>
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 16,
                                    padding: '16px',
                                    border: '2px dashed #e0e0e0',
                                    borderRadius: 8,
                                    background: '#f8f9fa',
                                    transition: 'all 0.2s'
                                }}>
                                    <input
                                        type="file"
                                        accept={FILE_TYPES.VIDEO.accept}
                                        onChange={(e) => {
                                            const file = e.target.files[0];
                                            if (file) {
                                                try {
                                                    validateFile(file, 'VIDEO');
                                                    setPromptFaceFile(file);
                                                    setForm(prev => ({ ...prev, prompt_face: file }));
                                                } catch (error) {
                                                    alert(error.message);
                                                }
                                            }
                                        }}
                                        style={{ display: 'none' }}
                                        id="prompt-face-upload"
                                    />
                                    <label
                                        htmlFor="prompt-face-upload"
                                        style={{
                                            display: 'inline-block',
                                            padding: '8px 16px',
                                            background: '#1976d2',
                                            color: '#fff',
                                            borderRadius: 6,
                                            cursor: 'pointer',
                                            fontSize: 14,
                                            fontWeight: 500,
                                            transition: 'all 0.2s'
                                        }}
                                    >
                                        Select Face Video
                                    </label>
                                    {promptFaceFile && (
                                        <div style={{
                                            fontSize: 12,
                                            color: '#1976d2',
                                            marginTop: 4
                                        }}>
                                            Selected: {promptFaceFile.name}
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    }
                    // Add ref_text field for avatar creation
                    if (col.key === 'ref_text' && selectedMenu === 'avatar' && !isEdit) {
                        return (
                            <div key={col.key} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                <label style={{ fontSize: 14, fontWeight: 500, color: '#333', marginBottom: 4 }}>
                                    {col.label} {form.support_clone === true ? '(Required when support_clone is true)' : '(Disabled when support_clone is false)'}
                                </label>
                                <TextField
                                    value={form.ref_text || ''}
                                    onChange={e => setForm({ ...form, ref_text: e.target.value })}
                                    fullWidth
                                    variant="outlined"
                                    size="medium"
                                    multiline
                                    rows={3}
                                    disabled={form.support_clone === false}
                                    placeholder={form.support_clone === true ? "Enter reference text for voice synthesis" : "This field is disabled when support_clone is false"}
                                    InputProps={{
                                        style: {
                                            borderRadius: 8,
                                            fontSize: 14
                                        }
                                    }}
                                    sx={{
                                        '& .MuiOutlinedInput-root': {
                                            '& fieldset': {
                                                borderColor: '#e0e0e0',
                                            },
                                            '&:hover fieldset': {
                                                borderColor: '#bdbdbd',
                                            },
                                            '&.Mui-focused fieldset': {
                                                borderColor: '#1976d2',
                                            },
                                        },
                                    }}
                                />
                            </div>
                        );
                    }
                    // Add prompt voice file upload for avatar creation
                    if (col.key === 'prompt_voice' && selectedMenu === 'avatar' && !isEdit) {
                        return (
                            <div key={col.key} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                <label style={{ fontSize: 14, fontWeight: 500, color: '#333', marginBottom: 4 }}>
                                    Prompt Voice Audio (WAV) {form.support_clone === true ? '(Required when support_clone is true)' : '(Disabled when support_clone is false)'}
                                </label>
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 16,
                                    padding: '16px',
                                    border: '2px dashed #e0e0e0',
                                    borderRadius: 8,
                                    background: '#f8f9fa',
                                    transition: 'all 0.2s'
                                }}>
                                    <input
                                        type="file"
                                        accept={FILE_TYPES.AUDIO.accept}
                                        onChange={(e) => {
                                            const file = e.target.files[0];
                                            if (file) {
                                                try {
                                                    validateFile(file, 'AUDIO');
                                                    setPromptVoiceFile(file);
                                                    setForm(prev => ({ ...prev, prompt_voice: file }));
                                                } catch (error) {
                                                    alert(error.message);
                                                }
                                            }
                                        }}
                                        style={{ display: 'none' }}
                                        id="prompt-voice-upload"
                                        disabled={form.support_clone === false}
                                    />
                                    <label
                                        htmlFor="prompt-voice-upload"
                                        style={{
                                            display: 'inline-block',
                                            padding: '8px 16px',
                                            background: form.support_clone === false ? '#e0e0e0' : '#1976d2',
                                            color: form.support_clone === false ? '#999' : '#fff',
                                            borderRadius: 6,
                                            cursor: form.support_clone === false ? 'not-allowed' : 'pointer',
                                            fontSize: 14,
                                            fontWeight: 500,
                                            transition: 'all 0.2s'
                                        }}
                                    >
                                        {form.support_clone === false ? 'Disabled' : 'Select Voice Audio'}
                                    </label>
                                    <div style={{
                                        fontSize: 12,
                                        color: '#666',
                                        marginTop: 8
                                    }}>
                                        {FILE_TYPES.AUDIO.description}
                                    </div>
                                    {promptVoiceFile && (
                                        <div style={{
                                            fontSize: 12,
                                            color: '#1976d2',
                                            marginTop: 4
                                        }}>
                                            Selected: {promptVoiceFile.name}
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    }
                    return (
                        <div key={col.key} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            <label style={{ fontSize: 14, fontWeight: 500, color: '#333', marginBottom: 4 }}>{col.label}</label>
                            <TextField
                                value={form[col.key] || ''}
                                onChange={e => setForm({ ...form, [col.key]: e.target.value })}
                                fullWidth
                                variant="outlined"
                                size="medium"
                                placeholder={`Enter ${col.label.toLowerCase()}`}
                                InputProps={{
                                    style: {
                                        borderRadius: 8,
                                        fontSize: 14
                                    }
                                }}
                                sx={{
                                    '& .MuiOutlinedInput-root': {
                                        '& fieldset': {
                                            borderColor: '#e0e0e0',
                                        },
                                        '&:hover fieldset': {
                                            borderColor: '#bdbdbd',
                                        },
                                        '&.Mui-focused fieldset': {
                                            borderColor: '#1976d2',
                                        },
                                    },
                                }}
                            />
                        </div>
                    );
                })}
                {showPassword && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        <label style={{ fontSize: 14, fontWeight: 500, color: '#333', marginBottom: 4 }}>Password</label>
                        <TextField
                            type="password"
                            value={form.password || ''}
                            onChange={e => setForm({ ...form, password: e.target.value })}
                            fullWidth
                            variant="outlined"
                            size="medium"
                            placeholder="Enter password"
                            InputProps={{
                                style: {
                                    borderRadius: 8,
                                    fontSize: 14
                                }
                            }}
                            sx={{
                                '& .MuiOutlinedInput-root': {
                                    '& fieldset': {
                                        borderColor: '#e0e0e0',
                                    },
                                    '&:hover fieldset': {
                                        borderColor: '#bdbdbd',
                                    },
                                    '&.Mui-focused fieldset': {
                                        borderColor: '#1976d2',
                                    },
                                },
                            }}
                        />
                    </div>
                )}
            </DialogContent>
            <DialogActions
                style={{
                    padding: '16px 24px',
                    background: '#f8f9fa',
                    borderTop: '1px solid #e9ecef',
                    gap: 12
                }}
            >
                <Button
                    onClick={onClose}
                    style={{
                        padding: '8px 24px',
                        borderRadius: 8,
                        textTransform: 'none',
                        fontSize: 14,
                        fontWeight: 500
                    }}
                >
                    Cancel
                </Button>
                <Button
                    onClick={() => onSave(form)}
                    variant="contained"
                    style={{
                        padding: '8px 24px',
                        borderRadius: 8,
                        textTransform: 'none',
                        fontSize: 14,
                        fontWeight: 500,
                        background: '#1976d2',
                        boxShadow: '0 2px 8px rgba(25, 118, 210, 0.3)'
                    }}
                >
                    {isEdit ? 'Update' : 'Create'}
                </Button>
            </DialogActions>
        </Dialog>
    );
}

const BASE_URL = apiConfig.BACKEND_URL;
const DEFAULT_AVATAR = 'https://cdn.jsdelivr.net/gh/edent/SuperTinyIcons/images/svg/user.svg';

function UserTable({ selectedMenu, onLogout, isDarkMode }) {
    const config = tableConfig[selectedMenu] || tableConfig['user'];
    
    // Table data management for different types
    const [userTableData, setUserTableData] = useState([]);
    const [modelTableData, setModelTableData] = useState([]);
    const [avatarTableData, setAvatarTableData] = useState([]);
    const [knowledgeTableData, setKnowledgeTableData] = useState([]);
    const [logsTableData, setLogsTableData] = useState([]);
    const [searchId, setSearchId] = useState('');
    const [searchInfo, setSearchInfo] = useState('');
    const [page, setPage] = useState(1);
    const [selectedRow, setSelectedRow] = useState('');
    // Modal states
    const [modalOpen, setModalOpen] = useState(false);
    const [modalEdit, setModalEdit] = useState(false);
    const [modalInitial, setModalInitial] = useState(null);
    // Delete confirmation dialog states
    const [deleteModalOpen, setDeleteModalOpen] = useState(false);
    const [deleteRowId, setDeleteRowId] = useState(null);

    // Loading states for long operations
    const [isCreatingAvatar, setIsCreatingAvatar] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState('');

    // Avatar image loading states
    const [loadingImages, setLoadingImages] = useState({});

    // File management states
    const [uploadingFile, setUploadingFile] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);
    const [allUsers, setAllUsers] = useState([]);

    // UI states
    const [showMenu, setShowMenu] = useState(false);
    const [imgError, setImgError] = useState(false);
    
    // Button hover states
    const [hoveredEditBtn, setHoveredEditBtn] = useState(null);
    const [hoveredDeleteBtn, setHoveredDeleteBtn] = useState(null);

    // User management API data
    const [loading, setLoading] = useState(false);
    const [apiError, setApiError] = useState(null);

    // Unified pagination statistics display
    const [totalCount, setTotalCount] = useState(0);

    // 统一的主题样式配置（与HomePage保持一致）
    const themeStyles = {
        // 基础颜色
        background: isDarkMode ? '#0f0f23' : '#ffffff',
        color: isDarkMode ? '#e5e7eb' : '#0f172a',
        
        // 容器
        containerBackground: isDarkMode ? 'rgba(20, 20, 36, 0.9)' : 'rgba(255, 255, 255, 0.8)',
        containerBorder: isDarkMode ? '1px solid rgba(80, 80, 120, 0.3)' : '1px solid rgba(255, 255, 255, 0.2)',
        containerShadow: isDarkMode ? '0 8px 32px rgba(0, 0, 0, 0.7)' : '0 8px 32px rgba(37, 99, 235, 0.08)',
        
        // 卡片
        cardBackground: isDarkMode ? 'rgba(30, 30, 50, 0.9)' : 'rgba(255, 255, 255, 0.95)',
        cardBorder: isDarkMode ? '1px solid rgba(80, 80, 120, 0.3)' : '1px solid rgba(37, 99, 235, 0.1)',
        cardShadow: isDarkMode ? '0 4px 16px rgba(0, 0, 0, 0.5)' : '0 4px 16px rgba(37, 99, 235, 0.05)',
        
        // 表格
        tableHeader: isDarkMode ? 'rgba(30, 30, 50, 0.95)' : 'rgba(248, 250, 252, 0.95)',
        tableRow: isDarkMode ? 'rgba(20, 20, 36, 0.5)' : 'rgba(255, 255, 255, 0.9)',
        tableRowHover: isDarkMode ? 'rgba(40, 40, 60, 0.8)' : 'rgba(248, 250, 252, 0.9)',
        tableRowSelected: isDarkMode ? 'rgba(76, 76, 109, 0.6)' : 'rgba(255, 249, 225, 0.9)',
        tableBorder: isDarkMode ? 'rgba(80, 80, 120, 0.3)' : 'rgba(226, 232, 240, 0.8)',
        
        // 输入框
        inputBackground: isDarkMode ? 'rgba(30, 30, 50, 0.9)' : 'rgba(255, 255, 255, 0.95)',
        inputBorder: isDarkMode ? 'rgba(80, 80, 120, 0.3)' : 'rgba(102, 126, 234, 0.15)',
        inputColor: isDarkMode ? '#e5e7eb' : '#0f172a',
        inputPlaceholder: isDarkMode ? '#6b7280' : '#94a3b8',
        
        // 按钮
        buttonPrimary: isDarkMode ? 'linear-gradient(135deg, #4c4c6d 0%, #3a3a5c 100%)' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        buttonPrimaryHover: isDarkMode ? 'linear-gradient(135deg, #5c5c7d 0%, #4a4a6c 100%)' : 'linear-gradient(135deg, #7689f1 0%, #8655b2 100%)',
        buttonSecondary: isDarkMode ? 'rgba(30, 30, 50, 0.9)' : 'rgba(255, 255, 255, 0.95)',
        buttonText: '#ffffff',
        buttonSecondaryText: isDarkMode ? '#e5e7eb' : '#667eea',
        
        // 页面按钮
        pageBtn: (isActive) => isActive 
            ? (isDarkMode ? 'linear-gradient(135deg, #4c4c6d 0%, #3a3a5c 100%)' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)')
            : (isDarkMode ? 'rgba(30, 30, 50, 0.6)' : 'rgba(248, 250, 252, 0.9)'),
        pageBtnText: (isActive) => isActive ? '#ffffff' : (isDarkMode ? '#9ca3af' : '#64748b'),
        
        // 工具栏
        toolbarBg: isDarkMode ? 'rgba(15, 15, 30, 0.95)' : 'rgba(255, 255, 255, 0.95)',
        
        // 创建按钮
        createBtn: isDarkMode ? 'linear-gradient(135deg, #4c4c6d 0%, #3a3a5c 100%)' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        createBtnText: '#ffffff',
        
        // 标签颜色
        tagText: '#fff',
        tagBg: (color) => {
            const tagColorMap = {
                blue: '#2196f3',
                yellow: '#FFD600',
                green: '#4ADE80',
                pink: '#F06292',
                red: '#FF5252',
                gray: '#BDBDBD'
            };
            return tagColorMap[color] || '#BDBDBD';
        },
        
        // 编辑按钮
        editBtn: (selected) => selected ? '#FF5252' : (isDarkMode ? '#888' : '#bbb'),
        editBtnBg: (selected) => selected ? '#FFF0F0' : 'transparent',
        
        // 阴影
        shadow: isDarkMode ? '0 8px 32px rgba(0, 0, 0, 0.7)' : '0 8px 32px rgba(37, 99, 235, 0.08)',
        
        // 侧边栏菜单
        menuBackground: isDarkMode ? 'rgba(15, 15, 25, 0.95)' : 'rgba(255, 255, 255, 0.95)',
        menuItemBackground: isDarkMode ? 'rgba(30, 30, 50, 0.6)' : 'rgba(248, 250, 252, 0.8)',
        menuItemHover: isDarkMode ? 'rgba(40, 40, 60, 0.8)' : 'rgba(237, 242, 247, 0.9)',
        menuItemActive: isDarkMode ? 'linear-gradient(135deg, #4c4c6d 0%, #3a3a5c 100%)' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        menuItemText: isDarkMode ? '#e5e7eb' : '#1e293b',
        menuItemActiveText: '#ffffff',
        
        isDarkMode: isDarkMode
    };

    // User list query
    const fetchUserList = async () => {
        setLoading(true);
        setApiError(null);
        try {
            if (selectedMenu === 'user') {
                const res = await adminService.getUserList({ page: 1, limit: 100 });
                if (res.success && res.data && res.data.users) {
                    setUserTableData(res.data.users.map(u => ({
                        id: u.id,
                        avatar: u.avatar,
                        email: u.email,
                        username: u.username,
                        role: u.role,
                        status: u.status,
                        phone: u.phone,
                        full_name: u.full_name,
                        bio: u.bio,
                        created_at: u.created_at,
                        last_login: u.last_login,
                        tagColor: u.role === 'admin' ? 'blue' : u.role === 'tutor' ? 'yellow' : u.role === 'student' ? 'green' : 'gray',
                        selected: false
                    })));
                }
            }
        } catch (e) {
            setApiError('Failed to get user list');
        } finally {
            setLoading(false);
        }
    };

    // Avatar data mapping
    const fetchAvatarList = async () => {
        setLoading(true);
        setApiError(null);
        try {
            const res = await adminService.getAvatarList();
            if (res.success && res.data) {
                // Transform API response to match table structure
                let avatarData = [];

                // API返回的是对象格式，需要转换为数组
                if (typeof res.data === 'object' && !Array.isArray(res.data)) {
                    avatarData = Object.entries(res.data).map(([key, avatar]) => ({
                        id: key, // 使用key作为id
                        name: key, // 使用key作为name
                        avatarImage: null, // 初始为null，稍后加载
                        avatar_blur: 'No', // API中没有这个字段，默认为No
                        support_clone: avatar.clone ? 'Yes' : 'No', // 使用clone字段
                        timbre: avatar.timbre || '',
                        ref_text: avatar.description || '', // 使用description字段
                        tts_model: avatar.tts_model || '',
                        avatar_model: avatar.avatar_model || '',
                        status: 'active', // API中没有status字段，默认为active
                        created_at: new Date().toISOString().split('T')[0], // API中没有created_at字段，使用当前日期
                        prompt_face: '', // API中没有这些字段
                        prompt_voice: '',
                        tagColor: 'green', // 默认为绿色
                        selected: false
                    }));
                } else if (Array.isArray(res.data)) {
                    // 保持原有的数组处理逻辑
                    avatarData = res.data.map(avatar => ({
                        id: avatar.name || avatar.id,
                        image: avatar.avatar_blur || avatar.image || DEFAULT_AVATAR,
                        name: avatar.name,
                        avatar_blur: avatar.avatar_blur ? 'Yes' : 'No',
                        tts_model: avatar.tts_model || '',
                        avatar_model: avatar.avatar_model || '',
                        support_clone: avatar.support_clone ? 'Yes' : 'No',
                        timbre: avatar.timbre || '',
                        status: avatar.status || 'active',
                        created_at: avatar.created_at || new Date().toISOString().split('T')[0],
                        prompt_face: avatar.prompt_face || '',
                        prompt_voice: avatar.prompt_voice || '',
                        ref_text: avatar.ref_text || '',
                        tagColor: avatar.status === 'active' ? 'green' : 'gray',
                        selected: false
                    }));
                }

                setAvatarTableData(avatarData);
                setTotalCount(avatarData.length);

                // 加载所有Avatar的预览图片
                loadAvatarImages(avatarData);
            } else {
                setApiError(res.message || 'Failed to get Avatar list');
            }
        } catch (e) {
            setApiError('Failed to get Avatar list');
        } finally {
            setLoading(false);
        }
    };

    // 加载Avatar预览图片
    const loadAvatarImages = async (avatarData) => {
        // 批量更新，减少状态更新次数
        const imageUpdates = {};

        for (const avatar of avatarData) {
            try {
                // 设置加载状态
                setLoadingImages(prev => ({ ...prev, [avatar.id]: true }));

                const result = await adminService.getAvatarPreview(avatar.name);
                if (result.success && result.data) {
                    // 创建blob URL
                    const blob = new Blob([result.data], { type: 'image/jpeg' });
                    const imageUrl = URL.createObjectURL(blob);

                    // 收集更新，不立即更新状态
                    imageUpdates[avatar.id] = imageUrl;
                } else {
                    // 设置默认图片
                    imageUpdates[avatar.id] = DEFAULT_AVATAR;
                }
            } catch (error) {
                console.error(`Failed to load avatar image for ${avatar.name}:`, error);
                // 设置默认图片
                imageUpdates[avatar.id] = DEFAULT_AVATAR;
            } finally {
                // 清除加载状态
                setLoadingImages(prev => ({ ...prev, [avatar.id]: false }));
            }
        }

        // 批量更新状态，只触发一次重新渲染
        if (Object.keys(imageUpdates).length > 0) {
            setAvatarTableData(prev => {
                const newData = prev.map(item =>
                    imageUpdates[item.id]
                        ? { ...item, avatarImage: imageUpdates[item.id] }
                        : item
                );
                return newData;
            });
        }
    };

    // Model/Knowledge data mapping
    const fetchModelList = async () => {
        setLoading(true);
        setApiError(null);
        try {
            const res = await adminService.getModelList({ page: 1, limit: 100 });
            if (res.success && res.data && res.data.models) {
                setModelTableData(res.data.models.map(m => ({
                    id: m.id,
                    name: m.name,
                    type: m.type,
                    status: m.status,
                    version: m.version,
                    owner: m.owner,
                    created_at: m.created_at,
                    tagColor: m.status?.toLowerCase() === 'active' ? 'green' : m.status?.toLowerCase() === 'inactive' ? 'yellow' : 'gray',
                    selected: m.selected
                })));
                // Sync total count
                setTotalCount(res.data.total || res.data.models.length);
            }
        } catch (e) {
            setApiError('Failed to get model list');
        } finally {
            setLoading(false);
        }
    };
    const fetchKnowledgeList = async () => {
        setLoading(true);
        setApiError(null);
        try {
            // 获取公共文件列表
            console.log('Fetching knowledge list...');
            const publicFilesRes = await adminService.getPublicFiles();
            console.log('Knowledge API response:', publicFilesRes);

            let knowledgeData = [];

            if (publicFilesRes.success && publicFilesRes.data) {
                console.log('Processing knowledge data:', publicFilesRes.data);

                // 处理公共文件数据 - 根据实际API返回格式
                if (publicFilesRes.data.files && Array.isArray(publicFilesRes.data.files)) {
                    console.log('Found files array:', publicFilesRes.data.files);
                    // API返回格式: { "files": ["file1.pdf", "file2.pdf", ...] }
                    knowledgeData = publicFilesRes.data.files.map((filename, index) => {
                        // 从文件名提取文件类型
                        const fileExtension = filename.split('.').pop()?.toLowerCase() || 'unknown';
                        const fileType = getFileTypeFromExtension(fileExtension);

                        return {
                            id: filename, // 使用文件名作为ID
                            filename: filename,
                            file_type: fileType,
                            file_size: 'Unknown', // API没有提供文件大小
                            upload_time: 'Unknown', // API没有提供上传时间
                            user_name: 'Admin', // 默认为Admin
                            status: 'active',
                            tagColor: 'green',
                            selected: false
                        };
                    });
                } else if (Array.isArray(publicFilesRes.data)) {
                    console.log('Data is direct array:', publicFilesRes.data);
                    // 如果直接返回数组格式
                    knowledgeData = publicFilesRes.data.map((filename, index) => {
                        const fileExtension = filename.split('.').pop()?.toLowerCase() || 'unknown';
                        const fileType = getFileTypeFromExtension(fileExtension);

                        return {
                            id: filename,
                            filename: filename,
                            file_type: fileType,
                            file_size: 'Unknown',
                            upload_time: 'Unknown',
                            user_name: 'Admin',
                            status: 'active',
                            tagColor: 'green',
                            selected: false
                        };
                    });
                } else {
                    console.log('Unexpected data format:', typeof publicFilesRes.data, publicFilesRes.data);
                }
            } else {
                console.log('API call failed or no data:', publicFilesRes);
            }

            console.log('Final knowledge data:', knowledgeData);
            setKnowledgeTableData(knowledgeData);
            setTotalCount(knowledgeData.length);
        } catch (e) {
            console.error('Error fetching knowledge list:', e);
            setApiError('Failed to get knowledge base list');
        } finally {
            setLoading(false);
        }
    };

    // 格式化文件大小
    const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    // 获取文件类型颜色
    const getFileTypeColor = (fileType) => {
        const typeColors = {
            'pdf': '#FF5252',
            'doc': '#2196F3',
            'docx': '#2196F3',
            'txt': '#4CAF50',
            'xls': '#FF9800',
            'xlsx': '#FF9800',
            'Unknown': '#9E9E9E'
        };
        return typeColors[fileType.toLowerCase()] || '#9E9E9E';
    };

    // 从文件扩展名获取文件类型
    const getFileTypeFromExtension = (extension) => {
        const extensionMap = {
            'pdf': 'PDF',
            'doc': 'DOC',
            'docx': 'DOCX',
            'txt': 'TXT',
            'xls': 'XLS',
            'xlsx': 'XLSX'
        };
        return extensionMap[extension.toLowerCase()] || 'Unknown';
    };

    const fetchUserActionLogs = async (currentPage = 1) => {
        setLoading(true);
        setApiError(null);
        try {
            // 构建搜索参数 - 直接使用后端接口期望的参数
            const searchParams = { page: currentPage, per_page: 10 };

            // 处理搜索条件，转换为后端接口期望的参数
            if (searchId) {
                // 如果searchId是数字，可能是用户ID
                const searchIdNum = parseInt(searchId);
                if (!isNaN(searchIdNum)) {
                    // 后端接口中没有target_user_id参数，暂时忽略
                    console.log('Search ID is number:', searchIdNum);
                }
            }
            if (searchInfo) {
                // searchInfo可能是邮箱或操作类型
                if (searchInfo.includes('@')) {
                    // 如果包含@，可能是邮箱
                    searchParams.operator_email = searchInfo;
                } else {
                    // 否则可能是操作类型
                    searchParams.action = searchInfo;
                }
            }

            console.log('Frontend search params:', searchParams); // 调试前端参数

            console.log('Sending searchParams:', searchParams); // 调试参数
            console.log('Current page being sent:', currentPage); // 调试当前页
            const res = await adminService.getUserLogs(searchParams);
            console.log('API Response:', res); // 调试信息
            console.log('Current page in API call:', currentPage); // 调试当前页
            if (res.success && res.data && res.data.logs) {
                console.log('Logs data length:', res.data.logs.length); // 调试数据长度
                console.log('Logs data:', res.data.logs); // 调试数据内容
                console.log('API response structure:', res.data); // 调试API响应结构

                const mappedData = res.data.logs.map(log => ({
                    id: String(log.id || ''),
                    operator_email: String(log.operator_email || ''),
                    action: String(log.action || ''),
                    target_user_id: String(log.target_user_id || ''),
                    target_user_email: String(log.target_user_email || ''),
                    reason: String(log.reason || ''),
                    details: log.details || '', // 保持details为对象，在渲染时处理
                    timestamp: String(log.timestamp || ''),
                    tagColor: getActionTagColor(log.action),
                    selected: false
                }));
                console.log('Setting logsTableData with length:', mappedData.length); // 调试信息
                setLogsTableData(mappedData);
                // Sync total count from API response
                const total = res.data.total || res.data.logs.length || 0;
                console.log('Setting totalCount:', total); // 调试信息
                setTotalCount(total);
            }
        } catch (e) {
            console.error('Error fetching user action logs:', e); // 调试错误
            setApiError('Failed to get user action logs');
        } finally {
            setLoading(false);
        }
    };

    // 获取操作类型的标签颜色
    const getActionTagColor = (action) => {
        const actionColors = {
            'create': 'green',
            'update': 'blue',
            'delete': 'red',
            'login': 'yellow',
            'logout': 'gray',
            'ban': 'red',
            'unban': 'green',
            'reset_password': 'orange'
        };
        return actionColors[action] || 'gray';
    };

    // 格式化时间戳
    const formatTimestamp = (timestamp) => {
        if (!timestamp) return '';
        try {
            const date = new Date(timestamp);
            return date.toLocaleString('en-US', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch (error) {
            return timestamp;
        }
    };

    // 格式化details对象
    const formatDetails = (details) => {
        if (!details) return '';
        if (typeof details === 'string') return details;
        if (typeof details === 'object') {
            try {
                // 将对象转换为更易读的格式
                const formattedDetails = Object.entries(details).map(([key, value]) => {
                    if (Array.isArray(value)) {
                        return `${key}: ${value.join(' → ')}`;
                    } else {
                        return `${key}: ${value}`;
                    }
                }).join(', ');
                return formattedDetails;
            } catch (error) {
                return JSON.stringify(details);
            }
        }
        return String(details);
    };

    // useEffect根據selectedMenu自動拉取
    useEffect(() => {
        if (selectedMenu === 'user') {
            fetchUserList();
        } else if (selectedMenu === 'avatar') {
            fetchAvatarList();
        } else if (selectedMenu === 'model') {
            fetchModelList();
        } else if (selectedMenu === 'knowledge') {
            fetchKnowledgeList();
        } else if (selectedMenu === 'logs') {
            fetchUserActionLogs(1); // 确保从第一页开始
        }
    }, [selectedMenu]);

    // 头像与退出按钮相关
    let avatar = null;
    const userStr = localStorage.getItem('user');
    if (userStr) {
        const user = JSON.parse(userStr);
        avatar = user.avatar || user.avatar_url || null;
    }
    const avatarSrc = imgError || !avatar ? DEFAULT_AVATAR : (avatar.startsWith('http') ? avatar : `${BASE_URL}${avatar}`);
    const handleLogoutClick = () => {
        if (window.confirm('Are you sure you want to log out?')) {
            if (onLogout) onLogout();
        }
    };

    // 根據 selectedMenu 取得對應數據和 set 方法
    const data = React.useMemo(() => {
        if (selectedMenu === 'user') {
            return userTableData;
        } else if (selectedMenu === 'avatar') {
            return avatarTableData;
        } else if (selectedMenu === 'knowledge') {
            return knowledgeTableData;
        } else if (selectedMenu === 'model') {
            return modelTableData;
        } else if (selectedMenu === 'logs') {
            return logsTableData;
        }
        return userTableData;
    }, [selectedMenu, userTableData, avatarTableData, modelTableData, knowledgeTableData, logsTableData]);

    // 當切換管理界面時，重置分頁和選中狀態
    useEffect(() => {
        setPage(1);
        setSearchId('');
        setSearchInfo('');
        // 設置第一個數據為選中狀態
        const currentData = data;
        if (currentData.length > 0) {
            setSelectedRow(currentData[0].id);
        } else {
            setSelectedRow('');
        }
    }, [selectedMenu]); // 移除data依赖，只在selectedMenu变化时重置

    // 处理搜索变化 - 对于logs管理界面，使用防抖重新获取数据
    useEffect(() => {
        if (selectedMenu === 'logs') {
            // 使用防抖，避免频繁调用API
            const timeoutId = setTimeout(() => {
                setPage(1);
                fetchUserActionLogs(1);
            }, 500); // 500ms防抖

            return () => clearTimeout(timeoutId);
        }
    }, [searchId, searchInfo, selectedMenu]);

    const setData = (rows) => {
        if (selectedMenu === 'user') {
            setUserTableData(rows);
        } else if (selectedMenu === 'avatar') {
            setAvatarTableData(rows);
        } else if (selectedMenu === 'knowledge') {
            setKnowledgeTableData(rows);
        } else if (selectedMenu === 'model') {
            setModelTableData(rows);
        } else if (selectedMenu === 'logs') {
            setLogsTableData(rows);
        }
    };

    // 過濾邏輯根據不同表格自動適配
    // 对于logs管理界面，使用服务器端搜索，不进行本地过滤
    const filteredData = selectedMenu === 'logs'
        ? data
        : data.filter(row =>
            (!searchId || row.id?.includes(searchId)) &&
            (!searchInfo || Object.values(row).some(v => typeof v === 'string' && v.includes(searchInfo)))
        );
    const resultsPerPage = selectedMenu === 'logs' ? 10 : 5;

    // 对于logs管理界面，使用服务器端分页
    const pageCount = selectedMenu === 'logs'
        ? Math.ceil(totalCount / resultsPerPage)
        : Math.ceil(filteredData.length / resultsPerPage);

    // 对于logs管理界面，直接使用API返回的数据，不进行本地分页
    // 对于logs管理界面，API已经返回了当前页的数据，所以直接使用
    const pagedData = selectedMenu === 'logs'
        ? data // 直接使用API返回的数据，因为API已经返回了当前页的数据
        : filteredData.slice((page - 1) * resultsPerPage, page * resultsPerPage);

    // 调试信息
    if (selectedMenu === 'logs') {
        console.log('Logs pagination debug:', {
            totalCount,
            resultsPerPage,
            pageCount,
            currentPage: page,
            dataLength: data.length,
            pagedDataLength: pagedData.length
        });
    }

    const handleRowSelect = (rowId) => {
        setSelectedRow(rowId);
    };

    const handleEdit = (rowId) => {
        const row = data.find(r => r.id === rowId);
        setModalEdit(true);
        setModalInitial(row);
        setModalOpen(true);
    };

    const handleCreateNew = () => {
        setModalEdit(false);
        setModalInitial(null);
        setModalOpen(true);
    };

    const handleDelete = (rowId) => {
        setDeleteRowId(rowId);
        setDeleteModalOpen(true);
    };

    // 处理页码变化
    const handlePageChange = (newPage) => {
        console.log('Page change requested:', { from: page, to: newPage, selectedMenu }); // 调试信息
        if (selectedMenu === 'logs') {
            // 对于logs管理界面，重新调用API获取对应页的数据
            // 保持当前的搜索条件
            console.log('Calling fetchUserActionLogs with page:', newPage); // 调试信息
            fetchUserActionLogs(newPage);
        }
        setPage(newPage);
    };



    // 創建用戶
    const handleModalSave = async (form) => {
        if (modalEdit) {
            // 編輯
            if (selectedMenu === 'user') {
                const userId = form.id.replace(/^U/, '');
                await adminService.updateUser(userId, {
                    email: form.email,
                    username: form.username,
                    role: form.role,
                    status: form.status,
                    phone: form.phone,
                    full_name: form.full_name,
                    bio: form.bio
                });
                fetchUserList();
            } else if (selectedMenu === 'avatar') {
                // 编辑Avatar - 目前API不支持编辑，只支持创建和删除
                alert('Avatar editing is not supported yet. Please delete and recreate.');
                fetchAvatarList();
            }
        } else {
            // 新增
            if (selectedMenu === 'user') {
                await adminService.createUser({
                    email: form.email,
                    password: form.password || '123456',
                    username: form.username,
                    role: form.role,
                    status: form.status,
                    phone: form.phone,
                    full_name: form.full_name,
                    bio: form.bio
                });
                fetchUserList();
            } else if (selectedMenu === 'avatar') {
                // 创建Avatar
                try {
                    // 验证必需字段
                    if (!form.name) {
                        alert('Please enter avatar name');
                        return;
                    }
                    if (!form.prompt_face) {
                        alert('Please upload prompt face video (MP4)');
                        return;
                    }
                    if (!form.tts_model) {
                        alert('Please select TTS model');
                        return;
                    }
                    if (!form.avatar_model) {
                        alert('Please select avatar model');
                        return;
                    }

                    // 立即显示加载动画，防止网络超时错误
                    setIsCreatingAvatar(true);
                    setLoadingMessage('Creating avatar... This may take several minutes.');

                    try {
                        // 根据support_clone的值进行验证
                        if (form.support_clone === true) {
                            // 克隆模式：需要prompt_voice和ref_text，timbre必须为null
                            if (!form.prompt_voice) {
                                alert('Please upload prompt voice audio (WAV) when support_clone is true');
                                return;
                            }
                            if (!form.ref_text) {
                                alert('Please enter reference text when support_clone is true');
                                return;
                            }
                            if (form.timbre) {
                                alert('Timbre should be null when support_clone is true');
                                return;
                            }
                        } else {
                            // 非克隆模式：需要timbre，不需要prompt_voice和ref_text
                            if (!form.timbre) {
                                alert('Please select timbre when support_clone is false');
                                return;
                            }

                            // 验证timbre必须存在于模型对应的音色列表中
                            try {
                                const ttsModelsResult = await adminService.getTtsModels();
                                if (ttsModelsResult.success && ttsModelsResult.data) {
                                    let modelsArray = [];
                                    if (typeof ttsModelsResult.data === 'object' && !Array.isArray(ttsModelsResult.data)) {
                                        modelsArray = Object.entries(ttsModelsResult.data).map(([key, model]) => ({
                                            id: key,
                                            name: model.full_name || key,
                                            clone: model.clone,
                                            cur_timbre: model.cur_timbre,
                                            license: model.license,
                                            status: model.status,
                                            timbres: model.timbres
                                        }));
                                    } else if (Array.isArray(ttsModelsResult.data)) {
                                        modelsArray = ttsModelsResult.data;
                                    }

                                    const selectedModel = modelsArray.find(model => model.name === form.tts_model);
                                    if (selectedModel && selectedModel.timbres && Array.isArray(selectedModel.timbres)) {
                                        if (!selectedModel.timbres.includes(form.timbre)) {
                                            alert(`Selected timbre "${form.timbre}" is not available for the selected TTS model "${form.tts_model}". Available timbres: ${selectedModel.timbres.join(', ')}`);
                                            return;
                                        }
                                    } else {
                                        alert(`No timbres available for the selected TTS model "${form.tts_model}"`);
                                        return;
                                    }
                                } else {
                                    alert('Failed to fetch TTS models for validation');
                                    return;
                                }
                            } catch (error) {
                                console.error('Error fetching TTS models for validation:', error);
                                alert('Error validating timbre selection');
                                return;
                            }

                            if (form.prompt_voice) {
                                alert('Prompt voice should be null when support_clone is false');
                                return;
                            }
                            if (form.ref_text) {
                                alert('Reference text should be null when support_clone is false');
                                return;
                            }
                        }

                        const avatarData = {
                            name: form.name || null,
                            avatar_blur: form.avatar_blur !== undefined ? form.avatar_blur : false,
                            support_clone: form.support_clone !== undefined ? form.support_clone : null,
                            timbre: form.support_clone === true ? null : (form.timbre || null),
                            ref_text: form.support_clone === true ? (form.ref_text || null) : null,
                            tts_model: form.tts_model || null,
                            avatar_model: form.avatar_model || null,
                            prompt_face: form.prompt_face || null,
                            prompt_voice: form.support_clone === true ? (form.prompt_voice || null) : null
                        };

                        // 调试信息
                        console.log('Avatar data being sent:', avatarData);
                        console.log('Form data:', form);

                        const startTime = Date.now();
                        console.log('Creating avatar... This may take several minutes.');

                        const result = await adminService.createAvatar(avatarData);
                        const duration = Math.round((Date.now() - startTime) / 1000);

                        if (result.success) {
                            alert(`Avatar created successfully! (Completed in ${duration} seconds)`);
                            fetchAvatarList();
                        } else {
                            if (result.error === 'Request timeout') {
                                alert(`Avatar creation is still in progress. Please wait and check the status later. (Operation took ${duration} seconds)`);
                            } else {
                                alert(`Failed to create avatar: ${result.message}`);
                            }
                        }
                    } catch (error) {
                        alert(`Error creating avatar: ${error.message}`);
                    } finally {
                        setIsCreatingAvatar(false);
                        setLoadingMessage('');
                    }
                } catch (error) {
                    alert(`Error creating avatar: ${error.message}`);
                } finally {
                    setIsCreatingAvatar(false);
                    setLoadingMessage('');
                }
            }
        }
        setModalOpen(false);
    };

    // 刪除用戶
    const handleConfirmDelete = async () => {
        if (deleteRowId && selectedMenu === 'user') {
            const userId = deleteRowId.replace(/^U/, '');
            await adminService.deleteUser(userId);
            fetchUserList();
        } else if (deleteRowId && selectedMenu === 'avatar') {
            // 删除Avatar
            try {
                const result = await adminService.deleteAvatar(deleteRowId);
                if (result.success) {
                    alert('Avatar deleted successfully!');
                    fetchAvatarList();
                } else {
                    alert(`Failed to delete avatar: ${result.message}`);
                }
            } catch (error) {
                alert(`Error deleting avatar: ${error.message}`);
            }
        } else if (deleteRowId && selectedMenu === 'knowledge') {
            // 删除文件 - 使用文件名作为删除参数
            try {
                const result = await adminService.deleteFile(deleteRowId);
                if (result.success) {
                    alert('File deleted successfully!');
                    fetchKnowledgeList();
                } else {
                    alert(`Failed to delete file: ${result.message}`);
                }
            } catch (error) {
                alert(`Error deleting file: ${error.message}`);
            }
        }
        setDeleteModalOpen(false);
        setDeleteRowId(null);
    };

    // 文件上传处理
    const handleFileUpload = async (file) => {
        if (!file) return;

        setUploadingFile(true);
        try {
            const result = await adminService.uploadFile(file);
            if (result.success) {
                alert('File uploaded successfully!');
                fetchKnowledgeList();
                setSelectedFile(null);
            } else {
                alert(`Failed to upload file: ${result.message}`);
            }
        } catch (error) {
            alert(`Error uploading file: ${error.message}`);
        } finally {
            setUploadingFile(false);
        }
    };

    // 文件选择处理
    const handleFileSelect = (event) => {
        const file = event.target.files[0];
        if (file) {
            setSelectedFile(file);
        }
    };

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            height: '100vh',
            width: '100%',
            background: isDarkMode 
                ? 'linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%)'
                : 'linear-gradient(135deg, #fafbfc 0%, #f1f5f9 100%)',
            color: themeStyles.color,
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

            {/* 主内容容器 */}
            <div style={{
                position: 'relative',
                zIndex: 10,
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                background: themeStyles.containerBackground,
                backdropFilter: 'blur(20px)',
                borderRadius: '20px',
                margin: '16px',
                overflow: 'hidden',
                boxShadow: themeStyles.containerShadow,
                border: themeStyles.containerBorder,
                transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
            }}>
            {/* 全局加载动画 */}
            {isCreatingAvatar && (
                <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: isDarkMode ? 'rgba(0, 0, 0, 0.7)' : 'rgba(0, 0, 0, 0.5)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 9999,
                    backdropFilter: 'blur(10px)',
                }}>
                    <div style={{
                        background: themeStyles.cardBackground,
                        borderRadius: '16px',
                        padding: '32px',
                        boxShadow: themeStyles.cardShadow,
                        border: themeStyles.cardBorder,
                        maxWidth: '400px',
                        width: '90%'
                    }}>
                        <LoadingSpinner
                            message={loadingMessage}
                            size="large"
                        />
                    </div>
                </div>
            )}
            {/* 右上角头像 */}
            <div style={{ position: 'absolute', top: 24, right: 40, zIndex: 20, display: 'flex', alignItems: 'center', gap: 16 }}>
                {/* 头像和退出菜单 */}
                <div
                    style={{ position: 'relative', display: 'inline-block' }}
                    onMouseEnter={() => setShowMenu(true)}
                    onMouseLeave={() => setShowMenu(false)}
                >
                    <img
                        src={avatarSrc}
                        alt=""
                        style={{
                            width: 48,
                            height: 48,
                            borderRadius: '50%',
                            objectFit: 'cover',
                            border: isDarkMode ? '2px solid rgba(80, 80, 120, 0.5)' : '2px solid rgba(102, 126, 234, 0.3)',
                            boxShadow: themeStyles.cardShadow,
                            cursor: 'pointer',
                            background: isDarkMode ? 'rgba(30, 30, 50, 0.9)' : '#f0f0f0',
                            transition: 'all 0.3s ease',
                        }}
                        onError={() => setImgError(true)}
                    />
                    {showMenu && (
                        <div style={{
                            position: 'absolute',
                            top: 54,
                            right: 0,
                            background: themeStyles.cardBackground,
                            border: themeStyles.cardBorder,
                            borderRadius: 12,
                            boxShadow: themeStyles.cardShadow,
                            backdropFilter: 'blur(20px)',
                            minWidth: 120,
                            zIndex: 10,
                            padding: '8px 0',
                            textAlign: 'center',
                            transition: 'all 0.3s ease',
                        }}>
                            <button
                                onClick={handleLogoutClick}
                                style={{
                                    width: '100%',
                                    padding: '10px 0',
                                    background: 'none',
                                    color: isDarkMode ? '#e5e7eb' : '#667eea',
                                    border: 'none',
                                    borderRadius: 0,
                                    cursor: 'pointer',
                                    fontWeight: 500,
                                    fontSize: 16,
                                    transition: 'all 0.2s',
                                    outline: 'none'
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.background = isDarkMode ? 'rgba(40, 40, 60, 0.6)' : 'rgba(102, 126, 234, 0.1)';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.background = 'none';
                                }}
                                onMouseDown={e => e.preventDefault()}
                            >
                                Logout
                            </button>
                        </div>
                    )}
                </div>
            </div>
            {/* 標題和工具欄 */}
            <div style={{
                padding: '32px 32px 0 32px',
                background: themeStyles.toolbarBg,
                backdropFilter: 'blur(20px)',
                display: 'flex',
                flexDirection: 'column',
                gap: 16,
                borderBottom: isDarkMode ? '1px solid rgba(80, 80, 120, 0.3)' : '1px solid rgba(37, 99, 235, 0.1)',
                transition: 'all 0.3s ease',
            }}>
                <div style={{
                    fontWeight: 700,
                    fontSize: 28,
                    marginBottom: 8,
                    color: themeStyles.color,
                    transition: 'color 0.3s ease',
                }}>{config.title}</div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
                    <div style={{ display: 'flex', gap: 12 }}>
                        <input
                            type="text"
                            placeholder={selectedMenu === 'logs' ? `Search by Log ID` : `Search by ID`}
                            value={searchId}
                            onChange={e => setSearchId(e.target.value)}
                            style={{
                                padding: '10px 16px',
                                borderRadius: 8,
                                border: themeStyles.inputBorder,
                                fontSize: 15,
                                outline: 'none',
                                minWidth: 140,
                                background: themeStyles.inputBackground,
                                color: themeStyles.inputColor,
                                backdropFilter: 'blur(10px)',
                                transition: 'all 0.3s ease',
                                boxShadow: 'none',
                            }}
                            onFocus={(e) => {
                                e.currentTarget.style.boxShadow = isDarkMode ? '0 0 0 2px rgba(76, 76, 109, 0.4)' : '0 0 0 2px rgba(102, 126, 234, 0.2)';
                            }}
                            onBlur={(e) => {
                                e.currentTarget.style.boxShadow = 'none';
                            }}
                        />
                        <input
                            type="text"
                            placeholder={selectedMenu === 'logs' ? `Search by Email/Action` : `Filter by Info`}
                            value={searchInfo}
                            onChange={e => setSearchInfo(e.target.value)}
                            style={{
                                padding: '10px 16px',
                                borderRadius: 8,
                                border: themeStyles.inputBorder,
                                fontSize: 15,
                                outline: 'none',
                                minWidth: 140,
                                background: themeStyles.inputBackground,
                                color: themeStyles.inputColor,
                                backdropFilter: 'blur(10px)',
                                transition: 'all 0.3s ease',
                                boxShadow: 'none',
                            }}
                            onFocus={(e) => {
                                e.currentTarget.style.boxShadow = isDarkMode ? '0 0 0 2px rgba(76, 76, 109, 0.4)' : '0 0 0 2px rgba(102, 126, 234, 0.2)';
                            }}
                            onBlur={(e) => {
                                e.currentTarget.style.boxShadow = 'none';
                            }}
                        />
                    </div>
                    {selectedMenu !== 'logs' && (
                        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                            {selectedMenu === 'knowledge' ? (
                                <>
                                    <label htmlFor="file-upload" style={{
                                        display: 'inline-block',
                                        padding: '8px 16px',
                                        background: uploadingFile ? '#e0e0e0' : 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                                        color: '#fff',
                                        borderRadius: 8,
                                        cursor: uploadingFile ? 'not-allowed' : 'pointer',
                                        fontSize: 14,
                                        fontWeight: 500,
                                        transition: 'all 0.2s'
                                    }}>
                                        <input
                                            id="file-upload"
                                            type="file"
                                            style={{ display: 'none' }}
                                            onChange={handleFileSelect}
                                            disabled={uploadingFile}
                                        />
                                        {uploadingFile ? 'Uploading...' : 'Select File'}
                                    </label>
                                    {selectedFile && (
                                        <Button
                                            variant="contained"
                                            style={{
                                                background: uploadingFile ? '#e0e0e0' : '#1976d2',
                                                color: '#fff',
                                                fontWeight: 700,
                                                borderRadius: 8,
                                                fontSize: 14,
                                                padding: '8px 16px'
                                            }}
                                            onClick={() => handleFileUpload(selectedFile)}
                                            disabled={uploadingFile}
                                        >
                                            {uploadingFile ? 'Uploading...' : 'Upload File'}
                                        </Button>
                                    )}
                                </>
                            ) : selectedMenu === 'model' ? (
                                // 模型管理界面不显示创建按钮
                                null
                            ) : (
                                <button
                                    onClick={handleCreateNew}
                                    style={{
                                        background: themeStyles.createBtn,
                                        color: themeStyles.createBtnText,
                                        fontWeight: 700,
                                        borderRadius: 10,
                                        fontSize: 16,
                                        padding: '10px 32px',
                                        border: 'none',
                                        cursor: 'pointer',
                                        boxShadow: isDarkMode ? '0 4px 16px rgba(76, 76, 109, 0.5)' : '0 4px 16px rgba(102, 126, 234, 0.25)',
                                        transition: 'all 0.3s ease',
                                        backdropFilter: 'blur(10px)',
                                    }}
                                    onMouseEnter={(e) => {
                                        e.currentTarget.style.transform = 'translateY(-2px)';
                                        e.currentTarget.style.boxShadow = isDarkMode ? '0 8px 24px rgba(76, 76, 109, 0.6)' : '0 8px 24px rgba(102, 126, 234, 0.35)';
                                    }}
                                    onMouseLeave={(e) => {
                                        e.currentTarget.style.transform = 'translateY(0)';
                                        e.currentTarget.style.boxShadow = isDarkMode ? '0 4px 16px rgba(76, 76, 109, 0.5)' : '0 4px 16px rgba(102, 126, 234, 0.25)';
                                    }}
                                >
                                    Create New One
                                </button>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* 信息表格 */}
            <div style={{ flex: 1, overflow: 'auto', padding: 32 }}>
                <table style={{
                    width: '100%',
                    borderCollapse: 'separate',
                    borderSpacing: 0,
                    background: themeStyles.cardBackground,
                    borderRadius: 16,
                    boxShadow: themeStyles.cardShadow,
                    border: themeStyles.cardBorder,
                    overflow: 'hidden',
                    backdropFilter: 'blur(20px)',
                    transition: 'all 0.3s ease',
                }}>
                    <thead>
                        <tr>
                            {config.columns.map(col => (
                                <th key={col.key} style={{
                                    padding: '12px 8px',
                                    background: themeStyles.tableHeader,
                                    borderBottom: `2px solid ${themeStyles.tableBorder}`,
                                    fontWeight: 700,
                                    fontSize: 15,
                                    textAlign: 'left',
                                    maxWidth: selectedMenu === 'logs' && (col.key === 'operator_email' || col.key === 'target_user_email' || col.key === 'details') ? '200px' : 'auto'
                                }}>{col.label}</th>
                            ))}
                            {selectedMenu !== 'model' && (
                                <th style={{ padding: '12px 8px', background: themeStyles.tableHeader, borderBottom: `2px solid ${themeStyles.tableBorder}`, fontWeight: 700, fontSize: 15, textAlign: 'center' }}>Actions</th>
                            )}
                        </tr>
                    </thead>
                    <tbody>
                        {pagedData.map((row, idx) => (
                            <tr
                                key={row.id}
                                style={{
                                    background: row.id === selectedRow ? themeStyles.tableRowSelected : themeStyles.tableRow,
                                    transition: 'all 0.2s ease',
                                    cursor: 'pointer'
                                }}
                                onClick={() => handleRowSelect(row.id)}
                                onMouseEnter={(e) => {
                                    if (row.id !== selectedRow) {
                                        e.currentTarget.style.background = themeStyles.tableRowHover;
                                        e.currentTarget.style.transform = 'scale(1.005)';
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    if (row.id !== selectedRow) {
                                        e.currentTarget.style.background = themeStyles.tableRow;
                                        e.currentTarget.style.transform = 'scale(1)';
                                    }
                                }}
                            >
                                {config.columns.map(col => (
                                    <td key={col.key} style={{
                                        padding: '10px 8px',
                                        borderBottom: `1px solid ${themeStyles.tableBorder}`,
                                        fontSize: 15,
                                        textAlign: 'left',
                                        color: themeStyles.color,
                                        transition: 'color 0.3s ease',
                                        maxWidth: selectedMenu === 'logs' && (col.key === 'operator_email' || col.key === 'target_user_email' || col.key === 'details') ? '200px' : 'auto',
                                        overflow: selectedMenu === 'logs' && (col.key === 'operator_email' || col.key === 'target_user_email' || col.key === 'details') ? 'hidden' : 'visible',
                                        textOverflow: selectedMenu === 'logs' && (col.key === 'operator_email' || col.key === 'target_user_email' || col.key === 'details') ? 'ellipsis' : 'clip',
                                        whiteSpace: selectedMenu === 'logs' && (col.key === 'operator_email' || col.key === 'target_user_email' || col.key === 'details') ? 'nowrap' : 'normal'
                                    }}>
                                        {col.key === 'avatar' ? (
                                            <img src={row.avatar ? (row.avatar.startsWith('http') ? row.avatar : `${BASE_URL}${row.avatar}`) : DEFAULT_AVATAR} alt="avatar" style={{ width: 32, height: 32, borderRadius: '50%', objectFit: 'cover', background: '#f0f0f0' }} />
                                        ) : col.key === 'avatarImage' ? (
                                            <div style={{ position: 'relative', width: 80, height: 80 }}>
                                                {loadingImages[row.id] ? (
                                                    <div style={{
                                                        width: 80,
                                                        height: 80,
                                                        borderRadius: 8,
                                                        background: '#f0f0f0',
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'center',
                                                        border: '2px dashed #e0e0e0'
                                                    }}>
                                                        <div style={{
                                                            width: 20,
                                                            height: 20,
                                                            border: '2px solid #e0e0e0',
                                                            borderTop: '2px solid #1976d2',
                                                            borderRadius: '50%',
                                                            animation: 'spin 1s linear infinite'
                                                        }}></div>
                                                    </div>
                                                ) : (
                                                    <img
                                                        src={row.avatarImage || DEFAULT_AVATAR}
                                                        alt="avatar preview"
                                                        style={{
                                                            width: 80,
                                                            height: 80,
                                                            borderRadius: 8,
                                                            objectFit: 'cover',
                                                            background: '#f0f0f0',
                                                            border: '2px solid #e0e0e0'
                                                        }}
                                                        onError={(e) => {
                                                            e.target.src = DEFAULT_AVATAR;
                                                        }}
                                                    />
                                                )}
                                            </div>
                                        ) : col.key === 'image' ? (
                                            <img src={row.image || DEFAULT_AVATAR} alt="avatar" style={{ width: 48, height: 64, borderRadius: 8, objectFit: 'cover', background: '#f0f0f0' }} />
                                        ) : col.key === 'description' ? (
                                            <div style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={row[col.key]}>
                                                {row[col.key]}
                                            </div>
                                        ) : col.key === 'avatar_blur' && selectedMenu === 'avatar' ? (
                                            <span style={{
                                                display: 'inline-block',
                                                background: avatarStatusColorMap[row[col.key]] || '#eee',
                                                color: '#fff',
                                                borderRadius: 8,
                                                padding: '2px 12px',
                                                fontWeight: 700,
                                                fontSize: 13
                                            }}>{row[col.key]}</span>
                                        ) : col.key === 'support_clone' && selectedMenu === 'avatar' ? (
                                            <span style={{
                                                display: 'inline-block',
                                                background: avatarStatusColorMap[row[col.key]] || '#eee',
                                                color: '#fff',
                                                borderRadius: 8,
                                                padding: '2px 12px',
                                                fontWeight: 700,
                                                fontSize: 13
                                            }}>{row[col.key]}</span>
                                        ) : col.key === 'timestamp' && selectedMenu === 'logs' ? (
                                            <span style={{ fontSize: 13, color: '#666' }}>
                                                {formatTimestamp(row[col.key])}
                                            </span>
                                        ) : col.key === 'details' && selectedMenu === 'logs' ? (
                                            <div style={{
                                                maxWidth: 200,
                                                overflow: 'hidden',
                                                textOverflow: 'ellipsis',
                                                whiteSpace: 'nowrap',
                                                fontSize: 13,
                                                color: '#666'
                                            }} title={formatDetails(row[col.key])}>
                                                {formatDetails(row[col.key])}
                                            </div>
                                        ) : col.key === 'file_type' && selectedMenu === 'knowledge' ? (
                                            <span style={{
                                                display: 'inline-block',
                                                background: getFileTypeColor(row[col.key]),
                                                color: '#fff',
                                                borderRadius: 8,
                                                padding: '2px 12px',
                                                fontWeight: 700,
                                                fontSize: 13
                                            }}>{row[col.key]}</span>
                                        ) : col.isTag ? (
                                            <span style={{
                                                display: 'inline-block',
                                                background: themeStyles.tagBg(row.tagColor),
                                                color: themeStyles.tagText,
                                                borderRadius: 8,
                                                padding: '2px 12px',
                                                fontWeight: 700,
                                                fontSize: 13
                                            }}>{row[col.key]}</span>
                                        ) : (
                                            (() => {
                                                const value = row[col.key];
                                                // 安全检查：只渲染基本类型
                                                if (value === null || value === undefined) {
                                                    return '';
                                                }
                                                if (typeof value === 'object') {
                                                    // 如果是对象，尝试转换为字符串或显示对象信息
                                                    try {
                                                        return JSON.stringify(value);
                                                    } catch (error) {
                                                        return '[Object]';
                                                    }
                                                }
                                                return String(value);
                                            })()
                                        )}
                                    </td>
                                ))}
                                {selectedMenu !== 'model' && (
                                    <td style={{ padding: '10px 8px', borderBottom: `1px solid ${themeStyles.tableBorder}`, textAlign: 'center' }}>
                                        <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
                                            {selectedMenu === 'knowledge' ? (
                                                <IconButton
                                                    style={{
                                                        background: row.id === selectedRow ? '#FFE5E5' : '#f8f9fa',
                                                        color: row.id === selectedRow ? '#FF5252' : '#FF5252',
                                                        borderRadius: 8
                                                    }}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleDelete(row.id);
                                                    }}
                                                >
                                                    <Delete />
                                                </IconButton>
                                            ) : (
                                                <>
                                                    {selectedMenu !== 'avatar' && selectedMenu !== 'logs' && (
                                                        <IconButton
                                                            style={{
                                                                background: hoveredEditBtn === row.id ? 'rgba(255, 82, 82, 0.1)' : 'transparent',
                                                                color: hoveredEditBtn === row.id ? '#FF5252' : (isDarkMode ? '#888' : '#bbb'),
                                                                borderRadius: 8,
                                                                transition: 'all 0.2s ease'
                                                            }}
                                                            onMouseEnter={() => setHoveredEditBtn(row.id)}
                                                            onMouseLeave={() => setHoveredEditBtn(null)}
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                handleEdit(row.id);
                                                            }}
                                                        >
                                                            <Edit />
                                                        </IconButton>
                                                    )}
                                                    {selectedMenu !== 'logs' && (
                                                        <IconButton
                                                            style={{
                                                                background: hoveredDeleteBtn === row.id ? 'rgba(255, 82, 82, 0.1)' : 'transparent',
                                                                color: hoveredDeleteBtn === row.id ? '#FF5252' : (isDarkMode ? '#888' : '#bbb'),
                                                                borderRadius: 8,
                                                                transition: 'all 0.2s ease'
                                                            }}
                                                            onMouseEnter={() => setHoveredDeleteBtn(row.id)}
                                                            onMouseLeave={() => setHoveredDeleteBtn(null)}
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                handleDelete(row.id);
                                                            }}
                                                        >
                                                            <Delete />
                                                        </IconButton>
                                                    )}
                                                </>
                                            )}
                                        </div>
                                    </td>
                                )}
                            </tr>
                        ))}
                    </tbody>
                </table>

                {/* 分頁欄 */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginTop: 24,
                    padding: '16px 20px',
                    background: themeStyles.toolbarBg,
                    backdropFilter: 'blur(20px)',
                    borderRadius: 12,
                    border: themeStyles.cardBorder,
                    boxShadow: themeStyles.cardShadow,
                    transition: 'all 0.3s ease',
                }}>
                    <div style={{
                        fontSize: 15,
                        color: isDarkMode ? '#9ca3af' : '#888',
                        transition: 'color 0.3s ease',
                    }}>
                        {selectedMenu === 'logs' ? (
                            totalCount > 0 ? (
                                `Showing ${(page - 1) * resultsPerPage + 1} to ${Math.min(page * resultsPerPage, totalCount)} of ${totalCount} results`
                            ) : (
                                'No results found'
                            )
                        ) : (
                            `Showing ${filteredData.length === 0 ? 0 : (page - 1) * resultsPerPage + 1} to ${Math.min(page * resultsPerPage, filteredData.length)} of ${totalCount || filteredData.length} results`
                        )}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                        {pageCount > 0 ? (
                            Array.from({ length: pageCount }, (_, i) => (
                                <button
                                    key={i}
                                    onClick={() => handlePageChange(i + 1)}
                                    style={{
                                        background: themeStyles.pageBtn(page === i + 1),
                                        color: themeStyles.pageBtnText(page === i + 1),
                                        border: 'none',
                                        borderRadius: 8,
                                        padding: '8px 16px',
                                        fontWeight: 700,
                                        fontSize: 15,
                                        cursor: 'pointer',
                                        boxShadow: page === i + 1 
                                            ? (isDarkMode ? '0 4px 16px rgba(76, 76, 109, 0.5)' : '0 4px 16px rgba(102, 126, 234, 0.25)')
                                            : 'none',
                                        transition: 'all 0.3s ease',
                                        backdropFilter: 'blur(10px)',
                                    }}
                                    onMouseEnter={(e) => {
                                        if (page !== i + 1) {
                                            e.currentTarget.style.transform = 'translateY(-2px)';
                                            e.currentTarget.style.boxShadow = isDarkMode ? '0 4px 16px rgba(76, 76, 109, 0.3)' : '0 4px 16px rgba(102, 126, 234, 0.15)';
                                        }
                                    }}
                                    onMouseLeave={(e) => {
                                        if (page !== i + 1) {
                                            e.currentTarget.style.transform = 'translateY(0)';
                                            e.currentTarget.style.boxShadow = 'none';
                                        }
                                    }}
                                >
                                    {i + 1}
                                </button>
                            ))
                        ) : (
                            <div style={{
                                fontSize: 15,
                                color: isDarkMode ? '#6b7280' : '#888',
                                transition: 'color 0.3s ease',
                            }}>No data available</div>
                        )}
                    </div>
                </div>
            </div>
            {/* 新增/編輯彈窗 */}
            <CreateEditModal
                open={modalOpen}
                onClose={() => setModalOpen(false)}
                onSave={handleModalSave}
                columns={config.columns}
                initialData={modalInitial}
                isEdit={modalEdit}
                selectedMenu={selectedMenu}
            />
            {/* 刪除確認對話框 */}
            <Dialog
                open={deleteModalOpen}
                onClose={() => setDeleteModalOpen(false)}
                maxWidth="sm"
                fullWidth
                PaperProps={{
                    style: {
                        borderRadius: 20,
                        boxShadow: themeStyles.containerShadow,
                        overflow: 'hidden',
                        background: themeStyles.cardBackground,
                        backdropFilter: 'blur(20px)',
                        border: themeStyles.cardBorder,
                    }
                }}
            >
                <DialogTitle
                    style={{
                        background: isDarkMode ? 'rgba(139, 0, 0, 0.2)' : '#fff5f5',
                        borderBottom: isDarkMode ? '1px solid rgba(139, 0, 0, 0.3)' : '1px solid #fed7d7',
                        padding: '20px 24px',
                        margin: 0,
                        fontSize: 18,
                        fontWeight: 600,
                        color: isDarkMode ? '#fca5a5' : '#c53030',
                        transition: 'all 0.3s ease',
                    }}
                >
                    Confirm Delete
                </DialogTitle>
                <DialogContent style={{
                    padding: '24px',
                    background: themeStyles.cardBackground,
                }}>
                    <div style={{
                        fontSize: 16,
                        color: themeStyles.color,
                        lineHeight: 1.5,
                        transition: 'color 0.3s ease',
                    }}>
                        Are you sure you want to delete this record? This action cannot be undone.
                    </div>
                </DialogContent>
                <DialogActions style={{
                    padding: '16px 24px',
                    gap: 12,
                    background: isDarkMode ? 'rgba(30, 30, 50, 0.5)' : '#f8f9fa',
                    borderTop: isDarkMode ? '1px solid rgba(80, 80, 120, 0.3)' : '1px solid #e9ecef',
                    transition: 'all 0.3s ease',
                }}>
                    <button
                        onClick={() => setDeleteModalOpen(false)}
                        style={{
                            background: themeStyles.buttonSecondary,
                            color: themeStyles.buttonSecondaryText,
                            fontWeight: 600,
                            fontSize: 15,
                            padding: '8px 24px',
                            borderRadius: 8,
                            border: themeStyles.cardBorder,
                            cursor: 'pointer',
                            transition: 'all 0.3s ease',
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.transform = 'translateY(-2px)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.transform = 'translateY(0)';
                        }}
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleConfirmDelete}
                        style={{
                            background: 'linear-gradient(135deg, #FF5252 0%, #d32f2f 100%)',
                            color: 'white',
                            fontWeight: 600,
                            fontSize: 15,
                            borderRadius: 8,
                            padding: '8px 24px',
                            border: 'none',
                            cursor: 'pointer',
                            boxShadow: '0 4px 16px rgba(255, 82, 82, 0.3)',
                            transition: 'all 0.3s ease',
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.transform = 'translateY(-2px)';
                            e.currentTarget.style.boxShadow = '0 8px 24px rgba(255, 82, 82, 0.4)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.transform = 'translateY(0)';
                            e.currentTarget.style.boxShadow = '0 4px 16px rgba(255, 82, 82, 0.3)';
                        }}
                    >
                        Delete
                    </button>
                </DialogActions>
            </Dialog>
            </div>
        </div>
    );
}

export default UserTable; 