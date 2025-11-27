# Backend Node API

Simple Express API that receives a JSON body with `csv` path and calls the Python `serve_model.py` to get a prediction.

Example (Windows cmd):
```cmd
cd backend-node
npm install
node server.js
```

Then POST to `http://localhost:3001/api/predict` with JSON `{"csv": "<absolute-or-relative-path-to-csv>"}`
