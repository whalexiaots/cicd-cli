# SSH 文件下载

## 用法

```bash
cicd-cli ssh +download <remote_path> <local_path>
```

## 参数

| 参数 | 说明 |
|------|------|
| remote_path | 远程文件路径 |
| local_path | 本地保存路径 |

## 示例

```bash
cicd-cli ssh +download /tmp/build.log ./build.log
cicd-cli ssh +download /out/target/product/boot.img ./artifacts/boot.img
```
