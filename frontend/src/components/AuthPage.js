import React, { useState } from 'react';
import {
    Container,
    Paper,
    TextField,
    Button,
    Typography,
    Box,
    Tabs,
    Tab,
    IconButton,
    InputAdornment,
    Alert,
    CircularProgress,
    FormControlLabel,
    Checkbox
} from '@mui/material';
import {
    Visibility,
    VisibilityOff,
    Person,
    Lock,
    Email
} from '@mui/icons-material';
import authService from '../services/authService';

function AuthPage({ onLoginSuccess }) {
    const [tabValue, setTabValue] = useState(0);
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // Login form state
    const [loginForm, setLoginForm] = useState({
        email: '',
        password: ''
    });

    // Registration form state
    const [registerForm, setRegisterForm] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        code: ''
    });

    // Password validation state
    const [passwordValidation, setPasswordValidation] = useState({
        length: false,
        uppercase: false,
        lowercase: false,
        number: false,
        special: false
    });

    // Password strength calculation
    const getPasswordStrength = () => {
        const validations = Object.values(passwordValidation);
        const validCount = validations.filter(Boolean).length;

        if (validCount === 0) return { strength: 'Very Weak', color: '#ef4444', width: '20%' };
        if (validCount === 1) return { strength: 'Weak', color: '#f97316', width: '40%' };
        if (validCount === 2) return { strength: 'Fair', color: '#eab308', width: '60%' };
        if (validCount === 3) return { strength: 'Good', color: '#84cc16', width: '80%' };
        if (validCount === 4) return { strength: 'Strong', color: '#22c55e', width: '90%' };
        if (validCount === 5) return { strength: 'Very Strong', color: '#10b981', width: '100%' };

        return { strength: 'Very Weak', color: '#ef4444', width: '20%' };
    };

    // Verification code related state
    const [verificationCodeSent, setVerificationCodeSent] = useState(false);
    const [codeCountdown, setCodeCountdown] = useState(0);

    const passwordsFilled = Boolean(registerForm.password) && Boolean(registerForm.confirmPassword);
    const isPasswordMismatch = passwordsFilled && registerForm.password !== registerForm.confirmPassword;

    const handleTabChange = (event, newValue) => {
        setTabValue(newValue);
        setError('');
        setSuccess('');
        setVerificationCodeSent(false);
        setCodeCountdown(0);
        // 重置密码验证状态
        setPasswordValidation({
            length: false,
            uppercase: false,
            lowercase: false,
            number: false,
            special: false
        });
    };

    const handleLoginChange = (e) => {
        setLoginForm({
            ...loginForm,
            [e.target.name]: e.target.value
        });
    };

    const handleRegisterChange = (e) => {
        const { name, value } = e.target;
        setRegisterForm({
            ...registerForm,
            [name]: value
        });

        // 密码验证逻辑
        if (name === 'password') {
            const password = value;
            setPasswordValidation({
                length: password.length >= 8,
                uppercase: /[A-Z]/.test(password),
                lowercase: /[a-z]/.test(password),
                number: /\d/.test(password),
                special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)
            });
        }
    };

    // Send verification code
    const handleSendVerificationCode = async () => {
        if (!registerForm.email) {
            setError('Please enter your email first');
            return;
        }

        if (registerForm.password && registerForm.confirmPassword && registerForm.password !== registerForm.confirmPassword) {
            return;
        }

        setLoading(true);
        setError('');

        try {
            const result = await authService.sendVerificationCode({
                email: registerForm.email,
                purpose: 'register'
            });

            if (result.success) {
                setSuccess(result.message);
                setVerificationCodeSent(true);
                // Start countdown
                setCodeCountdown(60);
                const timer = setInterval(() => {
                    setCodeCountdown((prev) => {
                        if (prev <= 1) {
                            clearInterval(timer);
                            return 0;
                        }
                        return prev - 1;
                    });
                }, 1000);
            } else {
                setError(result.message);
            }
        } catch (error) {
            setError('Failed to send verification code, please try again later');
        } finally {
            setLoading(false);
        }
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');

        try {
            const result = await authService.login(loginForm);

            if (result.success) {
                setSuccess(result.message);
                // Call parent component callback
                setTimeout(() => {
                    onLoginSuccess(authService.getCurrentUser());
                }, 1000);
            } else {
                setError(result.message);
            }
        } catch (error) {
            setError('Login failed, please try again later');
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');

        // Validate password
        if (registerForm.password !== registerForm.confirmPassword) {
            setError('Passwords do not match');
            setLoading(false);
            return;
        }

        // 密码复杂度验证
        const password = registerForm.password;
        const minLength = 8;
        const hasUpperCase = /[A-Z]/.test(password);
        const hasLowerCase = /[a-z]/.test(password);
        const hasNumbers = /\d/.test(password);
        const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);

        if (password.length < minLength) {
            setError(`Password must be at least ${minLength} characters long!`);
            setLoading(false);
            return;
        }
        if (!hasUpperCase) {
            setError('Password must contain at least one uppercase letter (A-Z)!');
            setLoading(false);
            return;
        }
        if (!hasLowerCase) {
            setError('Password must contain at least one lowercase letter (a-z)!');
            setLoading(false);
            return;
        }
        if (!hasNumbers) {
            setError('Password must contain at least one number (0-9)!');
            setLoading(false);
            return;
        }
        if (!hasSpecialChar) {
            setError('Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.)!');
            setLoading(false);
            return;
        }

        // Validate verification code
        if (!registerForm.code) {
            setError('Please enter verification code');
            setLoading(false);
            return;
        }

        try {
            const result = await authService.register({
                email: registerForm.email,
                password: registerForm.password,
                code: registerForm.code,
                role: 'student' // 所有注册用户默认为student角色
            });

            if (result.success) {
                setSuccess(result.message);
                // After successful registration, automatically switch to login page
                setTimeout(() => {
                    setTabValue(0);
                    setLoginForm({
                        email: registerForm.email,
                        password: registerForm.password
                    });
                    setVerificationCodeSent(false);
                    setCodeCountdown(0);
                    // 重置密码验证状态
                    setPasswordValidation({
                        length: false,
                        uppercase: false,
                        lowercase: false,
                        number: false,
                        special: false
                    });
                }, 2000);
            } else {
                setError(result.message);
            }
        } catch (error) {
            setError('Registration failed, please try again later');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container component="main" maxWidth="sm">
            <Box
                sx={{
                    marginTop: 8,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    minHeight: '100vh',
                    justifyContent: 'center',
                }}
            >
                <Paper
                    elevation={0}
                    sx={{
                        padding: 6,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        width: '100%',
                        borderRadius: 4,
                        background: 'rgba(255, 255, 255, 0.9)',
                        backdropFilter: 'blur(20px)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        boxShadow: '0 8px 32px rgba(37, 99, 235, 0.08)',
                    }}
                >
                    <Box sx={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: 2, 
                        mb: 4,
                        background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        backgroundClip: 'text',
                    }}>
                        <Typography component="h1" variant="h3" sx={{ 
                            fontWeight: 700,
                            letterSpacing: '-0.025em',
                        }}>
                            Virtual Mentor
                        </Typography>
                    </Box>

                    <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 3 }}>
                        <Tab label="Login" />
                        <Tab label="Register" />
                    </Tabs>

                    {error && (
                        <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
                            {error}
                        </Alert>
                    )}

                    {success && (
                        <Alert severity="success" sx={{ width: '100%', mb: 2 }}>
                            {success}
                        </Alert>
                    )}

                    {tabValue === 0 && (
                        <Box component="form" onSubmit={handleLogin} sx={{ width: '100%' }}>
                            <TextField
                                margin="normal"
                                required
                                fullWidth
                                id="email"
                                label="Email"
                                name="email"
                                autoComplete="email"
                                autoFocus
                                value={loginForm.email}
                                onChange={handleLoginChange}
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <Email />
                                        </InputAdornment>
                                    ),
                                }}
                            />
                            <TextField
                                margin="normal"
                                required
                                fullWidth
                                name="password"
                                label="Password"
                                type={showPassword ? 'text' : 'password'}
                                id="password"
                                autoComplete="current-password"
                                value={loginForm.password}
                                onChange={handleLoginChange}
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <Lock />
                                        </InputAdornment>
                                    ),
                                    endAdornment: (
                                        <InputAdornment position="end">
                                            <IconButton
                                                onClick={() => setShowPassword(!showPassword)}
                                                edge="end"
                                            >
                                                {showPassword ? <VisibilityOff /> : <Visibility />}
                                            </IconButton>
                                        </InputAdornment>
                                    ),
                                }}
                            />
                            <Button
                                type="submit"
                                fullWidth
                                variant="contained"
                                sx={{ mt: 3, mb: 2, py: 1.5 }}
                                disabled={loading}
                            >
                                {loading ? <CircularProgress size={24} /> : 'Login'}
                            </Button>
                        </Box>
                    )}

                    {tabValue === 1 && (
                        <Box component="form" onSubmit={handleRegister} sx={{ width: '100%' }}>
                            <TextField
                                margin="normal"
                                required
                                fullWidth
                                id="email"
                                label="Email"
                                name="email"
                                autoComplete="email"
                                autoFocus
                                value={registerForm.email}
                                onChange={handleRegisterChange}
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <Email />
                                        </InputAdornment>
                                    ),
                                }}
                            />

                            <TextField
                                margin="normal"
                                required
                                fullWidth
                                name="password"
                                label="Password"
                                type={showPassword ? 'text' : 'password'}
                                id="password"
                                autoComplete="new-password"
                                value={registerForm.password}
                                onChange={handleRegisterChange}
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <Lock />
                                        </InputAdornment>
                                    ),
                                    endAdornment: (
                                        <InputAdornment position="end">
                                            <IconButton
                                                onClick={() => setShowPassword(!showPassword)}
                                                edge="end"
                                            >
                                                {showPassword ? <VisibilityOff /> : <Visibility />}
                                            </IconButton>
                                        </InputAdornment>
                                    ),
                                }}
                            />

                            {/* Password requirements */}
                            {registerForm.password && (
                                <Box sx={{ mt: 1, p: 2, bgcolor: '#f8fafc', borderRadius: 1, border: '1px solid #e2e8f0' }}>
                                    {/* Password strength indicator */}
                                    <Box sx={{ mb: 2 }}>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                            <Typography variant="body2" sx={{ fontWeight: 500, color: '#374151' }}>
                                                Password Strength:
                                            </Typography>
                                            <Typography variant="body2" sx={{
                                                fontWeight: 600,
                                                color: getPasswordStrength().color
                                            }}>
                                                {getPasswordStrength().strength}
                                            </Typography>
                                        </Box>
                                        <Box sx={{
                                            width: '100%',
                                            height: 6,
                                            bgcolor: '#e5e7eb',
                                            borderRadius: 3,
                                            overflow: 'hidden'
                                        }}>
                                            <Box sx={{
                                                width: getPasswordStrength().width,
                                                height: '100%',
                                                bgcolor: getPasswordStrength().color,
                                                transition: 'all 0.3s ease'
                                            }} />
                                        </Box>
                                    </Box>

                                    <Typography variant="body2" sx={{ mb: 1, fontWeight: 500, color: '#374151' }}>
                                        Password Requirements:
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Box sx={{
                                                width: 12,
                                                height: 12,
                                                borderRadius: '50%',
                                                bgcolor: passwordValidation.length ? '#10b981' : '#d1d5db'
                                            }} />
                                            <Typography variant="body2" sx={{
                                                color: passwordValidation.length ? '#10b981' : '#6b7280',
                                                fontSize: '0.75rem'
                                            }}>
                                                At least 8 characters long
                                            </Typography>
                                        </Box>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Box sx={{
                                                width: 12,
                                                height: 12,
                                                borderRadius: '50%',
                                                bgcolor: passwordValidation.uppercase ? '#10b981' : '#d1d5db'
                                            }} />
                                            <Typography variant="body2" sx={{
                                                color: passwordValidation.uppercase ? '#10b981' : '#6b7280',
                                                fontSize: '0.75rem'
                                            }}>
                                                At least one uppercase letter (A-Z)
                                            </Typography>
                                        </Box>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Box sx={{
                                                width: 12,
                                                height: 12,
                                                borderRadius: '50%',
                                                bgcolor: passwordValidation.lowercase ? '#10b981' : '#d1d5db'
                                            }} />
                                            <Typography variant="body2" sx={{
                                                color: passwordValidation.lowercase ? '#10b981' : '#6b7280',
                                                fontSize: '0.75rem'
                                            }}>
                                                At least one lowercase letter (a-z)
                                            </Typography>
                                        </Box>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Box sx={{
                                                width: 12,
                                                height: 12,
                                                borderRadius: '50%',
                                                bgcolor: passwordValidation.number ? '#10b981' : '#d1d5db'
                                            }} />
                                            <Typography variant="body2" sx={{
                                                color: passwordValidation.number ? '#10b981' : '#6b7280',
                                                fontSize: '0.75rem'
                                            }}>
                                                At least one number (0-9)
                                            </Typography>
                                        </Box>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Box sx={{
                                                width: 12,
                                                height: 12,
                                                borderRadius: '50%',
                                                bgcolor: passwordValidation.special ? '#10b981' : '#d1d5db'
                                            }} />
                                            <Typography variant="body2" sx={{
                                                color: passwordValidation.special ? '#10b981' : '#6b7280',
                                                fontSize: '0.75rem'
                                            }}>
                                                At least one special character (!@#$%^&*()_+-=[]{ }|;:,.)
                                            </Typography>
                                        </Box>
                                    </Box>
                                </Box>
                            )}
                            <TextField
                                margin="normal"
                                required
                                fullWidth
                                name="confirmPassword"
                                label="Confirm Password"
                                type={showPassword ? 'text' : 'password'}
                                id="confirmPassword"
                                value={registerForm.confirmPassword}
                                onChange={handleRegisterChange}
                                error={isPasswordMismatch}
                                helperText={isPasswordMismatch ? 'Passwords do not match' : ''}
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <Lock />
                                        </InputAdornment>
                                    ),
                                }}
                            />



                            {/* Verification code input */}
                            <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                                <TextField
                                    margin="normal"
                                    required
                                    fullWidth
                                    name="code"
                                    label="Verification Code"
                                    id="code"
                                    value={registerForm.code}
                                    onChange={handleRegisterChange}
                                    placeholder="Enter verification code"
                                />
                                <Button
                                    variant="outlined"
                                    onClick={handleSendVerificationCode}
                                    disabled={loading || codeCountdown > 0 || !registerForm.email || isPasswordMismatch}
                                    sx={{ mt: 2, minWidth: 120 }}
                                >
                                    {loading ? (
                                        <CircularProgress size={20} />
                                    ) : codeCountdown > 0 ? (
                                        `${codeCountdown}s`
                                    ) : (
                                        'Send Code'
                                    )}
                                </Button>
                            </Box>

                            <Button
                                type="submit"
                                fullWidth
                                variant="contained"
                                sx={{ mt: 3, mb: 2, py: 1.5 }}
                                disabled={loading}
                            >
                                {loading ? <CircularProgress size={24} /> : 'Register'}
                            </Button>
                        </Box>
                    )}
                </Paper>
            </Box>
        </Container>
    );
}

export default AuthPage; 