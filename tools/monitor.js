const { spawn } = require('child_process');
const path = require('path');

function spawnNode(scriptPath, name) {
  const node = process.execPath || 'node';
  const proc = spawn(node, [scriptPath], { stdio: 'inherit', shell: false });
  proc.on('close', code => console.log(`${name} exited with code ${code}`));
  proc.on('error', err => console.error(`${name} error:`, err));
  return proc;
}

console.log('Monitor: starting API and frontend...');
const apiScript = path.join(__dirname, 'run_server.js');
const frontendScript = path.join(__dirname, 'run_frontend.js');

const apiProc = spawnNode(apiScript, 'API');
const feProc = spawnNode(frontendScript, 'Frontend');

function shutdown(code) {
  console.log('Monitor: shutting down children');
  try { apiProc.kill('SIGINT'); } catch (e) {}
  try { feProc.kill('SIGINT'); } catch (e) {}
  process.exit(code || 0);
}

process.on('SIGINT', () => shutdown(0));
process.on('SIGTERM', () => shutdown(0));
process.on('uncaughtException', err => { console.error(err); shutdown(1); });
