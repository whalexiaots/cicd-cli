"""统一认证管理

管理各服务的认证状态:
  - Gerrit: HTTP Password
  - Jira: API Token (PAT)
  - Jenkins: API Token
  - SSH: 密码/密钥
  - FTP: 用户名/密码
  - 易链: SSO JWT Token (AES-192-ECB 加密)
"""

import json
import sys
from pathlib import Path

from core.config import (
    get_elink_config,
    get_gerrit_config,
    get_jenkins_config,
    get_jira_config,
    get_secrets_dir,
    get_ssh_config,
    get_ftp_config,
    get_current_project,
)


def check_gerrit_auth(project=None):
    """检查 Gerrit 认证状态"""
    cfg = get_gerrit_config(project)
    ok = bool(cfg["host"] and cfg["username"] and cfg["http_password"])
    return {"service": "gerrit", "status": "ok" if ok else "missing", "host": cfg["host"], "user": cfg["username"]}


def check_jenkins_auth(project=None):
    """检查 Jenkins 认证状态"""
    cfg = get_jenkins_config(project)
    ok = bool(cfg["host"] and cfg["username"] and cfg["api_token"])
    return {"service": "jenkins", "status": "ok" if ok else "missing", "host": cfg["host"], "user": cfg["username"]}


def check_jira_auth(project=None):
    """检查 Jira 认证状态"""
    cfg = get_jira_config(project)
    ok = bool(cfg["host"] and cfg["username"] and cfg["api_token"])
    return {"service": "jira", "status": "ok" if ok else "missing", "host": cfg["host"], "user": cfg["username"]}


def check_ssh_auth(project=None):
    """检查 SSH 认证状态"""
    cfg = get_ssh_config(project)
    ok = bool(cfg["host"] and cfg["user"] and cfg["password"])
    return {"service": "ssh", "status": "ok" if ok else "missing", "host": cfg["host"], "user": cfg["user"]}


def check_ftp_auth(project=None):
    """检查 FTP 认证状态"""
    cfg = get_ftp_config(project)
    ok = bool(cfg["host"] and cfg["user"])
    return {"service": "ftp", "status": "ok" if ok else "missing", "host": cfg["host"], "user": cfg["user"]}


def check_elink_auth(project=None):
    """检查易链认证状态"""
    cfg = get_elink_config(project)
    secrets_path = Path(cfg["secrets_path"]).expanduser()

    result = {
        "service": "elink",
        "status": "missing",
        "host": cfg["host"],
        "user": cfg["username"],
    }

    if not secrets_path.is_file():
        result["detail"] = "token 文件不存在"
        return result

    try:
        with open(secrets_path, "r", encoding="utf-8") as f:
            secrets = json.load(f)
        token = secrets.get("token", "")
        if token:
            result["status"] = "ok"
            result["detail"] = f"token: {token[:8]}..."
        else:
            result["detail"] = "token 为空"
    except (json.JSONDecodeError, OSError):
        result["detail"] = "token 文件损坏"

    return result


def auth_status(project=None):
    """获取所有服务的认证状态"""
    if project is None:
        project = get_current_project()

    results = [
        check_gerrit_auth(project),
        check_jenkins_auth(project),
        check_jira_auth(project),
        check_ssh_auth(project),
        check_ftp_auth(project),
        check_elink_auth(project),
    ]

    return {
        "project": project or "(global)",
        "services": results,
    }


def elink_login(username=None, password=None, aes_key=None):
    """登录易链并缓存 Token

    优先使用浏览器 SSO 授权登录（推荐），回退到账号密码登录。

    SSO 授权流程:
      1. 启动本地 HTTP 回调服务器
      2. 打开浏览器到 elink SSO 登录页
      3. 用户在浏览器中完成认证
      4. SSO 重定向到 localhost 回调，携带 token
      5. cicd-cli 捕获 token 并保存

    Returns:
        dict: 登录结果
    """
    cfg = get_elink_config()

    # 优先尝试 SSO 浏览器授权
    try:
        return _elink_sso_login(cfg)
    except Exception as e:
        # SSO 失败时回退到账号密码方式
        username = username or cfg["username"]
        password = password or cfg["password"]
        aes_key = aes_key or cfg["aes_key"]

        if not all([username, password, aes_key]):
            return {"status": "error", "message": f"SSO 授权失败: {e}. 且缺少账号密码配置"}

        return _elink_password_login(cfg, username, password, aes_key)


def _elink_sso_login(cfg):
    """通过浏览器 SSO 授权登录易链

    流程:
      1. 打开浏览器到 SSO 登录页
      2. 用户完成认证（自动跳转到 elink Web）
      3. 从浏览器 Cookie 提取 token 并输入到 CLI
    """
    import webbrowser

    base_url = f"{cfg['protocol']}://{cfg['host']}"
    sso_url = f"{base_url}/sso/token/login"

    print(json.dumps({
        "status": "waiting",
        "message": f"正在打开浏览器进行 SSO 授权...\n如浏览器未自动打开，请手动访问:\n{sso_url}"
    }), file=sys.stderr)

    webbrowser.open(sso_url)

    # 提示用户提取 token
    print("\n" + "=" * 60, file=sys.stderr)
    print("SSO 授权登录步骤:", file=sys.stderr)
    print("1. 在浏览器中完成登录（自动跳转到易链页面）", file=sys.stderr)
    print("2. 登录成功后，按 F12 打开开发者工具", file=sys.stderr)
    print(f"3. 切换到 Application → Cookies → {cfg['host']}", file=sys.stderr)
    print("4. 复制 'token' 字段的值", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # 等待用户输入 token
    try:
        token = input("\n请粘贴 token（或输入 q 取消）: ").strip()
    except (EOFError, KeyboardInterrupt):
        raise RuntimeError("用户取消 SSO 授权")

    if not token or token.lower() == "q":
        raise RuntimeError("用户取消 SSO 授权")

    # 保存 token
    secrets_path = Path(cfg["secrets_path"]).expanduser()
    secrets_path.parent.mkdir(parents=True, exist_ok=True)

    secrets = {
        "token": token,
        "accessToken": "",
        "cookie": f"token={token}",
        "userId": "",
        "account": cfg.get("username", ""),
        "login_method": "sso",
    }
    with open(secrets_path, "w", encoding="utf-8") as f:
        json.dump(secrets, f, indent=2, ensure_ascii=False)

    return {"status": "ok", "message": f"SSO 授权成功: {token[:8]}..."}

    # 保存 token
    secrets_path = Path(cfg["secrets_path"]).expanduser()
    secrets_path.parent.mkdir(parents=True, exist_ok=True)

    secrets = {
        "token": token_result["token"],
        "accessToken": token_result.get("access_token", ""),
        "cookie": f"token={token_result['token']}; ts_uid={token_result.get('access_token', '')}",
        "userId": token_result.get("user_id", ""),
        "account": cfg.get("username", ""),
        "login_method": "sso",
    }
    with open(secrets_path, "w", encoding="utf-8") as f:
        json.dump(secrets, f, indent=2, ensure_ascii=False)

    return {"status": "ok", "message": f"SSO 授权成功: {secrets['token'][:8]}..."}


def _elink_password_login(cfg, username, password, aes_key):
    """使用账号密码登录易链（回退方式）"""
    try:
        import requests
        from Crypto.Cipher import AES
        import base64

        # AES-192-ECB ZeroPadding 加密
        key_bytes = aes_key.encode("utf-8")
        if len(key_bytes) != 24:
            key_bytes = base64.b64decode(aes_key)

        # ZeroPadding
        pwd_bytes = password.encode("utf-8")
        pad_len = 16 - (len(pwd_bytes) % 16)
        if pad_len != 16:
            pwd_bytes += b"\x00" * pad_len

        cipher = AES.new(key_bytes, AES.MODE_ECB)
        encrypted = base64.b64encode(cipher.encrypt(pwd_bytes)).decode("utf-8")
        full_password = f"TS::PASSWORD::SECURITY::{encrypted}"

        # 登录请求
        base_url = f"{cfg['protocol']}://{cfg['host']}"
        resp = requests.post(
            f"{base_url}/api/auth/token/login",
            data={"username": username, "password": full_password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            return {"status": "error", "message": data.get("msg", "登录失败")}

        # 保存 token
        token_data = data["data"]
        secrets_path = Path(cfg["secrets_path"]).expanduser()
        secrets_path.parent.mkdir(parents=True, exist_ok=True)

        secrets = {
            "token": token_data["jwtToken"],
            "accessToken": token_data["accessToken"],
            "cookie": f"token={token_data['jwtToken']}; ts_uid={token_data['accessToken']}",
            "userId": str(token_data.get("userId", "")),
            "account": username,
            "login_method": "password",
            "expires_in_seconds": token_data.get("expires_in", 719999),
        }
        with open(secrets_path, "w", encoding="utf-8") as f:
            json.dump(secrets, f, indent=2, ensure_ascii=False)

        return {"status": "ok", "message": f"密码登录成功: {secrets['token'][:8]}..."}

    except ImportError as e:
        return {"status": "error", "message": f"缺少依赖: {e}. 请安装 pycryptodome"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
