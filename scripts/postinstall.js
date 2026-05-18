#!/usr/bin/env node
/**
 * cicd-cli postinstall 脚本
 * npm install 后自动创建 venv 并安装 Python 依赖
 */
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const ROOT = path.resolve(__dirname, '..');
const REQ = path.join(ROOT, 'requirements.txt');
const HOME = process.env.HOME || process.env.USERPROFILE || '~';
const CICD_HOME = path.join(HOME, '.cicd-cli');
const VENV_DIR = path.join(CICD_HOME, '.venv');

console.log('\n🔧 cicd-cli postinstall');
console.log('='.repeat(40));

// 检查 Python
let python = null;
for (const cmd of ['python3', 'python']) {
  try {
    const ver = execSync(`${cmd} --version`, { encoding: 'utf8' }).trim();
    python = cmd;
    console.log(`✅ ${ver}`);
    break;
  } catch {}
}

if (!python) {
  console.log('⚠️  未找到 Python 3。请安装 Python 3.8+ 后运行:');
  console.log(`   pip install -r ${REQ}`);
  process.exit(0);
}

// 创建配置目录
const configDir = path.join(CICD_HOME, 'config');
if (!fs.existsSync(configDir)) {
  try {
    fs.mkdirSync(configDir, { recursive: true });
    console.log(`📁 配置目录: ${configDir}`);
  } catch {}
}

// 创建虚拟环境并安装依赖
if (fs.existsSync(REQ)) {
  const venvPip = path.join(VENV_DIR, 'bin', 'pip');
  
  if (!fs.existsSync(VENV_DIR)) {
    console.log(`📦 创建虚拟环境: ${VENV_DIR}`);
    try {
      execSync(`${python} -m venv "${VENV_DIR}"`, { stdio: 'inherit', timeout: 60000 });
    } catch {
      console.log('⚠️  虚拟环境创建失败，尝试直接 pip install...');
      try {
        execSync(`${python} -m pip install -r "${REQ}" -q --break-system-packages`, {
          stdio: 'inherit', timeout: 120000
        });
        console.log('✅ Python 依赖安装完成（系统级）');
      } catch {
        console.log('⚠️  自动安装失败，请手动运行:');
        console.log(`   ${python} -m pip install -r ${REQ}`);
      }
      finish();
      return;
    }
  }

  console.log('📦 安装 Python 依赖到 venv...');
  try {
    execSync(`"${venvPip}" install -r "${REQ}" -q`, {
      stdio: 'inherit', timeout: 120000
    });
    console.log('✅ Python 依赖安装完成');
  } catch {
    console.log('⚠️  venv pip 安装失败，请手动运行:');
    console.log(`   ${VENV_DIR}/bin/pip install -r ${REQ}`);
  }
}

finish();

function finish() {
  console.log(`\n🎉 cicd-cli 安装完成!`);
  console.log(`   虚拟环境: ${VENV_DIR}`);
  console.log(`   运行 cicd-cli config init 初始化配置`);
  console.log(`   运行 cicd-cli --help 查看帮助`);
}
