---
name: cicd-ftp
version: 0.1.0
description: >-
  FTP 文件下载与验证：文件下载、自动重试、MD5/魔数验证、目录列表。
  触发词：FTP、下载、download、文件传输、ftp://、构建产物。
metadata:
  requires:
    bins: ["python3"]
---

# FTP 文件下载

> **前置条件**: 先阅读 [../cicd-shared/SKILL.md](../cicd-shared/SKILL.md) 了解认证和配置。

## Shortcuts（推荐优先使用）

| Shortcut | 说明 |
|----------|------|
| `+download` | 下载文件（支持 FTP URL 或路径，自动重试）|
| `+list` | 列出远程目录内容 |
| `+test` | 测试 FTP 连接 |
| `+verify` | 验证本地文件完整性（MD5 + 魔数）|

## 快速示例

```bash
# 通过 URL 下载
cicd-cli ftp +download "ftp://user:pass@server/project/VerifyBuild/latest.zip"

# 通过配置下载
cicd-cli ftp +download /project/VerifyBuild/build_001.zip --local ./build.zip

# 指定 FTP 服务器
cicd-cli ftp +download /path/file.zip --server server1

# 列出目录
cicd-cli ftp +list /project/VerifyBuild/

# 测试连接
cicd-cli ftp +test
cicd-cli ftp +test --server server2

# 验证文件
cicd-cli ftp +verify ./build.zip --md5 abc123def456
```

## 配置

```json
{
  "ftp": {
    "host": "<FTP_SERVER_IP>",
    "port": 21,
    "user": "<USERNAME>",
    "password": "<PASSWORD>",
    "local_dir": "/tmp/downloads",
    "max_retries": 3
  },
  "ftp_servers": {
    "chengdu": { "host": "<FTP_SERVER_IP>", "user": "<USERNAME>", "password": "<PASSWORD>" },
    "server2": { "host": "<IP2>", "user": "<USER2>", "password": "<PASS2>" }
  }
}
```

## 关键约束

- **CRITICAL**: 下载失败自动重试（默认 3 次），最终失败返回错误
- **WARNING**: 大文件下载注意磁盘空间
- 使用标准库 ftplib，无第三方依赖
- 支持 ZIP/GZIP/RAR/7Z 魔数验证
