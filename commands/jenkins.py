"""Jenkins API 命令封装

提供 Jenkins 编译触发、状态轮询、日志分析功能。
"""

import time
import requests
from urllib.parse import urljoin

from core.config import get_jenkins_config
from core import output as out


class JenkinsClient:
    """Jenkins REST API 客户端"""

    def __init__(self, host, username, api_token):
        self.host = host.rstrip("/")
        self.username = username
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (username, api_token)

    def _url(self, path):
        return f"{self.host}/{path.lstrip('/')}"

    def _get(self, path, params=None):
        resp = self.session.get(self._url(path), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json() if resp.text else {}

    def _post(self, path, data=None, params=None):
        resp = self.session.post(self._url(path), data=data, params=params, timeout=30)
        resp.raise_for_status()
        return resp

    def trigger_build(self, job_name, params=None):
        """触发编译

        Args:
            job_name: Jenkins job 名称
            params: 编译参数 dict

        Returns:
            dict: {queue_url, queue_id}
        """
        if params:
            path = f"job/{job_name}/buildWithParameters"
            resp = self._post(path, params=params)
        else:
            path = f"job/{job_name}/build"
            resp = self._post(path)

        queue_url = resp.headers.get("Location", "")
        queue_id = queue_url.rstrip("/").split("/")[-1] if queue_url else ""

        return {
            "status": "queued",
            "queue_url": queue_url,
            "queue_id": queue_id,
            "job_name": job_name,
        }

    def get_queue_item(self, queue_id):
        """获取队列项状态"""
        return self._get(f"queue/item/{queue_id}/api/json")

    def get_build_info(self, job_name, build_number):
        """获取编译信息"""
        return self._get(f"job/{job_name}/{build_number}/api/json")

    def get_build_console(self, job_name, build_number, start=0):
        """获取编译控制台输出"""
        resp = self.session.get(
            self._url(f"job/{job_name}/{build_number}/logText/progressiveText"),
            params={"start": start},
            timeout=30,
        )
        return {
            "text": resp.text,
            "offset": int(resp.headers.get("X-Text-Size", 0)),
            "more_data": resp.headers.get("X-More-Data", "false") == "true",
        }

    def poll_build(self, job_name, queue_id, interval=30, timeout_minutes=120):
        """轮询编译状态直到完成

        Yields:
            dict: 状态更新事件
        """
        # 等待队列分配 build number
        start_time = time.time()
        build_number = None

        while time.time() - start_time < timeout_minutes * 60:
            try:
                queue_info = self.get_queue_item(queue_id)
                if "executable" in queue_info:
                    build_number = queue_info["executable"]["number"]
                    yield {"event": "build_started", "build_number": build_number}
                    break
                elif queue_info.get("cancelled"):
                    yield {"event": "cancelled"}
                    return
                else:
                    yield {"event": "queued", "why": queue_info.get("why", "")}
            except requests.HTTPError:
                pass
            time.sleep(min(interval, 10))

        if not build_number:
            yield {"event": "timeout", "phase": "queue"}
            return

        # 轮询编译状态
        while time.time() - start_time < timeout_minutes * 60:
            try:
                build_info = self.get_build_info(job_name, build_number)
                if not build_info.get("building"):
                    yield {
                        "event": "completed",
                        "result": build_info.get("result"),
                        "duration_ms": build_info.get("duration"),
                        "url": build_info.get("url"),
                    }
                    return
                else:
                    elapsed = (time.time() - start_time) / 60
                    yield {"event": "building", "elapsed_minutes": round(elapsed, 1)}
            except requests.HTTPError:
                pass
            time.sleep(interval)

        yield {"event": "timeout", "phase": "build"}


def create_client(project=None):
    """从配置创建 Jenkins 客户端"""
    cfg = get_jenkins_config(project)
    if not cfg["host"]:
        raise ValueError("Jenkins host 未配置。请检查 services.json。")
    return JenkinsClient(
        host=cfg["host"],
        username=cfg["username"],
        api_token=cfg["api_token"],
    )
