---
name: cicd-ssh
version: 0.1.0
description: >-
  SSH 远程连接与文件传输：远程命令执行、文件上传下载、批量操作。
  触发词：SSH、远程、连接、命令执行、上传、下载、scp、sftp、paramiko。
metadata:
  requires:
    bins: ["python3"]
    packages: ["paramiko"]
---

# SSH 远程操作

> **前置条件**: 先阅读 [../cicd-shared/SKILL.md](../cicd-shared/SKILL.md) 了解认证和配置。

## Shortcuts（推荐优先使用）

| Shortcut | 说明 | 详情 |
|----------|------|------|
| `+exec` | 远程执行命令 | [references/cicd-ssh-exec.md](references/cicd-ssh-exec.md) |
| `+upload` | 上传文件 | [references/cicd-ssh-upload.md](references/cicd-ssh-upload.md) |
| `+download` | 下载文件 | [references/cicd-ssh-download.md](references/cicd-ssh-download.md) |

## 快速示例

```bash
# 远程执行命令
cicd-cli ssh +exec "ls -la /home/user/workspace"
cicd-cli ssh +exec "cd /path && source build/envsetup.sh && make -j8" --timeout 600

# 上传文件
cicd-cli ssh +upload --local ./patch.diff --remote /home/user/patches/patch.diff

# 下载文件
cicd-cli ssh +download --remote /home/user/build/out.zip --local ./out.zip
```

## 配置

```json
{
  "ssh": {
    "host": "10.0.0.200",
    "port": 36002,
    "user": "username",
    "password": "password",
    "remote_dir": "/home/user/workspace"
  }
}
```

项目级覆盖: `projects.<name>.ssh`

## 关键约束

- **CRITICAL**: 远程路径必须在 `remote_dir` 范围内操作
- **CRITICAL**: 禁止执行 `rm -rf /` 等危险命令
- **WARNING**: 长时间命令建议设置 `--timeout`（默认 300 秒）
- 跨平台：使用 paramiko（纯 Python），无需系统 SSH 客户端
