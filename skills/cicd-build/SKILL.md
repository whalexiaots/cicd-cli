---
name: cicd-build
description: >-
  远程编译：通过 SSH 在代码服务器上执行 turbox_build.sh，覆盖 Android (HLOS)、
  nonHLOS 子系统（bl/rpm/aop/tz/adsp/cdsp/mpss/uefi/soccp）、kernel、
  签名与打包（fastboot/flat/meta/OTA）。
  Use when user mentions: 远程编译、编译代码、全量编译、增量编译、编译模块、
  清理编译、make、mka、构建镜像、编译 boot、编译 kernel、编译 hlos、
  编译 nonhlos、编译子系统、打包镜像、打 OTA 包、签名镜像、turbox_build。
---

> 依赖: `cicd-ssh` (远程命令执行) · 配置: `projects.<name>.ssh` + `projects.<name>.repo`

# Remote Build Skill

## Shortcuts

| 命令 | 说明 | 示例 |
|------|------|------|
| `+module <path>` | 增量编译单模块 | `cicd-cli build +module frameworks/base/services` |
| `+kernel` | 编译 kernel | `cicd-cli build +kernel --defconfig xxx_defconfig` |
| `+image <type>` | 编译指定 image | `cicd-cli build +image bootimg` |
| `+nonhlos` | 编译 nonHLOS | `cicd-cli build +nonhlos --sub adsp` |
| `+hlos` | 全量 HLOS 编译 | `cicd-cli build +hlos --clean` |
| `+all` | 完整编译 | `cicd-cli build +all --sign --pack fastboot` |
| `+custom` | 自定义参数 | `cicd-cli build +custom -- --mpss --adsp -l` |

## 决策表：何时用哪条命令

| 修改范围 | 推荐 Shortcut | turbox_build.sh 参数 | 预估耗时 |
|----------|---------------|---------------------|----------|
| 仅改 Android 单模块 (Java/C) | `+module <path>` | `-a --ap-m <module> -l` | 5–30 min |
| 仅改 boot/system/userdata image | `+image bootimg` | `-a --ap-i bootimg -l` | 10–30 min |
| 仅改 kernel defconfig | `+kernel` | `-a --ap-k <defconfig> -l` | 30–45 min |
| 仅改某 nonHLOS 子系统 | `+nonhlos --sub <name>` | `--<sub> -l` | 5–20 min |
| 改了 Android.mk / 编译规则 | `+hlos --clean` | `-c -a -l` | 40–90 min |
| 改了多个模块，不确定范围 | `+hlos` | `-a -l` | 40–90 min |
| 全量 nonHLOS | `+nonhlos` | `-b -l` | 30–60 min |
| 完整版本 (HLOS + nonHLOS + 打包) | `+all --pack fastboot` | `--all --zip_fastboot_build -l` | 60–120 min |
| 首次拉代码 / 不知道改了什么 | `+all --clean` | `--all -c -l` | 120–240 min |

## 关键开关

| 标志 | 说明 |
|------|------|
| `--clean` | Clean 编译（首次/规则变更后必加） |
| `--no-log` | 不保存日志（**不推荐**） |
| `--jobs N` | 并发数（OOM 时降为 4 或 2） |
| `--no-ccache` | 关 CCACHE（debug 编译问题时） |
| `--sign` | 编译后签名所有镜像 |
| `--pack <type>` | 编译后打包 (fastboot/flat/meta/ota/sdk) |

## 打包类型

| 类型 | 用途 |
|------|------|
| fastboot | fastboot 刷机包 |
| flat | flat 刷机包 |
| meta | 含全部 ELF 调试包 |
| ota | OTA 全量 + target 包 |
| sdk | SDK 包 |

## nonHLOS 子系统列表

`bl` · `rpm` · `aop` · `tz` · `adsp` · `cdsp` · `mpss` · `soccp` · `uefi`

## 产物位置

| 类型 | 路径 (相对 REPO_ROOT) |
|------|------|
| HLOS images | `out/target/product/<product>/{boot,system,vendor,super,userdata}.img` |
| nonHLOS bin | `common/build/bin/NON-HLOS.bin` |
| 编译日志 | `turbox/output/log/` |
| 打包产物 | `turbox/output/` |

## 异常处理

| 错误关键词 | 原因 | 处置 |
|-----------|------|------|
| `No such file` (envsetup) | cwd 不在 REPO_ROOT | 检查 services.json 中 repo.root 配置 |
| `ninja: error: missing` | 增量编译缓存错乱 | 加 `--clean` 重编 |
| `out of memory` / OOM | 并发太高 | 降低 --jobs 到 4 或 2 |
| `No space left on device` | 磁盘满 | 清理 out/ 目录 |
| `Permission denied (publickey)` | SSH key 缺失 | 检查 cicd-cli auth status |
| CCACHE 缓存疑似污染 | 代码未生效 | 加 `--no-ccache` 重编 |

## 超时配置

| 编译类型 | 默认超时 |
|----------|---------|
| 单模块 (+module) | 30 min |
| kernel / nonHLOS 单子系统 | 45 min |
| 全量 HLOS (+hlos) | 120 min |
| 全量 nonHLOS (+nonhlos) | 90 min |
| 完整 +all | 180 min |
| Clean 后全量 | 240 min |

## CRITICAL

- **每次必加日志**（默认已开启，除非 --no-log）
- **改了 Android.mk / 编译规则必加 --clean**
- **不要混用增量和全量产物刷机**
- **CCACHE 默认开启**：debug 编译问题第一步关 CCACHE

## 配置示例

```json
{
  "projects": {
    "dodo": {
      "ssh": {
        "host": "10.0.0.1",
        "port": 22,
        "user": "builder",
        "password": "xxx"
      },
      "repo": {
        "root": "/home/scm/code/DoDo/qssi",
        "product": "dodo",
        "variant": "userdebug"
      }
    }
  }
}
```
