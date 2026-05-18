#!/usr/bin/env node
/**
 * cicd-cli Node.js wrapper
 * 将调用转发给 Python 入口
 * 特殊命令 "install" 执行本地安装初始化
 */
const { execFileSync, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const ROOT = path.resolve(__dirname, '..');
const ENTRY = path.join(ROOT, 'core', 'cli.py');

// 拦截 install 命令 — 执行本地初始化
if (process.argv[2] === 'install') {
  const postinstall = path.join(ROOT, 'scripts', 'postinstall.js');
  try {
    execFileSync(process.execPath, [postinstall], { stdio: 'inherit' });
  } catch (e) {
    process.exit(e.status || 1);
  }
  process.exit(0);
}

// 查找 Python（优先 ~/.cicd-cli/.venv）
const os = require('os');
const venvPython = path.join(os.homedir(), '.cicd-cli', '.venv', 'bin', 'python3');
let python = null;

if (require('fs').existsSync(venvPython)) {
  python = venvPython;
} else {
  for (const cmd of ['python3', 'python']) {
    try {
      execSync(`${cmd} --version`, { stdio: 'ignore' });
      python = cmd;
      break;
    } catch {}
  }
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
