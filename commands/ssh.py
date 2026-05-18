"""SSH 远程操作命令

提供 SSH 连接、命令执行、文件传输功能。
使用 paramiko 实现跨平台兼容。
"""

import os
import sys
from pathlib import Path

try:
    import paramiko
except ImportError:
    paramiko = None

from core.config import get_ssh_config
from core import output as out


class SSHClient:
    """SSH 客户端封装"""

    def __init__(self, host, port=22, user="", password="", key_file=None):
        if paramiko is None:
            raise ImportError("paramiko 未安装。请运行: pip install paramiko")
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.key_file = key_file
        self._client = None

    def connect(self):
        """建立 SSH 连接"""
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        kwargs = {
            "hostname": self.host,
            "port": self.port,
            "username": self.user,
            "timeout": 30,
        }
        if self.key_file and Path(self.key_file).is_file():
            kwargs["key_filename"] = self.key_file
        elif self.password:
            kwargs["password"] = self.password

        self._client.connect(**kwargs)
        return self

    def close(self):
        """关闭连接"""
        if self._client:
            self._client.close()
            self._client = None

    def exec_command(self, command, timeout=300):
        """执行远程命令

        Returns:
            dict: {exit_code, stdout, stderr}
        """
        if not self._client:
            self.connect()

        _, stdout, stderr = self._client.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()

        return {
            "exit_code": exit_code,
            "stdout": stdout.read().decode("utf-8", errors="replace"),
            "stderr": stderr.read().decode("utf-8", errors="replace"),
        }

    def upload_file(self, local_path, remote_path):
        """上传文件"""
        if not self._client:
            self.connect()

        sftp = self._client.open_sftp()
        try:
            sftp.put(str(local_path), str(remote_path))
            return {"status": "ok", "local": str(local_path), "remote": str(remote_path)}
        finally:
            sftp.close()

    def download_file(self, remote_path, local_path):
        """下载文件"""
        if not self._client:
            self.connect()

        sftp = self._client.open_sftp()
        try:
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            sftp.get(str(remote_path), str(local_path))
            return {"status": "ok", "remote": str(remote_path), "local": str(local_path)}
        finally:
            sftp.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()


def create_client(project=None):
    """从配置创建 SSH 客户端"""
    cfg = get_ssh_config(project)
    if not cfg["host"]:
        raise ValueError("SSH host 未配置。请检查 services.json 中的 ssh 配置。")
    return SSHClient(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
    )
