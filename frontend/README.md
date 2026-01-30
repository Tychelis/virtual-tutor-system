# Frontend - React-Based User Interface

## 🎯 Overview

The Frontend is a modern, responsive single-page application (SPA) built with React 19, serving as the primary user interface for the Virtual Tutor System. It provides an intuitive, visually appealing interface for real-time chat interactions, avatar-based video tutoring via WebRTC, document management, and user profile customization. The application features role-based routing (Student/Tutor) with distinct interfaces and capabilities for each user type.

**Architecture Role**: User Interface Layer → API Consumer → WebRTC Client

## ✨ Key Features

### Core Capabilities

- **Real-Time Chat Interface**
  - Server-Sent Events (SSE) for streaming LLM responses
  - Live text rendering with progressive display
  - Message history with session management
  - File attachment support (documents, images, audio)
  - Favorite/pin conversations
  - Multi-session concurrent chats

- **Avatar-Based Video Tutoring**
  - WebRTC integration for real-time avatar streaming
  - Dynamic avatar selection from backend catalog
  - Avatar preview before connection
  - Seamless avatar switching without page reload
  - Synchronized TTS with avatar lip-sync
  - Full-screen video mode

- **User Authentication & Authorization**
  - JWT-based authentication with auto-refresh
  - Role-based access control (Student/Tutor/Admin)
  - Email verification during registration
  - Password reset functionality
  - Token expiry warning modal with session extension
  - Persistent login state across tabs

- **Document Management**
  - Multi-format upload (PDF, TXT, DOCX, images, audio)
  - Drag-and-drop file upload
  - File list with search and filtering
  - Automatic RAG indexing notification
  - Upload progress tracking
  - File preview thumbnails

- **User Profile Management**
  - Customizable profile (avatar, bio, name)
  - Upload custom profile picture
  - View/edit personal information
  - Session statistics dashboard
  - Notification preferences

- **Tutor Admin Interface**
  - User management (view, edit, delete users)
  - Avatar creation and customization
  - TTS model selection and configuration
  - System statistics dashboard
  - User activity monitoring

- **Modern UI/UX Design**
  - Material-UI 7 components with custom theming
  - Glassmorphism effects with backdrop blur
  - Smooth animations and transitions
  - Responsive design (desktop, tablet, mobile)
  - Dark mode support (toggle-able)
  - Gradient color schemes
  - Accessibility features (ARIA labels, keyboard navigation)

## 🛠️ Technology Stack

### Core Framework
- **React 19.1.0** - Latest React with concurrent features
- **React Router DOM 7.6.3** - Client-side routing with nested routes
- **React Scripts 5.0.1** - Webpack-based build toolchain

### UI Libraries
- **Material-UI (MUI) 7.1.2** - Comprehensive component library
  - `@mui/material` - Core components
  - `@mui/icons-material` - Icon library (1000+ icons)
  - `@mui/lab` - Experimental components
- **Emotion** - CSS-in-JS styling library
  - `@emotion/react 11.14.0`
  - `@emotion/styled 11.14.0`

### HTTP & Communication
- **Axios 1.10.0** - Promise-based HTTP client
- **Fetch API** - Native browser API for SSE streaming
- **WebRTC** - Real-time peer-to-peer communication

### Testing
- **Jest** - JavaScript testing framework
- **React Testing Library 16.3.0** - Component testing utilities
- **Testing Library User Event 13.5.0** - User interaction simulation

### Development Tools
- **Web Vitals 2.1.4** - Performance monitoring
- **ESLint** - Code linting
- **Browserslist** - Target browser configuration

## 📁 Project Structure

```
frontend/
├── public/                     # Static assets
│   ├── index.html              # HTML template
│   ├── favicon.ico             # Site icon
│   └── manifest.json           # PWA manifest
│
├── src/
│   ├── index.js                # Application entry point
│   ├── App.js                  # Root component with routing
│   ├── App.css                 # Global styles
│   ├── config.js               # API configuration (auto-generated)
│   │
│   ├── components/             # React components
│   │   ├── AuthPage.js         # Login/Register page
│   │   ├── HomePage.js         # Main student interface
│   │   ├── UserAdminPage.js    # Tutor admin interface
│   │   ├── TokenExpiryModal.js # JWT expiry warning modal
│   │   ├── LoadingSpinner.js   # Loading indicator
│   │   ├── PreviewNavigator.js # Avatar preview component
│   │   │
│   │   ├── HomeHeader/         # Top navigation bar
│   │   ├── HomeSidebar/        # Left sidebar (chat list, subjects)
│   │   ├── HomeChatWindow/     # Main chat display area
│   │   ├── HomeChatList/       # Chat session list
│   │   ├── HomeFooter/         # Chat input area (text, file, voice)
│   │   ├── AdminSidebar/       # Admin navigation sidebar
│   │   └── UserTable/          # User management table
│   │
│   ├── services/               # API service layer
│   │   ├── authService.js      # Authentication APIs
│   │   ├── chatService.js      # Chat & messaging APIs
│   │   ├── userService.js      # User profile APIs
│   │   ├── uploadService.js    # File upload APIs
│   │   ├── adminService.js     # Admin management APIs
│   │   ├── notificationService.js  # Notification APIs
│   │   └── tokenService.js     # JWT token management
│   │
│   ├── utils/                  # Utility functions
│   │   └── request.js          # Axios wrapper with interceptors
│   │
│   └── setupTests.js           # Jest configuration
│
├── .env                        # Environment variables (production)
├── .env.development            # Development environment variables
├── package.json                # Dependencies & scripts
├── Dockerfile                  # Docker container configuration
└── README.md                   # This file
```

## 🏗️ Architecture & Technical Implementation

### Application Structure

```
┌──────────────────────────────────────────────────────────────┐
│                      Browser (User)                          │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  React App │  │  WebRTC    │  │  SSE Stream│           │
│  │  (UI Layer)│  │  (Video)   │  │  (Chat)    │           │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘           │
└────────┼───────────────┼───────────────┼───────────────────┘
         │               │               │
         ▼               ▼               ▼
┌────────────────────────────────────────────────────────────┐
│                    Backend Services                        │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ REST API     │  │ WebRTC Proxy │  │ SSE Endpoint │   │
│  │ (Port 8203)  │  │ (Dynamic)    │  │ (Streaming)  │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Application Root (`App.js`)

**Routing & Theme Management:**
```javascript
function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('token'));
  const [userRole, setUserRole] = useState(getUserRole());
  const [showTokenModal, setShowTokenModal] = useState(false);

  // JWT Token Monitoring
  useEffect(() => {
    if (isLoggedIn) {
      tokenService.startTokenMonitoring(
        handleTokenExpired,    // Callback when token expires
        handleTokenWarning     // Callback 5 min before expiry
      );
    }
    return () => tokenService.stopTokenMonitoring();
  }, [isLoggedIn]);

  return (
    <ThemeProvider theme={createModernTheme('light')}>
      <BrowserRouter>
        <Routes>
          {/* Public Route */}
          <Route path="/login" element={
            isLoggedIn ? <Navigate to="/" /> : <AuthPage onLoginSuccess={handleLoginSuccess} />
          } />
          
          {/* Protected Routes (Role-Based) */}
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
        
        {/* Global Modal */}
        <TokenExpiryModal 
          isOpen={showTokenModal} 
          onExtend={handleExtendSession}
          onLogout={handleLogout}
        />
      </BrowserRouter>
    </ThemeProvider>
  );
}
```

**Key Features:**
- Material-UI theme with custom palette, typography, and component overrides
- Glassmorphism effects (backdrop blur, transparency)
- Gradient color schemes (primary: blue, secondary: purple)
- Shadow system with 25 elevation levels
- Custom border radius (12px default)

#### 2. Authentication Page (`AuthPage.js`)

**Features:**
- Tab-based UI (Login / Register)
- Email verification with countdown timer
- Password validation with strength indicator
- Form validation with real-time feedback
- Remember me functionality
- Responsive design with centered card layout

**Login Flow:**
```
1. User enters email + password
2. Frontend calls authService.login()
3. Backend validates credentials → returns JWT
4. Frontend stores token in localStorage
5. Start token monitoring (auto-refresh)
6. Redirect to HomePage (or AdminPage for tutors)
```

**Register Flow:**
```
1. User enters email
2. Click "Send Verification Code"
3. Backend sends email → 6-digit code
4. User enters code + password
5. Frontend calls authService.register()
6. Backend creates user account
7. Auto-login after successful registration
```

#### 3. Home Page (`HomePage.js`)

**Layout Structure:**
```
┌────────────────────────────────────────────────────┐
│  HomeHeader (Top Nav)                              │
│  [Logo] [User Info] [Theme Toggle] [Logout]       │
├────────┬──────────────────────────┬────────────────┤
│        │                          │                │
│  Home  │   HomeChatWindow         │   Video Area   │
│ Sidebar│   (Messages Display)     │   (Avatar/     │
│        │                          │    WebRTC)     │
│ [Chat  │   [Message 1]            │   [Preview]    │
│  List] │   [Message 2]            │   or           │
│ [Subj.]│   [Message 3]            │   [Stream]     │
│        │                          │                │
│        ├──────────────────────────┤                │
│        │   HomeFooter             │                │
│        │   (Input Area)           │                │
│        │   [Text] [File] [Voice]  │                │
└────────┴──────────────────────────┴────────────────┘
```

**State Management:**
```javascript
const [sessions, setSessions] = useState([]);           // Chat sessions
const [selectedChatId, setSelectedChatId] = useState(null);
const [messages, setMessages] = useState([]);           // Current chat messages
const [selectedSubject, setSelectedSubject] = useState('All'); // Filter
const [isDarkMode, setIsDarkMode] = useState(false);    // Theme
const [sessionMessages, setSessionMessages] = useState({}); // Cache
```

**Key Functions:**
- `fetchMessages(session_id)` - Load messages for selected chat
- `refreshSessions()` - Sync chat list from backend
- `handleNewChat()` - Create new chat session
- `handleSendMessage()` - Send message via SSE streaming

#### 4. Chat Streaming (`chatService.js`)

**SSE Implementation:**
```javascript
async chatStream(formData, onChunk, onComplete, onError) {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'text/event-stream'
    },
    body: formData
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let fullText = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        
        if (data.chunk) {
          fullText += data.chunk;
          onChunk(data.chunk, fullText);  // Progressive rendering
        }
        
        if (data.status === 'complete') {
          onComplete(fullText);           // Final callback
        }
      }
    }
  }
}
```

**Progressive Text Rendering:**
- Frontend receives LLM response word-by-word
- Displays text incrementally (typewriter effect)
- Avatar speaks synchronized with text chunks
- No waiting for complete response

#### 5. WebRTC Video Integration

**Connection Flow:**
```
1. User selects avatar from sidebar
2. Frontend calls backend: POST /api/avatar/start
3. Backend allocates port, starts avatar instance
4. Backend returns WebRTC proxy URL: /api/webrtc/offer
5. Frontend creates RTCPeerConnection
6. Exchange SDP offers/answers via proxy
7. Establish P2P connection (via STUN/TURN if needed)
8. Video stream displays in avatar container
```

**Dynamic Port Routing:**
- Each user gets unique avatar port (e.g., 8615, 8616, ...)
- Backend maintains user → port mapping in Redis
- WebRTC proxy forwards requests to correct port
- Enables concurrent multi-user avatar streaming

#### 6. Token Management (`tokenService.js`)

**Auto-Refresh Mechanism:**
```javascript
class TokenService {
  startTokenMonitoring(onExpired, onWarning) {
    this.monitorInterval = setInterval(async () => {
      const remaining = await this.getTokenRemainingTime();
      
      if (remaining <= 0) {
        onExpired();  // Token expired → force logout
      } else if (remaining <= 300) {  // 5 minutes
        onWarning(remaining);  // Show warning modal
      }
    }, 60000);  // Check every minute
  }

  async getTokenRemainingTime() {
    const response = await axios.get('/api/token_status');
    return response.data.expires_in_seconds;
  }
}
```

**Token Expiry Modal:**
- Appears 5 minutes before token expires
- Shows countdown timer
- Options: "Extend Session" or "Logout"
- Auto-logout when timer reaches 0

#### 7. File Upload (`uploadService.js`)

**Multi-Format Support:**
```javascript
async uploadFile(file, sessionId, onProgress) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);

  return await http.post('/chat/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      onProgress(percent);
    }
  });
}
```

**Supported Formats:**
- **Documents**: PDF, TXT, DOCX (auto-indexed to RAG)
- **Images**: PNG, JPG, JPEG
- **Audio**: WAV, MP3, M4A

**Upload Flow:**
```
1. User drags file or clicks upload button
2. Frontend validates file type and size
3. Show upload progress bar (0-100%)
4. POST to /api/chat/upload with FormData
5. Backend saves file to uploads/{user_id}/
6. Backend sends document to RAG service
7. Frontend receives confirmation with file metadata
8. Display file in chat as message attachment
```

#### 8. Configuration Management (`config.js`)

**Auto-Generated Configuration:**
```javascript
// 🤖 Auto-generated from ports_config.py
const config = {
  get BACKEND_URL() {
    const host = window.location.hostname;
    return `http://${host}:8203`;
  },
  get LIPSYNC_MANAGER_URL() {
    const host = window.location.hostname;
    return `http://${host}:8606`;
  },
  get WEBRTC_URL() {
    const host = window.location.hostname;
    return `http://${host}:8615`;
  }
};
```

**Why Auto-Generated?**
- Single source of truth (`scripts/ports_config.py`)
- Prevents port mismatch between frontend/backend
- Regenerate with: `python scripts/generate_frontend_config.py`
- Dynamic hostname detection (works on any server)

## 🚀 Installation & Deployment

### Prerequisites

- **Node.js**: 18.x LTS or higher
- **npm**: 9.x or higher (or use `yarn`/`pnpm`)
- **Browser**: Chrome/Edge (latest) recommended for WebRTC
- **Backend Services**: Must be running (Backend, Avatar Manager, LLM, RAG)

### Step 1: Install Dependencies

```bash
cd frontend

# Install all dependencies
npm install

# Or use yarn
yarn install

# Or use pnpm (faster)
pnpm install
```

**Key Dependencies Installed:**
```json
{
  "react": "^19.1.0",
  "react-dom": "^19.1.0",
  "react-router-dom": "^7.6.3",
  "@mui/material": "^7.1.2",
  "@mui/icons-material": "^7.1.2",
  "axios": "^1.10.0"
}
```

### Step 2: Configure Environment Variables

**Development (`.env.development`):**
```bash
# Backend API URL (auto-detected if not set)
REACT_APP_API_BASE_URL=http://localhost:8203/api

# WebRTC base URL (auto-detected)
REACT_APP_WEBRTC_BASE_URL=http://localhost:8615

# Enable debug logs
REACT_APP_DEBUG=true
```

**Production (`.env`):**
```bash
# Production backend URL
REACT_APP_API_BASE_URL=https://api.example.com/api

# Disable debug logs
REACT_APP_DEBUG=false

# Analytics tracking ID (optional)
REACT_APP_GA_TRACKING_ID=UA-XXXXXXXXX-X
```

**Note:** Environment variables must be prefixed with `REACT_APP_` to be accessible in the app.

### Step 3: Start Development Server

```bash
# Start on default port 3000
npm start

# Or specify custom port
PORT=3001 npm start

# Or use .env file
echo "PORT=3001" >> .env
npm start
```

**Development Server Features:**
- Hot module replacement (HMR) - instant updates without refresh
- Source maps - debug original code in browser
- Error overlay - shows compilation errors in browser
- Auto-open browser on start
- HTTPS support (set `HTTPS=true`)

**Access Application:**
- Local: http://localhost:3000
- Network: http://<your-ip>:3000 (for testing on mobile)

### Step 4: Build for Production

```bash
# Create optimized production build
npm run build

# Output: build/ directory
# - Minified JavaScript bundles
# - Optimized CSS
# - Compressed images
# - Service worker (PWA)
```

**Build Optimizations:**
- Code splitting (lazy loading)
- Tree shaking (remove unused code)
- Minification (Terser)
- CSS extraction
- Asset optimization
- Source map generation (optional)

**Build Output:**
```
build/
├── static/
│   ├── css/
│   │   └── main.abc123.css         # Compiled CSS (hashed)
│   ├── js/
│   │   ├── main.def456.js          # Main bundle
│   │   ├── 2.ghi789.chunk.js       # Code-split chunk
│   │   └── runtime-main.jkl012.js  # Webpack runtime
│   └── media/
│       └── logo.mno345.png         # Optimized images
├── index.html                       # Entry HTML
├── manifest.json                    # PWA manifest
└── asset-manifest.json              # Asset mapping
```

### Step 5: Deploy to Production

#### Option A: Static Hosting (Nginx)

```bash
# Build production bundle
npm run build

# Copy to Nginx web root
sudo cp -r build/* /var/www/html/

# Nginx configuration
server {
    listen 80;
    server_name tutornet.example.com;
    root /var/www/html;
    index index.html;

    # React Router support (SPA)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy (avoid CORS)
    location /api {
        proxy_pass http://localhost:8203;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # WebRTC proxy
    location /webrtc {
        proxy_pass http://localhost:8615;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
    }

    # Enable gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

#### Option B: Docker Container

```dockerfile
# Dockerfile (already included)
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Build and run:**
```bash
# Build Docker image
docker build -t virtual-tutor-frontend:latest .

# Run container
docker run -d \
  --name frontend \
  -p 80:80 \
  virtual-tutor-frontend:latest
```

#### Option C: Serve with Node.js

```bash
# Install serve package
npm install -g serve

# Serve production build
serve -s build -l 3000

# Or with PM2 (process manager)
pm2 serve build 3000 --name "frontend" --spa
```

### Step 6: Verify Deployment

```bash
# Check health
curl http://localhost:3000

# Check API connectivity
curl http://localhost:3000/api/health

# Test WebRTC endpoint
curl http://localhost:3000/webrtc/offer
```

## 🧪 Testing

### Run Unit Tests

```bash
# Run all tests
npm test

# Run tests in watch mode (development)
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Run specific test file
npm test AuthPage.test.js
```

### Test Coverage Report

```bash
npm test -- --coverage --coverageReporters=html

# Open coverage report
open coverage/index.html
```

### End-to-End Testing (Manual)

**Test Checklist:**
1. ✅ User Registration
   - [ ] Send verification code
   - [ ] Register with valid code
   - [ ] Password validation
   
2. ✅ User Login
   - [ ] Valid credentials
   - [ ] Invalid credentials (error handling)
   - [ ] Remember me
   
3. ✅ Chat Functionality
   - [ ] Create new chat
   - [ ] Send text message (streaming)
   - [ ] Upload file (PDF, image)
   - [ ] View chat history
   - [ ] Favorite chat
   - [ ] Delete chat
   
4. ✅ Avatar Integration
   - [ ] Select avatar
   - [ ] Start avatar instance
   - [ ] WebRTC video streaming
   - [ ] Switch avatar
   - [ ] Disconnect avatar
   
5. ✅ Token Management
   - [ ] Token expiry warning (5 min)
   - [ ] Extend session
   - [ ] Auto-logout on expiry
   
6. ✅ Tutor Admin (if tutor role)
   - [ ] View user list
   - [ ] Create avatar
   - [ ] Manage users

## 🔧 Troubleshooting

### Issue 1: Backend Connection Refused

**Symptoms:**
```
Network Error: connect ECONNREFUSED 127.0.0.1:8203
```

**Solutions:**
```bash
# Check if backend is running
curl http://localhost:8203/api/health

# Start backend if not running
cd backend && python run.py

# Verify config.js has correct URL
cat src/config.js
```

---

### Issue 2: WebRTC Video Not Displaying

**Symptoms:**
- Avatar preview works, but video doesn't stream
- Console error: "Failed to establish WebRTC connection"

**Debug Steps:**
```javascript
// Check browser console for errors
console.log('WebRTC URL:', config.WEBRTC_URL);

// Verify avatar is started
fetch('http://localhost:8203/api/avatar/list', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json()).then(console.log);

// Test WebRTC endpoint directly
curl http://localhost:8615/offer
```

**Common Causes:**
- Avatar Manager not running → `cd avatar-manager && python api.py`
- User hasn't started avatar → Click "Connect Avatar" first
- Firewall blocking WebRTC ports → Check ports 8615-8619
- Browser doesn't support WebRTC → Use Chrome/Edge

---

### Issue 3: SSE Streaming Stuck

**Symptoms:**
- Message sends but no response
- Spinner keeps loading indefinitely

**Solutions:**
```bash
# Check LLM service
curl http://localhost:8100/health

# Check backend streaming endpoint
curl -N http://localhost:8203/api/chat/stream \
  -H "Authorization: Bearer <token>" \
  -F "message=test"

# Check browser console for EventSource errors
```

---

### Issue 4: Token Expired on Page Load

**Symptoms:**
- Already logged in, but gets logged out on refresh
- "Token not found in Redis" error

**Cause:** Token expired or Redis was restarted

**Solution:**
- User must re-login (tokens are not persistent across Redis restarts)
- Increase token TTL in backend `.env`:
  ```bash
  JWT_ACCESS_TOKEN_EXPIRES=36000  # 10 hours
  REDIS_TOKEN_TTL_SECONDS=36000
  ```

---

### Issue 5: File Upload Fails

**Symptoms:**
```
Upload failed: File type not allowed
```

**Solutions:**
```javascript
// Check allowed file types in backend
const ALLOWED_DOCS = ['pdf', 'txt', 'docx'];
const ALLOWED_IMAGE = ['png', 'jpg', 'jpeg'];
const ALLOWED_AUDIO = ['wav', 'mp3', 'm4a'];

// Ensure file extension matches
const ext = file.name.split('.').pop().toLowerCase();
```

---

### Issue 6: Dark Mode Not Working

**Cause:** Theme state not persisted

**Solution:**
```javascript
// HomePage.js already handles persistence
const [isDarkMode, setIsDarkMode] = useState(() => {
  const saved = localStorage.getItem('darkMode');
  return saved ? JSON.parse(saved) : false;
});

// Save on toggle
const handleThemeToggle = () => {
  const newMode = !isDarkMode;
  setIsDarkMode(newMode);
  localStorage.setItem('darkMode', JSON.stringify(newMode));
};
```

---

### Issue 7: CORS Errors

**Symptoms:**
```
Access-Control-Allow-Origin missing
```

**Solution:**
```bash
# Backend should have CORS enabled
# Check backend/app.py:
CORS(app)  # Enable CORS for all routes

# Or configure specific origins:
CORS(app, origins=["http://localhost:3000"])
```

---

### Issue 8: Build Fails

**Symptoms:**
```
npm run build
Error: Cannot find module 'react'
```

**Solutions:**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear npm cache
npm cache clean --force

# Try with different Node version
nvm install 18
nvm use 18
npm install
```

---

## 📊 Performance Optimization

### Bundle Size Analysis

```bash
# Install analyzer
npm install --save-dev webpack-bundle-analyzer

# Build with analyzer
npm run build -- --stats
npx webpack-bundle-analyzer build/bundle-stats.json
```

### Code Splitting

```javascript
// Lazy load heavy components
const UserAdminPage = React.lazy(() => import('./components/UserAdminPage'));

<Suspense fallback={<LoadingSpinner />}>
  <UserAdminPage />
</Suspense>
```

### Image Optimization

```bash
# Compress images before adding to project
npx imagemin src/assets/* --out-dir=src/assets/optimized
```

### Caching Strategy

```javascript
// Service Worker (PWA)
// public/service-worker.js
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});
```

---

## 📝 Best Practices

### State Management
- Use `useState` for local component state
- Use `useContext` for shared state (theme, auth)
- Avoid prop drilling with Context API
- Consider Redux for complex state (if needed)

### API Calls
- Always show loading indicators
- Handle errors gracefully with user-friendly messages
- Implement retry logic for failed requests
- Use debouncing for search inputs

### Security
- Store JWT in `localStorage` (or `httpOnly` cookies for better security)
- Validate all user inputs client-side
- Sanitize displayed user-generated content (prevent XSS)
- Use HTTPS in production
- Implement CSRF protection

### Accessibility
- Use semantic HTML elements
- Provide ARIA labels for interactive elements
- Ensure keyboard navigation works
- Test with screen readers
- Maintain sufficient color contrast (WCAG AA)

### Performance
- Lazy load routes and heavy components
- Optimize images (WebP, compression)
- Minimize bundle size (code splitting)
- Use React.memo for expensive components
- Implement virtual scrolling for long lists

---

## 🌐 Browser Support

| Browser | Minimum Version | WebRTC Support | SSE Support |
|---------|----------------|----------------|-------------|
| Chrome  | 90+            | ✅ Full        | ✅ Full     |
| Edge    | 90+            | ✅ Full        | ✅ Full     |
| Firefox | 88+            | ✅ Full        | ✅ Full     |
| Safari  | 14+            | ⚠️ Limited    | ✅ Full     |
| Opera   | 76+            | ✅ Full        | ✅ Full     |

**Recommendations:**
- **Best Experience**: Chrome/Edge (latest)
- **Good Support**: Firefox, Opera
- **Limited**: Safari (WebRTC reliability issues)
- **Not Supported**: IE11 (use modern browsers)

---

**Version**: 2.0.0  
**Last Updated**: 2025-11-18  
**Maintainer**: Virtual Tutor Development Team

