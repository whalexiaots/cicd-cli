"""Jira REST API 命令封装

提供 Jira Bug 生命周期管理:
  - 创建/查询 Bug
  - 状态流转
  - 评论管理
  - 搜索 (JQL)
"""

import json
import requests

from core.config import get_jira_config
from core import output as out


class JiraClient:
    """Jira REST API 客户端"""

    def __init__(self, host, username, api_token):
        self.host = host.rstrip("/")
        self.username = username
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}",
        })

    def _url(self, path):
        return f"{self.host}/rest/api/2/{path.lstrip('/')}"

    def _get(self, path, params=None):
        resp = self.session.get(self._url(path), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path, data=None):
        resp = self.session.post(self._url(path), json=data, timeout=30)
        resp.raise_for_status()
        return resp.json() if resp.text else {}

    def _put(self, path, data=None):
        resp = self.session.put(self._url(path), json=data, timeout=30)
        resp.raise_for_status()
        return resp.json() if resp.text else {}

    def search(self, jql, max_results=50, fields=None):
        """JQL 搜索"""
        params = {"jql": jql, "maxResults": max_results}
        if fields:
            params["fields"] = ",".join(fields)
        return self._get("search", params=params)

    def get_issue(self, key):
        """获取 issue 详情"""
        return self._get(f"issue/{key}")

    def create_issue(self, project, summary, description="", issue_type="Bug",
                     priority="Major", assignee=None, **kwargs):
        """创建 issue"""
        fields = {
            "project": {"key": project},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
            "priority": {"name": priority},
        }
        if assignee:
            fields["assignee"] = {"name": assignee}
        fields.update(kwargs)
        return self._post("issue", {"fields": fields})

    def transition_issue(self, key, transition_id, fields=None, comment=None):
        """状态流转"""
        data = {"transition": {"id": str(transition_id)}}
        if fields:
            data["fields"] = fields
        if comment:
            data["update"] = {
                "comment": [{"add": {"body": comment}}]
            }
        resp = self.session.post(
            f"{self.host}/rest/api/2/issue/{key}/transitions",
            json=data, timeout=30,
        )
        resp.raise_for_status()
        return {"status": "ok", "key": key, "transition_id": transition_id}

    def add_comment(self, key, body):
        """添加评论"""
        return self._post(f"issue/{key}/comment", {"body": body})

    def assign_issue(self, key, assignee):
        """分配经办人"""
        resp = self.session.put(
            f"{self.host}/rest/api/2/issue/{key}",
            json={"fields": {"assignee": {"name": assignee}}},
            timeout=30,
        )
        resp.raise_for_status()
        return {"status": "ok", "key": key, "assignee": assignee}

    def get_transitions(self, key):
        """获取可用的状态流转"""
        resp = self.session.get(
            f"{self.host}/rest/api/2/issue/{key}/transitions",
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def my_open_bugs(self, project=None):
        """查询我的未关闭 Bug"""
        jql = "assignee = currentUser() AND status not in (Closed, Resolved)"
        if project:
            jql += f" AND project = {project}"
        jql += " ORDER BY updated DESC"
        return self.search(jql, fields=["summary", "status", "priority", "updated"])


def create_client(project=None):
    """从配置创建 Jira 客户端"""
    cfg = get_jira_config(project)
    if not cfg["host"]:
        raise ValueError("Jira host 未配置。请检查 services.json。")
    return JiraClient(
        host=cfg["host"],
        username=cfg["username"],
        api_token=cfg["api_token"],
    )
