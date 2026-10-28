import { spawn, spawnSync } from 'node:child_process';
import { readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('..', import.meta.url)).replace(/\/$/, '');
const env = { ...process.env, PATH: [dirname(process.execPath), '/opt/homebrew/bin', '/usr/local/bin', process.env.PATH].filter(Boolean).join(':') };
const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
const manifest = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'));
const versions = { ...manifest.dependencies, ...manifest.devDependencies };
const needsInstall = Object.entries(versions).some(([name, version]) => {
  try { return JSON.parse(readFileSync(join(root, 'node_modules', name, 'package.json'), 'utf8')).version !== version; }
  catch { return true; }
});

function run(args) {
  const result = spawnSync(npm, args, { cwd: root, env, stdio: 'inherit' });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status || 1);
}

if (needsInstall) run([existsSync(join(root, 'package-lock.json')) ? 'ci' : 'install']);
run(['run', 'build']);

function openBrowser(url) {
  if (process.argv.includes('--no-open')) return;
  const command = process.platform === 'darwin' ? '/usr/bin/open' : process.platform === 'win32' ? 'explorer.exe' : 'xdg-open';
  const child = spawn(command, [url], { detached: true, stdio: 'ignore', env });
  child.on('error', () => console.log(`Open ${url} in your browser.`));
  child.unref();
}

let running = '';
for (let port = 8765; port < 8775; port++) {
  const url = `http://127.0.0.1:${port}/`;
  try {
    const response = await fetch(`${url}__read_alone__`, { signal: AbortSignal.timeout(350) });
    const app = await response.json();
    if (app.application === 'read-alone' && app.runtime === 'react-vite' && app.root === root) { running = url; break; }
  } catch { /* Try the next port. */ }
}

if (running) {
  console.log(`Read Alone: ${running}`);
  openBrowser(running);
} else {
  const { preview } = await import('vite');
  const server = await preview({ root, configFile: join(root, 'vite.config.js'), preview: { host: '127.0.0.1', port: 8765, open: false } });
  const url = server.resolvedUrls.local[0];
  console.log(`Read Alone: ${url}`);
  console.log('Press Control-C to stop.');
  openBrowser(url);
}
