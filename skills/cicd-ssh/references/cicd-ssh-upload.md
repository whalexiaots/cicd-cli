# SSH 文件上传

## 用法

```bash
cicd-cli ssh +upload <local_path> <remote_path>
```

## 参数

| 参数 | 说明 |
|------|------|
| local_path | 本地文件路径 |
| remote_path | 远程目标路径 |

## 示例

```bash
cicd-cli ssh +upload ./patch.diff /tmp/patch.diff
cicd-cli ssh +upload ./build.zip /home/user/builds/
```
