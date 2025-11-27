# Redis Setup Guide for Bull Queue

## Windows Setup

### Option 1: Docker (Recommended)

1. **Install Docker Desktop** from [docker.com](https://www.docker.com/products/docker-desktop)

2. **Run Redis container**:
   ```bash
   docker run -d -p 6379:6379 --name redis redis:7-alpine
   ```

3. **Verify Redis is running**:
   ```bash
   docker ps
   ```

### Option 2: WSL2 (Windows Subsystem for Linux)

1. **Install WSL2**:
   ```powershell
   wsl --install
   ```

2. **In WSL2, install Redis**:
   ```bash
   sudo apt update
   sudo apt install redis-server
   sudo service redis-server start
   ```

3. **Access from Windows**: Redis will be available on `localhost:6379`

### Option 3: Memurai (Windows Redis Alternative)

1. **Download Memurai** from [memurai.com](https://www.memurai.com/)

2. **Install and start** Memurai service

3. **Configure** to use port 6379

---

## macOS Setup

### Using Homebrew

```bash
brew install redis
brew services start redis
```

### Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

---

## Linux Setup

```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

---

## Verify Redis Connection

Test from Node.js:

```javascript
const Redis = require('ioredis');
const redis = new Redis();

redis.ping().then(() => {
  console.log('✅ Redis is connected!');
}).catch(err => {
  console.error('❌ Redis connection failed:', err);
});
```

---

## Using Redis with Bull Queue

Once Redis is running, the Bull Queue system will automatically use it:

```bash
cd backend-node
node server.js
```

Check queue status:
```bash
curl http://localhost:3001/api/jobs/health
```

---

## Note

**The system works WITHOUT Redis!** Bull Queue is optional. If Redis is not available, the system falls back to direct Python API calls.

