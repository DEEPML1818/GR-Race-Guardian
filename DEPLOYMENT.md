# 🚀 GR Race Guardian - Deployment Guide

Complete deployment guide for the GR Race Guardian platform.

---

## 📋 Prerequisites

- GitHub account
- Vercel account (for frontend)
- Railway or Render account (for backend)
- Domain name (optional)

---

## 🌐 Frontend Deployment (Vercel)

### Step 1: Prepare Frontend

1. **Push to GitHub**:
   ```bash
   cd frontend-next
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/gr-race-guardian-frontend.git
   git push -u origin main
   ```

2. **Create `.env.local`** (if needed):
   ```
   NEXT_PUBLIC_API_URL=http://your-backend-url.com
   NEXT_PUBLIC_WS_URL=ws://your-backend-url.com
   ```

### Step 2: Deploy to Vercel

1. **Go to [Vercel](https://vercel.com)** and sign in
2. **Click "New Project"**
3. **Import your GitHub repository**
4. **Configure Project**:
   - Framework Preset: **Next.js**
   - Root Directory: `frontend-next`
   - Build Command: `npm run build` (auto-detected)
   - Output Directory: `.next` (auto-detected)

5. **Environment Variables** (if needed):
   - `NEXT_PUBLIC_API_URL` = Your backend URL
   - `NEXT_PUBLIC_WS_URL` = Your WebSocket URL

6. **Click "Deploy"**

7. **Your frontend will be live at**: `https://your-project.vercel.app`

---

## 🔧 Backend Deployment (Railway)

### Option A: Railway (Recommended)

#### Step 1: Prepare Backend

1. **Create `railway.json`** in `backend-node`:
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "node server.js",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

2. **Create `Procfile`** in `backend-node`:
   ```
   web: node server.js
   ```

3. **Environment Variables**:
   - `PORT` = 3001 (or Railway assigned port)
   - `PYTHON_API_URL` = http://python-backend-url:8000
   - `JWT_SECRET` = Your secret key
   - `REDIS_HOST` = Your Redis URL (if using)
   - `REDIS_PORT` = 6379
   - `NODE_ENV` = production

#### Step 2: Deploy to Railway

1. **Go to [Railway](https://railway.app)** and sign in
2. **Click "New Project"**
3. **Deploy from GitHub repo**:
   - Connect your GitHub account
   - Select your repository
   - Set root directory to `backend-node`

4. **Configure Environment Variables**:
   - Add all environment variables from above

5. **Deploy**: Railway will automatically deploy

6. **Get your URL**: Railway provides a URL like `https://your-app.up.railway.app`

---

## 🐍 Python Backend Deployment (Railway)

### Step 1: Prepare Python Backend

1. **Create `Procfile`** in `backend-python`:
   ```
   web: uvicorn app:app --host 0.0.0.0 --port $PORT
   ```

2. **Create `runtime.txt`** (optional, specify Python version):
   ```
   python-3.11.0
   ```

3. **Update `app.py`** to use PORT from environment:
   ```python
   import os
   PORT = int(os.environ.get('PORT', 8000))
   ```

### Step 2: Deploy to Railway

1. **Create new service in Railway** for Python backend
2. **Deploy from GitHub**:
   - Root directory: `backend-python`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`

3. **Environment Variables**:
   - `PORT` = 8000
   - `ENVIRONMENT` = production

4. **Get Python backend URL**

---

## 🔄 Option B: Render (Alternative)

### Frontend on Render

1. **Go to [Render](https://render.com)**
2. **New Web Service**
3. **Connect GitHub repo**
4. **Settings**:
   - Name: `gr-race-guardian-frontend`
   - Root Directory: `frontend-next`
   - Build Command: `npm install && npm run build`
   - Start Command: `npm start`
   - Environment: `Node`

### Backend on Render

1. **New Web Service** for Node.js
2. **Settings**:
   - Root Directory: `backend-node`
   - Build Command: `npm install`
   - Start Command: `node server.js`
   - Environment Variables: Same as Railway

### Python Backend on Render

1. **New Web Service** for Python
2. **Settings**:
   - Root Directory: `backend-python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`

---

## 📦 Docker Deployment (Alternative)

### Docker Compose Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend-next
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend-node:3001
    depends_on:
      - backend-node

  backend-node:
    build: ./backend-node
    ports:
      - "3001:3001"
    environment:
      - PYTHON_API_URL=http://backend-python:8000
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - backend-python
      - redis

  backend-python:
    build: ./backend-python
    ports:
      - "8000:8000"
    environment:
      - PORT=8000

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Dockerfiles

**`frontend-next/Dockerfile`**:
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

**`backend-node/Dockerfile`**:
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3001
CMD ["node", "server.js"]
```

**`backend-python/Dockerfile`**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Deploy with Docker

```bash
docker-compose up -d
```

---

## 🔐 Environment Variables Reference

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_WS_URL=wss://your-backend.railway.app
```

### Node.js Backend
```env
PORT=3001
PYTHON_API_URL=http://backend-python:8000
JWT_SECRET=your-secret-key-here
REDIS_HOST=localhost
REDIS_PORT=6379
NODE_ENV=production
```

### Python Backend
```env
PORT=8000
ENVIRONMENT=production
```

---

## 🔗 Connect Services

After deployment, update URLs:

1. **Frontend** → Update `NEXT_PUBLIC_API_URL` to point to Node.js backend
2. **Node.js Backend** → Update `PYTHON_API_URL` to point to Python backend
3. **WebSocket** → Update CORS origins in `backend-node/server.js`

---

## ✅ Post-Deployment Checklist

- [ ] Frontend deployed and accessible
- [ ] Node.js backend deployed and healthy
- [ ] Python backend deployed and healthy
- [ ] API endpoints responding
- [ ] WebSocket connections working
- [ ] Environment variables configured
- [ ] CORS settings updated
- [ ] Database/storage working (JSON files or cloud storage)
- [ ] Redis connected (if using Bull Queue)

---

## 🐛 Troubleshooting

### Frontend can't connect to backend
- Check CORS settings in backend
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check if backend is accessible

### WebSocket not working
- Verify WebSocket URL (use `wss://` for HTTPS)
- Check Socket.IO CORS settings
- Ensure WebSocket ports are open

### Python backend not responding
- Check if Python service is running
- Verify PORT environment variable
- Check logs for errors

### Redis connection failed
- Verify Redis is running (if using Bull Queue)
- Check `REDIS_HOST` and `REDIS_PORT`
- System works without Redis (falls back to direct calls)

---

## 🎯 Quick Deploy Commands

```bash
# Vercel CLI
npm i -g vercel
cd frontend-next
vercel --prod

# Railway CLI
npm i -g @railway/cli
railway login
railway init
railway up
```

---

## 📚 Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [Render Documentation](https://render.com/docs)
- [Docker Documentation](https://docs.docker.com)

---

**Your GR Race Guardian platform is now ready for production! 🏎️✨**

