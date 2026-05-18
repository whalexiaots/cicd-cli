"""Gerrit REST API 命令封装

提供 Gerrit 代码审查平台的操作接口:
  - 查询 changes
  - 提交 review
  - Cherry-pick
  - Dashboard
"""

import json
import requests
from urllib.parse import quote

from core.config import get_gerrit_config
from core import output as out


class GerritClient:
    """Gerrit REST API 客户端"""

    def __init__(self, host, username, http_password):
        self.host = host.rstrip("/")
        self.username = username
        self.http_password = http_password
        self.session = requests.Session()
        self.session.auth = (username, http_password)
        self.session.headers.update({"Content-Type": "application/json"})

    def _url(self, path):
        return f"{self.host}/a/{path.lstrip('/')}"

    def _get(self, path, params=None):
        resp = self.session.get(self._url(path), params=params, timeout=30)
        resp.raise_for_status()
        # Gerrit JSON 带有 )]}' 前缀
        text = resp.text
        if text.startswith(")]}'"):
            text = text[4:].strip()
        return json.loads(text) if text else {}

    def _post(self, path, data=None):
        resp = self.session.post(self._url(path), json=data, timeout=30)
        resp.raise_for_status()
        text = resp.text
        if text.startswith(")]}'"):
            text = text[4:].strip()
        return json.loads(text) if text else {}

    def query_changes(self, query, limit=25):
        """查询 changes"""
        return self._get("changes/", params={"q": query, "n": limit,
                                             "o": "CURRENT_REVISION", "o": "LABELS"})

    def get_change(self, change_id):
        """获取 change 详情"""
        return self._get(f"changes/{quote(str(change_id), safe='')}/detail")

    def get_change_files(self, change_id, revision="current"):
        """获取 change 修改的文件列表"""
        return self._get(f"changes/{change_id}/revisions/{revision}/files")

    def get_change_comments(self, change_id):
        """获取 change 的评论"""
        return self._get(f"changes/{change_id}/comments")

    def get_change_messages(self, change_id):
        """获取 change 的 messages"""
        return self._get(f"changes/{change_id}/messages")

    def get_reviewers(self, change_id):
        """获取 reviewers"""
        return self._get(f"changes/{change_id}/reviewers")

    def set_review(self, change_id, revision="current", labels=None, message=None):
        """提交 review"""
        data = {}
        if labels:
            data["labels"] = labels
        if message:
            data["message"] = message
        return self._post(f"changes/{change_id}/revisions/{revision}/review", data)

    def submit_change(self, change_id):
        """submit change"""
        return self._post(f"changes/{change_id}/submit")

    def abandon_change(self, change_id, message=None):
        """abandon change"""
        data = {"message": message} if message else {}
        return self._post(f"changes/{change_id}/abandon", data)

    def rebase_change(self, change_id):
        """rebase change"""
        return self._post(f"changes/{change_id}/rebase", {})

    def cherry_pick(self, change_id, revision, destination_branch, message=None):
        """cherry-pick change 到另一个分支"""
        data = {"destination": destination_branch}
        if message:
            data["message"] = message
        return self._post(f"changes/{change_id}/revisions/{revision}/cherrypick", data)

    def dashboard(self, query="is:open+owner:self"):
        """获取我的 dashboard"""
        return self.query_changes(query)


def create_client(project=None):
    """从配置创建 Gerrit 客户端"""
    cfg = get_gerrit_config(project)
    if not cfg["host"]:
        raise ValueError("Gerrit host 未配置。请检查 services.json 中的 gerrit 配置。")
    return GerritClient(
        host=cfg["host"],
        username=cfg["username"],
        http_password=cfg["http_password"],
    )
