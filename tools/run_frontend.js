const { spawn } = require('child_process');
const path = require('path');

function run() {
  const node = process.execPath || 'node';
  const server = path.join(__dirname, '..', 'frontend-demo', 'server.js');
  console.log('Starting frontend demo with', node, server);
  const proc = spawn(node, [server], { stdio: 'inherit', shell: false });

  proc.on('close', code => {
    console.log(`frontend server exited with code ${code}`);
    process.exit(code);
  });
}

run();
