"""SSH Shortcuts

+exec     远程执行命令
+upload   上传文件
+download 下载文件
"""

import argparse
import sys

from commands.ssh import create_client
from core import output as out


def handle_ssh(args, fmt):
    """SSH 服务域入口"""
    parser = argparse.ArgumentParser(prog="cicd-cli ssh")
    sub = parser.add_subparsers(dest="cmd")

    # +exec
    exec_p = sub.add_parser("+exec", help="远程执行命令")
    exec_p.add_argument("command", nargs="+", help="要执行的命令")
    exec_p.add_argument("--timeout", type=int, default=300, help="超时秒数 (默认: 300)")

    # +upload
    up_p = sub.add_parser("+upload", help="上传文件")
    up_p.add_argument("--local", required=True, help="本地文件路径")
    up_p.add_argument("--remote", required=True, help="远程目标路径")

    # +download
    dl_p = sub.add_parser("+download", help="下载文件")
    dl_p.add_argument("--remote", required=True, help="远程文件路径")
    dl_p.add_argument("--local", required=True, help="本地保存路径")

    # 解析剩余参数
    remaining = args._remaining if hasattr(args, "_remaining") else sys.argv[2:]
    ssh_args = parser.parse_args(remaining)

    project = getattr(args, "project", None)

    if not ssh_args.cmd:
        parser.print_help()
        return

    try:
        client = create_client(project)

        if ssh_args.cmd == "+exec":
            cmd_str = " ".join(ssh_args.command)
            with client:
                result = client.exec_command(cmd_str, timeout=ssh_args.timeout)
            out.output(result, fmt)

        elif ssh_args.cmd == "+upload":
            with client:
                result = client.upload_file(ssh_args.local, ssh_args.remote)
            out.output(result, fmt)

        elif ssh_args.cmd == "+download":
            with client:
                result = client.download_file(ssh_args.remote, ssh_args.local)
            out.output(result, fmt)

    except Exception as e:
        out.error(str(e), hint="检查 SSH 配置: cicd-cli auth status")
        sys.exit(1)
