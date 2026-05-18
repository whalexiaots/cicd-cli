"""FTP Shortcuts

+download   下载文件
+list       列出目录
+test       测试连接
+verify     验证文件完整性
"""

import argparse
import sys

from commands.ftp import create_client, parse_ftp_url, verify_file
from core.config import get_ftp_config
from core import output as out


def handle_ftp(args, fmt):
    """FTP 服务域入口"""
    parser = argparse.ArgumentParser(prog="cicd-cli ftp")
    sub = parser.add_subparsers(dest="cmd")

    # +download
    d_p = sub.add_parser("+download", help="下载文件")
    d_p.add_argument("url_or_path", help="FTP URL 或远程路径")
    d_p.add_argument("--local", help="本地保存路径")
    d_p.add_argument("--server", help="FTP 服务器名（来自 ftp_servers 配置）")
    d_p.add_argument("--retries", type=int, default=3, help="重试次数")

    # +list
    l_p = sub.add_parser("+list", help="列出目录")
    l_p.add_argument("path", nargs="?", default="/", help="远程目录路径")
    l_p.add_argument("--server", help="FTP 服务器名")

    # +test
    t_p = sub.add_parser("+test", help="测试连接")
    t_p.add_argument("--server", help="FTP 服务器名")

    # +verify
    v_p = sub.add_parser("+verify", help="验证本地文件完整性")
    v_p.add_argument("filepath", help="本地文件路径")
    v_p.add_argument("--md5", help="期望的 MD5 值")

    remaining = sys.argv[2:] if len(sys.argv) > 2 else []
    f_args = parser.parse_args(remaining)

    project = getattr(args, "project", None)

    if not f_args.cmd:
        parser.print_help()
        return

    try:
        if f_args.cmd == "+download":
            # 解析 URL 或使用配置
            if f_args.url_or_path.startswith("ftp://"):
                url_info = parse_ftp_url(f_args.url_or_path)
                from commands.ftp import FTPClient
                client = FTPClient(url_info["host"], url_info["port"],
                                   url_info["user"], url_info["password"])
                remote_path = url_info["path"]
            else:
                client = create_client(project, f_args.server)
                remote_path = f_args.url_or_path

            local_path = f_args.local or remote_path.split("/")[-1]

            # 带重试的下载
            last_error = None
            for attempt in range(f_args.retries):
                try:
                    with client:
                        result = client.download(remote_path, local_path)
                    result["attempt"] = attempt + 1
                    out.output(result, fmt)
                    return
                except Exception as e:
                    last_error = e
                    if attempt < f_args.retries - 1:
                        out.warning(f"下载失败 (第 {attempt + 1} 次): {e}")

            out.error(f"下载失败（重试 {f_args.retries} 次）: {last_error}")
            sys.exit(1)

        elif f_args.cmd == "+list":
            client = create_client(project, getattr(f_args, "server", None))
            with client:
                entries = client.list_dir(f_args.path)
            out.output({"path": f_args.path, "entries": entries}, fmt)

        elif f_args.cmd == "+test":
            client = create_client(project, getattr(f_args, "server", None))
            result = client.test_connection()
            out.output(result, fmt)

        elif f_args.cmd == "+verify":
            result = verify_file(f_args.filepath, getattr(f_args, "md5", None))
            out.output(result, fmt)

    except Exception as e:
        out.error(str(e), hint="检查 FTP 配置: cicd-cli auth status")
        sys.exit(1)
