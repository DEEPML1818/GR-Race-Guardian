const { spawn } = require('child_process');
const path = require('path');

function run() {
  const py = process.env.PYTHON || 'python';
  const backendDir = path.join(__dirname, '..', 'backend-python');
  const args = ['-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', '8000'];
  console.log('Starting FastAPI (uvicorn) using', py, args.join(' '));
  const proc = spawn(py, args, { cwd: backendDir, stdio: 'inherit', shell: false });

  proc.on('close', code => {
    console.log(`uvicorn exited with code ${code}`);
    process.exit(code);
  });
}

run();
