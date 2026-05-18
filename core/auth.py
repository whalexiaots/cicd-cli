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
    """通过浏览器 SSO 授权登录易链"""
    import threading
    import webbrowser
    import urllib.parse
    from http.server import HTTPServer, BaseHTTPRequestHandler

    base_url = f"{cfg['protocol']}://{cfg['host']}"
    callback_port = 18632  # 固定回调端口
    callback_url = f"http://localhost:{callback_port}/callback"
    token_result = {"token": None, "error": None}
    server_ref = [None]

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)

            # 从 URL 参数提取 token
            token = params.get("token", [None])[0]
            access_token = params.get("accessToken", params.get("access_token", [None]))[0]

            if token:
                token_result["token"] = token
                token_result["access_token"] = access_token or ""
                token_result["user_id"] = params.get("userId", [""])[0]

                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(
                    b"<html><body><h2>cicd-cli</h2>"
                    b"<p style='color:green'>&#10004; Login Success! You can close this page now.</p>"
                    b"<script>setTimeout(()=>window.close(),2000)</script>"
                    b"</body></html>"
                )
                # 在请求处理完成后关闭服务器
                threading.Thread(target=lambda: server_ref[0].shutdown(), daemon=True).start()
            else:
                # token 可能在 hash fragment，用 JS 提取后重定向
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(
                    b"<html><body><script>"
                    b"var h=window.location.hash.substring(1);"
                    b"if(h){window.location.href='/callback?'+h;}"
                    b"else{document.write('<p style=\"color:red\">Authorization failed. No token received.</p>');}"
                    b"</script></body></html>"
                )

        def log_message(self, format, *args):
            pass  # 静默日志

    # 启动回调服务器
    server = HTTPServer(("127.0.0.1", callback_port), CallbackHandler)
    server.timeout = 120
    server_ref[0] = server

    # 构建 SSO 登录 URL
    sso_url = f"{base_url}/sso/token/login?redirect_uri={urllib.parse.quote(callback_url)}"

    print(json.dumps({
        "status": "waiting",
        "message": f"正在打开浏览器进行 SSO 授权...\n如浏览器未自动打开，请手动访问:\n{sso_url}"
    }), file=sys.stderr)

    webbrowser.open(sso_url)

    # 使用 serve_forever() + shutdown() 确保回调后干净退出
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    # 等待最多 120 秒
    server_thread.join(timeout=120)
    if server_thread.is_alive():
        server.shutdown()
        server_thread.join(timeout=5)

    try:
        server.server_close()
    except Exception:
        pass

    if not token_result["token"]:
        raise RuntimeError("SSO 授权超时或失败")

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
