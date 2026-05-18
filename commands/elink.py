"""易链 (elink) API 命令封装

易链功能:
  - 登录认证 (AES-192-ECB + SSO JWT)
  - 项目查询
  - Gerrit 服务器查询
  - 忽略 Review -2 申请提交
"""

import json
import requests
from pathlib import Path

from core.config import get_elink_config, get_secrets_dir
from core import output as out


class ElinkClient:
    """易链 API 客户端"""

    def __init__(self, host, protocol="https", token=None, cookie=None):
        self.base_url = f"{protocol}://{host}"
        self.session = requests.Session()
        if cookie:
            self.session.headers.update({"Cookie": cookie})
        elif token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.session.headers.update({"Content-Type": "application/json"})

    def _post(self, path, data=None):
        resp = self.session.post(f"{self.base_url}/api/{path.lstrip('/')}", json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _get(self, path, params=None):
        resp = self.session.get(f"{self.base_url}/api/{path.lstrip('/')}", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def check_token(self):
        """验证 Token 有效性"""
        try:
            result = self._get("basic/user/info")
            if result.get("code") == 0:
                return {"status": "ok", "user": result.get("data", {}).get("username", "")}
            return {"status": "expired", "code": result.get("code")}
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                return {"status": "expired"}
            raise

    def project_list(self, project_name=None):
        """查询项目列表"""
        data = {}
        if project_name:
            data["projectName"] = project_name
        result = self._post("ts-platform/project/list", data)
        if result.get("code") == 0:
            return result.get("data", [])
        return []

    def query_gerrit_list(self, project_id):
        """查询项目关联的 Gerrit 服务器"""
        result = self._post("ts-basedata/masterGerrit/queryGerritList",
                            {"projectId": str(project_id)})
        if result.get("code") == 0:
            return result.get("data", [])
        return []

    def submit_ignore_check(self, project_id, project_name, commit_id,
                            gerrit_url, account_list, remark, module=2):
        """提交忽略 Review -2 申请

        Args:
            project_id: 易链项目 ID
            project_name: 项目名称
            commit_id: Gerrit change number
            gerrit_url: Gerrit 服务器地址
            account_list: 被忽略的检查账号列表 (如 ["checklog", "cppcheck"])
            remark: 忽略理由 (HTML 格式)
            module: 事业部 ID (2=IoT智能硬件, 1=智能汽车)

        Returns:
            dict: 提交结果
        """
        data = {
            "projectId": str(project_id),
            "projectName": project_name,
            "commitId": str(commit_id),
            "gerrit": gerrit_url,
            "accountList": account_list,
            "remark": f"<p>{remark}</p>" if not remark.startswith("<") else remark,
            "module": module,
        }
        result = self._post("ts-basedata/masterIgnoreCheck/submit", data)
        return result


def _load_token():
    """从缓存加载易链 Token"""
    cfg = get_elink_config()
    secrets_path = Path(cfg["secrets_path"]).expanduser()
    if not secrets_path.is_file():
        return None, None
    try:
        with open(secrets_path, "r", encoding="utf-8") as f:
            secrets = json.load(f)
        return secrets.get("token"), secrets.get("cookie")
    except (json.JSONDecodeError, OSError):
        return None, None


def _auto_refresh_token(project=None):
    """自动刷新过期的 elink Token

    当 Token 过期时，使用密码方式自动重新登录。
    需要 services.json 中配置 elink.auth.username/password/aes_key。
    """
    from core.auth import _elink_password_login
    cfg = get_elink_config(project)

    username = cfg.get("username", "")
    password = cfg.get("password", "")
    aes_key = cfg.get("aes_key", "")

    if not all([username, password, aes_key]):
        return False

    result = _elink_password_login(cfg, username, password, aes_key)
    return result.get("status") == "ok"


def create_client(project=None):
    """从配置创建易链客户端（自动加载缓存 Token，过期自动刷新）"""
    cfg = get_elink_config(project)
    token, cookie = _load_token()

    if not token and not cookie:
        # 尝试自动刷新
        if _auto_refresh_token(project):
            token, cookie = _load_token()
        if not token and not cookie:
            raise ValueError("易链未登录。请运行: cicd-cli elink +login")

    client = ElinkClient(
        host=cfg["host"],
        protocol=cfg["protocol"],
        token=token,
        cookie=cookie,
    )

    # 检查 token 有效性，过期则自动刷新
    status = client.check_token()
    if status.get("status") != "ok":
        if _auto_refresh_token(project):
            token, cookie = _load_token()
            client = ElinkClient(
                host=cfg["host"],
                protocol=cfg["protocol"],
                token=token,
                cookie=cookie,
            )
        else:
            raise ValueError("易链 Token 已过期且无法自动刷新。请运行: cicd-cli elink +login")

    return client


# 已知项目 ID 映射（从配置文件加载，此处为示例）
KNOWN_PROJECTS = {}
