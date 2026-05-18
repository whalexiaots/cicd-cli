# SSH 远程命令执行

## 用法

```bash
cicd-cli ssh +exec "<command>"
cicd-cli ssh +exec "<command>" --timeout 300
```

## 参数

| 参数 | 说明 |
|------|------|
| command | 要执行的远程命令 |
| --timeout | 超时秒数 (默认 300) |

## 示例

```bash
cicd-cli ssh +exec "ls -la /tmp"
cicd-cli ssh +exec "df -h" --timeout 10
cicd-cli ssh +exec "cd /path && make -j8" --timeout 3600
```
