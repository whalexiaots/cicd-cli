#!/usr/bin/env node
/**
 * cicd-cli Node.js wrapper
 * 将调用转发给 Python 入口
 */
const { execFileSync } = require('child_process');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const ENTRY = path.join(ROOT, 'core', 'cli.py');

// 查找 Python
let python = null;
for (const cmd of ['python3', 'python']) {
  try {
    require('child_process').execSync(`${cmd} --version`, { stdio: 'ignore' });
    python = cmd;
    break;
  } catch {}
}

if (!python) {
  console.error('错误: 未找到 Python 3。请安装 Python 3.8+');
  process.exit(1);
}

try {
  execFileSync(python, [ENTRY, ...process.argv.slice(2)], {
    stdio: 'inherit',
    env: { ...process.env, PYTHONPATH: ROOT },
  });
} catch (e) {
  process.exit(e.status || 1);
}
