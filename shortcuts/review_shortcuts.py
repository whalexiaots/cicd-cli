"""Review Shortcuts

+diff         获取最近变更的 diff
+files        列出变更文件
+format       自动格式检查
+commit-msg   检查 commit message
"""

import argparse
import sys

from commands.review import create_client
from core import output as out


def handle_review(args, fmt):
    """Review 服务域入口"""
    parser = argparse.ArgumentParser(prog="cicd-cli review")
    sub = parser.add_subparsers(dest="cmd")

    # +diff
    d_p = sub.add_parser("+diff", help="获取变更 diff")
    d_p.add_argument("--commits", type=int, default=1, help="回溯 commit 数 (默认 1)")

    # +files
    f_p = sub.add_parser("+files", help="列出变更文件")
    f_p.add_argument("--commits", type=int, default=1, help="回溯 commit 数")

    # +format
    fmt_p = sub.add_parser("+format", help="格式检查")
    fmt_p.add_argument("--commits", type=int, default=1, help="回溯 commit 数")
    fmt_p.add_argument("--file", action="append", help="指定文件 (可多次)")

    # +commit-msg
    cm_p = sub.add_parser("+commit-msg", help="检查 commit message")
    cm_p.add_argument("--commits", type=int, default=1, help="回溯 commit 数")

    remaining = sys.argv[2:] if len(sys.argv) > 2 else []
    r_args = parser.parse_args(remaining)

    project = getattr(args, "project", None)

    if not r_args.cmd:
        parser.print_help()
        return

    try:
        client = create_client(project)

        if r_args.cmd == "+diff":
            result = client.get_diff(commits=r_args.commits)
            out.output(result, fmt)

        elif r_args.cmd == "+files":
            result = client.get_changed_files(commits=r_args.commits)
            out.output(result, fmt)

        elif r_args.cmd == "+format":
            result = client.run_format_check(
                files=r_args.file,
                commits=r_args.commits,
            )
            out.output(result, fmt)

        elif r_args.cmd == "+commit-msg":
            result = client.get_commit_message(commits=r_args.commits)
            out.output(result, fmt)

    except Exception as e:
        out.error(str(e), hint="检查 SSH 配置: cicd-cli auth status")
        sys.exit(1)
