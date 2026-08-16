const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

class BackendManager {
  constructor(store) {
    this.store = store;
    this.process = null;
    this.pollInterval = null;
  }

  async start(env, isDev = false) {
    if (this.process) {
      await this.stop();
    }

    const port = env.PORT || '8765';

    const alreadyRunning = await this.checkHealth(port);
    if (alreadyRunning) {
      console.log(`[backend] already running on port ${port}, reusing`);
      return;
    }

    let binPath;
    if (isDev) {
      binPath = null;
    } else {
      const isWin = process.platform === 'win32';
      const ext = isWin ? '.exe' : '';
      binPath = path.join(process.resourcesPath, 'backend', `app${ext}`);
    }

    const childEnv = { ...process.env, ...env };

    if (binPath) {
      this.process = spawn(binPath, [], {
        env: childEnv,
        stdio: ['ignore', 'pipe', 'pipe'],
      });
    } else {
      const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
      this.process = spawn(pythonCmd, [
        '-m', 'uvicorn', 'backend.app:app',
        '--port', port,
        '--reload',
      ], {
        env: childEnv,
        stdio: ['ignore', 'pipe', 'pipe'],
        cwd: path.join(__dirname, '..'),
      });
    }

    this.process.stdout.on('data', (data) => {
      console.log(`[backend] ${data.toString().trim()}`);
    });

    this.process.stderr.on('data', (data) => {
      console.error(`[backend] ${data.toString().trim()}`);
    });

    this.process.on('exit', (code, signal) => {
      console.log(`[backend] exited with code ${code}, signal ${signal}`);
      this.process = null;
    });

    this.process.on('error', (err) => {
      console.error(`[backend] error: ${err.message}`);
      this.process = null;
    });

    await this.waitForHealth(port);
  }

  checkHealth(port) {
    return new Promise((resolve) => {
      const req = http.get(`http://localhost:${port}/health`, (res) => {
        resolve(res.statusCode === 200);
      });
      req.on('error', () => resolve(false));
      req.end();
    });
  }

  waitForHealth(port, maxRetries = 15) {
    return new Promise((resolve, reject) => {
      let retries = 0;
      const poll = () => {
        const req = http.get(`http://localhost:${port}/health`, (res) => {
          if (res.statusCode === 200) {
            resolve();
          } else if (retries < maxRetries) {
            retries++;
            setTimeout(poll, 500);
          } else {
            reject(new Error('Backend health check failed'));
          }
        });
        req.on('error', () => {
          if (retries < maxRetries) {
            retries++;
            setTimeout(poll, 500);
          } else {
            reject(new Error('Backend health check timed out'));
          }
        });
        req.end();
      };
      poll();
    });
  }

  async stop() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }

    if (this.process) {
      return new Promise((resolve) => {
        const timeout = setTimeout(() => {
          if (this.process) {
            this.process.kill('SIGKILL');
          }
          resolve();
        }, 5000);

        this.process.on('exit', () => {
          clearTimeout(timeout);
          this.process = null;
          resolve();
        });

        try {
          if (process.platform === 'win32') {
            spawn('taskkill', ['/pid', this.process.pid.toString(), '/f', '/t']);
          } else {
            this.process.kill('SIGTERM');
          }
        } catch {
          clearTimeout(timeout);
          this.process = null;
          resolve();
        }
      });
    }
  }
}

module.exports = BackendManager;
