---
name: cicd-patch
description: >-
  应用代码补丁：Gerrit cherry-pick、git format-patch、diff patch、
  AI 生成的补丁打到远程编译机。
  Use when user mentions: 应用补丁、打补丁、转移代码、合并补丁、
  cherry-pick、apply patch、git am、patch -p1。
---

> 依赖: `cicd-ssh` + `cicd-gerrit` · 配置: `projects.<name>.ssh` + `projects.<name>.gerrit` + `projects.<name>.repo`

# Patch Apply Skill

## Shortcuts

| 命令 | 说明 | 示例 |
|------|------|------|
| `+cherry-pick` | Gerrit cherry-pick | `cicd-cli patch +cherry-pick refs/changes/45/543945/1 --repo frameworks/base` |
| `+apply` | 应用 diff patch | `cicd-cli patch +apply --file fix.patch --repo kernel/msm-5.15` |
| `+am` | 应用 format-patch | `cicd-cli patch +am 0001-fix.patch --repo frameworks/base` |
| `+upload` | 上传并应用 | `cicd-cli patch +upload local.patch --repo vendor/qcom --method am` |
| `+abort` | 中止操作 | `cicd-cli patch +abort --type cherry-pick --repo frameworks/base` |

## 补丁方法决策

| 场景 | 推荐方法 | 命令 |
|------|----------|------|
| 已在 Gerrit 上的变更 | `+cherry-pick` | 通过 refspec 拉取并 cherry-pick |
| 本机已有 format-patch | `+am` | git am 保留 commit 信息 |
| AI 生成/手写的 diff | `+apply` | git apply (不创建 commit) |
| 本地文件需传远程 | `+upload` | 先上传再应用 |
| 冲突需中止 | `+abort` | cherry-pick --abort 或 am --abort |

## Gerrit Cherry-Pick 流程

```bash
# refspec 格式: refs/changes/<last2digits>/<changeID>/<patchset>
# 例: Change 543945 Patchset 1 → refs/changes/45/543945/1

cicd-cli patch +cherry-pick refs/changes/45/543945/1 \
  --repo frameworks/base \
  --gerrit-project general/platform/frameworks/base
```

若 `--gerrit-project` 省略，默认使用 `--repo` 的值。

## 定位目标仓库

在大型 Android 工程中定位补丁应用的 Git 仓库：

1. **按文件路径推断**: 修改的文件在 `frameworks/base/` 下 → repo = `frameworks/base`
2. **repo list**: `repo list | grep <keyword>`
3. **git log**: `cd <suspected_repo> && git log --oneline -5`

## 冲突处理

cherry-pick/am 冲突时：
1. `cicd-cli patch +abort` 中止
2. 手动解决冲突后重新提交
3. 或使用 `--check` 预检查: `cicd-cli patch +apply --check --file fix.patch`

## CRITICAL

- **cherry-pick 前确认分支正确**：在错误分支 cherry-pick 会污染编译
- **format-patch 保留 commit 信息**：优先用 +am 而非 +apply
- **大型 patch 先 --check**：避免部分应用导致代码不一致
- **冲突立即 +abort**：不要在冲突状态下编译
