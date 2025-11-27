const { spawn } = require('child_process');
const path = require('path');

function run() {
  const py = process.env.PYTHON || 'python';
  const script = path.join(__dirname, '..', 'backend-python', 'run_pipeline.py');
  console.log('Running pipeline with', py, script);
  const proc = spawn(py, [script], { stdio: 'inherit', shell: false });

  proc.on('close', code => {
    console.log(`pipeline exited with code ${code}`);
    process.exit(code);
  });
}

run();
