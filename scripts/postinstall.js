#!/usr/bin/env node
/**
 * cicd-cli postinstall / install 脚本
 * 1. 安装程序文件到 ~/.cicd-cli/
 * 2. 安装 skills 到 ~/.cicd-cli/skills/
 * 3. 创建默认配置文件（占位符）
 * 4. 创建 venv 并安装 Python 依赖
 * 5. 添加 bin 到 PATH 提示
 */
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const ROOT = path.resolve(__dirname, '..');
const HOME = process.env.HOME || process.env.USERPROFILE || '~';
const CICD_HOME = path.join(HOME, '.cicd-cli');
const VENV_DIR = path.join(CICD_HOME, '.venv');
const BIN_DIR = path.join(CICD_HOME, 'bin');
const CONFIG_DIR = path.join(CICD_HOME, 'config');
const SKILLS_DIR = path.join(CICD_HOME, 'skills');
const SECRETS_DIR = path.join(CICD_HOME, 'secrets');

console.log('\n🔧 cicd-cli install');
console.log('='.repeat(40));

// === Step 1: 安装程序文件 ===
console.log('\n📂 安装程序文件...');
const DIRS_TO_COPY = ['core', 'commands', 'shortcuts', 'bin', 'scripts'];
for (const dir of DIRS_TO_COPY) {
  const src = path.join(ROOT, dir);
  const dst = path.join(CICD_HOME, dir);
  if (fs.existsSync(src)) {
    copyDirSync(src, dst);
  }
}
// 复制顶层文件
for (const f of ['requirements.txt', 'pyproject.toml', 'AGENTS.md']) {
  const src = path.join(ROOT, f);
  if (fs.existsSync(src)) {
    fs.copyFileSync(src, path.join(CICD_HOME, f));
  }
}
// 确保 bin 脚本可执行
for (const f of fs.readdirSync(BIN_DIR)) {
  const fp = path.join(BIN_DIR, f);
  try { fs.chmodSync(fp, 0o755); } catch {}
}
console.log(`✅ 程序安装到: ${CICD_HOME}`);

// === Step 2: 安装 skills ===
console.log('\n📚 安装 skills...');
const skillsSrc = path.join(ROOT, 'skills');
if (fs.existsSync(skillsSrc)) {
  copyDirSync(skillsSrc, SKILLS_DIR);
  const count = fs.readdirSync(SKILLS_DIR).filter(d =>
    fs.statSync(path.join(SKILLS_DIR, d)).isDirectory()
  ).length;
  console.log(`✅ ${count} 个 skills 安装到: ${SKILLS_DIR}`);
} else {
  console.log('⚠️  未找到 skills 目录');
}

// === Step 2.5: 创建 Claude Code skills 软链接 ===
const claudeSkillsDir = path.join(HOME, '.claude', 'skills');
if (fs.existsSync(path.join(HOME, '.claude'))) {
  fs.mkdirSync(claudeSkillsDir, { recursive: true });
  const skillDirs = fs.existsSync(SKILLS_DIR) ?
    fs.readdirSync(SKILLS_DIR).filter(d => fs.statSync(path.join(SKILLS_DIR, d)).isDirectory()) : [];
  let linked = 0;
  for (const skill of skillDirs) {
    const linkPath = path.join(claudeSkillsDir, skill);
    const target = path.join(SKILLS_DIR, skill);
    try {
      if (fs.existsSync(linkPath)) fs.rmSync(linkPath, { recursive: true });
      fs.symlinkSync(target, linkPath);
      linked++;
    } catch {}
  }
  if (linked > 0) {
    console.log(`🔗 ${linked} 个 skills 已链接到 Claude Code: ${claudeSkillsDir}`);
  }
}

// === Step 3: 创建默认配置 ===
console.log('\n⚙️  配置文件...');
fs.mkdirSync(CONFIG_DIR, { recursive: true });
fs.mkdirSync(SECRETS_DIR, { recursive: true });

const configFile = path.join(CONFIG_DIR, 'services.json');
if (!fs.existsSync(configFile)) {
  const exampleSrc = path.join(ROOT, 'config', 'services.json.example');
  if (fs.existsSync(exampleSrc)) {
    fs.copyFileSync(exampleSrc, configFile);
  } else {
    fs.writeFileSync(configFile, JSON.stringify(getDefaultConfig(), null, 2) + '\n');
  }
  console.log(`✅ 默认配置已创建: ${configFile}`);
  console.log('   请编辑该文件填入实际服务地址和凭证');
} else {
  console.log(`✅ 配置文件已存在: ${configFile}（跳过）`);
}

// === Step 4: 创建 venv 并安装 Python 依赖 ===
console.log('\n🐍 Python 环境...');
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
  console.log('⚠️  未找到 Python 3。请安装 Python 3.8+');
} else {
  const reqFile = path.join(CICD_HOME, 'requirements.txt');
  if (fs.existsSync(reqFile)) {
    if (!fs.existsSync(VENV_DIR)) {
      console.log(`📦 创建虚拟环境: ${VENV_DIR}`);
      try {
        execSync(`${python} -m venv "${VENV_DIR}"`, { stdio: 'inherit', timeout: 60000 });
      } catch {
        console.log('⚠️  venv 创建失败');
      }
    }
    if (fs.existsSync(path.join(VENV_DIR, 'bin', 'pip'))) {
      console.log('📦 安装 Python 依赖...');
      try {
        execSync(`"${path.join(VENV_DIR, 'bin', 'pip')}" install -r "${reqFile}" -q`, {
          stdio: 'inherit', timeout: 120000
        });
        console.log('✅ Python 依赖安装完成');
      } catch {
        console.log('⚠️  pip install 失败，请手动运行:');
        console.log(`   ${VENV_DIR}/bin/pip install -r ${reqFile}`);
      }
    }
  }
}

// === Step 5: 完成 ===
console.log('\n' + '='.repeat(40));
console.log('🎉 cicd-cli 安装完成!\n');
console.log(`   安装目录: ${CICD_HOME}`);
console.log(`   配置文件: ${configFile}`);
console.log(`   Skills:   ${SKILLS_DIR}`);
console.log(`   虚拟环境: ${VENV_DIR}`);
console.log(`\n💡 添加到 PATH:`);
console.log(`   echo 'export PATH="${BIN_DIR}:$PATH"' >> ~/.bashrc && source ~/.bashrc`);
console.log(`\n   然后运行: cicd-cli --help`);

// === 工具函数 ===
function copyDirSync(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const dstPath = path.join(dst, entry.name);
    if (entry.isDirectory()) {
      copyDirSync(srcPath, dstPath);
    } else {
      fs.copyFileSync(srcPath, dstPath);
    }
  }
}

function getDefaultConfig() {
  return {
    jenkins: { host: "<JENKINS_HOST>", port: 443, protocol: "https", auth: { method: "api_token", username: "<USERNAME>", api_token: "<API_TOKEN>" } },
    gerrit: { host: "<GERRIT_HOST>", port: 443, protocol: "https", auth: { method: "http_password", username: "<USERNAME>", http_password: "<HTTP_PASSWORD>" } },
    jira: { host: "<JIRA_HOST>", port: 443, protocol: "https", auth: { method: "api_token", username: "<USERNAME>", api_token: "<API_TOKEN>" } },
    ssh: { host: "<BUILD_SERVER>", port: 22, user: "<USERNAME>", password: "<PASSWORD>", remote_dir: "/home/<USER>/workspace" },
    ftp: { host: "<FTP_HOST>", port: 21, user: "anonymous", password: "", local_dir: "/tmp/downloads", max_retries: 3 },
    elink: { host: "elink.thundersoft.com", protocol: "https", auth: { method: "sso", username: "<USERNAME>", password: "<PASSWORD>(可选)", aes_key: "<AES_KEY>(可选)" }, secrets_path: "~/.cicd-cli/secrets/elink.json", module: 2 },
    projects: { "MyProject": { ssh: { host: "<BUILD_SERVER>", remote_dir: "/path/to/code" }, jenkins: { job_name: "<JOB_NAME>" }, elink: { project_id: "<PROJECT_ID>", project_name: "<PROJECT_NAME>" } } }
  };
}
