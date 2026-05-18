#!/usr/bin/env node
/**
 * cicd-cli postinstall 脚本
 * npm install 后自动检查 Python 依赖
 */
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const ROOT = path.resolve(__dirname, '..');
const REQ = path.join(ROOT, 'requirements.txt');

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

// 安装 Python 依赖
if (fs.existsSync(REQ)) {
  console.log('📦 安装 Python 依赖...');
  try {
    execSync(`${python} -m pip install -r "${REQ}" -q`, {
      stdio: 'inherit',
      timeout: 120000,
    });
    console.log('✅ Python 依赖安装完成');
  } catch {
    console.log('⚠️  自动安装失败，请手动运行:');
    console.log(`   ${python} -m pip install -r ${REQ}`);
  }
}

// 创建配置目录
const configDir = path.join(
  process.env.HOME || process.env.USERPROFILE || '~',
  '.cicd-cli', 'config'
);
if (!fs.existsSync(configDir)) {
  try {
    fs.mkdirSync(configDir, { recursive: true });
    console.log(`📁 配置目录: ${configDir}`);
  } catch {}
}

console.log('\n🎉 cicd-cli 安装完成!');
console.log('   运行 cicd-cli config init 初始化配置');
console.log('   运行 cicd-cli --help 查看帮助\n');
