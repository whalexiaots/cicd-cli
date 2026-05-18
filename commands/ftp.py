"""FTP 文件下载命令

使用标准库 ftplib 实现，无第三方依赖。
支持: 下载、列目录、连接测试、完整性验证。
"""

import ftplib
import os
import hashlib
from pathlib import Path
from urllib.parse import urlparse

from core.config import get_ftp_config, get_ftp_servers
from core import output as out


class FTPClient:
    """FTP 客户端封装"""

    def __init__(self, host, port=21, user="anonymous", password="", timeout=30):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.timeout = timeout
        self._ftp = None

    def connect(self):
        """建立 FTP 连接"""
        self._ftp = ftplib.FTP()
        self._ftp.connect(self.host, self.port, timeout=self.timeout)
        self._ftp.login(self.user, self.password)
        self._ftp.set_pasv(True)
        return self

    def close(self):
        """关闭连接"""
        if self._ftp:
            try:
                self._ftp.quit()
            except Exception:
                self._ftp.close()
            self._ftp = None

    def list_dir(self, path="/"):
        """列出目录内容"""
        if not self._ftp:
            self.connect()
        entries = []
        self._ftp.cwd(path)
        self._ftp.retrlines("LIST", lambda line: entries.append(line))
        return entries

    def download(self, remote_path, local_path, callback=None):
        """下载文件（二进制模式）

        Args:
            remote_path: 远程文件路径
            local_path: 本地保存路径
            callback: 进度回调 (bytes_downloaded)

        Returns:
            dict: {status, local, remote, size}
        """
        if not self._ftp:
            self.connect()

        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        # 获取文件大小
        try:
            size = self._ftp.size(remote_path)
        except Exception:
            size = None

        downloaded = 0
        with open(local_path, "wb") as f:
            def write_chunk(data):
                nonlocal downloaded
                f.write(data)
                downloaded += len(data)
                if callback:
                    callback(downloaded)

            self._ftp.retrbinary(f"RETR {remote_path}", write_chunk, blocksize=65536)

        return {
            "status": "ok",
            "local": str(local_path),
            "remote": remote_path,
            "size": downloaded,
            "expected_size": size,
        }

    def test_connection(self):
        """测试连接"""
        try:
            self.connect()
            welcome = self._ftp.getwelcome()
            self.close()
            return {"status": "ok", "welcome": welcome}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()


def verify_file(filepath, expected_md5=None):
    """验证文件完整性"""
    filepath = Path(filepath)
    if not filepath.is_file():
        return {"status": "error", "message": "文件不存在"}

    result = {"status": "ok", "size": filepath.stat().st_size}

    # MD5 校验
    if expected_md5:
        md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                md5.update(chunk)
        actual_md5 = md5.hexdigest()
        result["md5"] = actual_md5
        if actual_md5 != expected_md5:
            result["status"] = "md5_mismatch"
            result["expected_md5"] = expected_md5

    # 压缩包魔数检查
    suffix = filepath.suffix.lower()
    with open(filepath, "rb") as f:
        header = f.read(4)

    magic_ok = True
    if suffix == ".zip" and header[:2] != b"PK":
        magic_ok = False
    elif suffix == ".gz" and header[:2] != b"\x1f\x8b":
        magic_ok = False
    elif suffix == ".7z" and header[:2] != b"7z":
        magic_ok = False

    if not magic_ok:
        result["status"] = "corrupted"
        result["message"] = f"文件魔数不匹配 ({suffix})"

    return result


def parse_ftp_url(url):
    """解析 FTP URL

    Returns:
        dict: {host, port, user, password, path}
    """
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "",
        "port": parsed.port or 21,
        "user": parsed.username or "anonymous",
        "password": parsed.password or "",
        "path": parsed.path or "/",
    }


def create_client(project=None, server_name=None):
    """从配置创建 FTP 客户端"""
    if server_name:
        servers = get_ftp_servers()
        cfg = servers.get(server_name, {})
        if not cfg:
            raise ValueError(f"FTP 服务器 '{server_name}' 不存在")
        return FTPClient(
            host=cfg.get("host", ""),
            port=cfg.get("port", 21),
            user=cfg.get("user", ""),
            password=cfg.get("password", ""),
        )

    cfg = get_ftp_config(project)
    if not cfg["host"]:
        raise ValueError("FTP host 未配置。请检查 services.json。")
    return FTPClient(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
    )
