# Frontend (Next.js)

This is a minimal Next.js page that POSTs to the Node API. For local development you can run Next.js on port 3000 and Node API on 3001. To avoid CORS, we've provided a simple server proxy suggestion below.

Run (Windows cmd):
```cmd
cd frontend-next
npm install
npm run dev
```

Proxy suggestion: add a lightweight reverse proxy or add a small Express endpoint that forwards `/api/proxy/*` to the Node API at `http://localhost:3001`.
