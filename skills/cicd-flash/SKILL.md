---
name: cicd-flash
description: >-
  刷机与设备验证：从远程服务器拉取构建产物，通过 fastboot / adb push 刷入设备。
  Use when user mentions: 刷机、刷固件、烧录、下载固件、fastboot、
  adb push、刷机验证、烧写镜像、flash firmware、push images。
---

> 依赖: `cicd-ssh` (产物下载) · 配置: `projects.<name>.ssh` + `projects.<name>.device`

# Flash & Verify Skill

## Shortcuts

| 命令 | 说明 | 示例 |
|------|------|------|
| `+download` | 下载构建产物 | `cicd-cli flash +download --images boot.img system.img` |
| `+fastboot` | fastboot 刷机 | `cicd-cli flash +fastboot --partition boot --image ./artifacts/boot.img` |
| `+push` | adb push 文件 | `cicd-cli flash +push ./lib.so /vendor/lib64/` |
| `+reboot` | 重启设备 | `cicd-cli flash +reboot --mode bootloader` |
| `+check` | 检查设备连接 | `cicd-cli flash +check` |
| `+verify` | 验证刷机结果 | `cicd-cli flash +verify --version 20260427` |

## 工作流

### 标准刷机流程

```raw
1. cicd-cli flash +check                    # 确认设备连接
2. cicd-cli flash +download --images boot.img system.img vendor.img
3. cicd-cli flash +reboot --mode bootloader  # 进入 fastboot
4. cicd-cli flash +fastboot --all            # 全量刷机
5. cicd-cli flash +verify                    # 验证版本
```

### 快速验证 (仅刷 boot)

```raw
1. cicd-cli flash +download --images boot.img
2. cicd-cli flash +reboot --mode bootloader
3. cicd-cli flash +fastboot --partition boot --image ./artifacts/boot.img
4. adb reboot
5. cicd-cli flash +verify
```

### adb push 单文件

```raw
1. cicd-cli flash +download --file vendor/lib64/libcamera.so
2. adb root && adb remount
3. cicd-cli flash +push ./artifacts/libcamera.so /vendor/lib64/
4. cicd-cli flash +reboot
```

## 刷机方法决策

| 场景 | 方法 | 说明 |
|------|------|------|
| 全量刷机 (首次/recovery) | `+fastboot --all` | turbox_flash.sh 全量 |
| 验证 boot/kernel 修改 | `+fastboot --partition boot` | 仅刷 boot 分区 |
| 验证 vendor 库修改 | `+push` | adb push 到设备 |
| 验证 system 修改 | `+fastboot --partition system` | 刷 system 分区 |
| nonHLOS 验证 | `+fastboot --partition modem` | 或使用脚本 |

## 产物路径

| 类型 | 远程路径 (相对 REPO_ROOT) |
|------|--------------------------|
| boot.img | `out/target/product/<product>/boot.img` |
| system.img | `out/target/product/<product>/system.img` |
| vendor.img | `out/target/product/<product>/vendor.img` |
| super.img | `out/target/product/<product>/super.img` |
| NON-HLOS.bin | `common/build/bin/NON-HLOS.bin` |
| 打包产物 | `turbox/output/` |

## 设备状态检查

`+check` 返回 adb 和 fastboot 设备列表：
- 有 adb 设备 → 可以 adb push 或 adb reboot bootloader
- 有 fastboot 设备 → 可以 fastboot flash
- 都没有 → 检查 USB 连接、驱动、设备是否开机

## CRITICAL

- **刷机前确认设备序列号**：多设备环境避免刷错
- **全量刷机前备份重要数据**
- **fastboot 刷机需要先 `adb reboot bootloader`**
- **adb push 前先 `adb root && adb remount`**
- **验证版本号确认刷机成功**

## 配置示例

```json
{
  "projects": {
    "<project_name>": {
      "device": {
        "serial": "<DEVICE_SERIAL>",
        "flash_method": "fastboot",
        "flash_script": "turbox_flash.sh"
      }
    }
  }
}
```
