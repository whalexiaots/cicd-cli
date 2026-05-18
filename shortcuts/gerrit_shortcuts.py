"""Gerrit Shortcuts

+dashboard    查看我的 Review 仪表板
+submit       提交代码到 Gerrit
+review       提交 Code Review
+cherry-pick  Cherry-pick change 到另一分支
+query        查询 changes
"""

import argparse
import sys

from commands.gerrit import create_client
from core import output as out


def handle_gerrit(args, fmt):
    """Gerrit 服务域入口"""
    parser = argparse.ArgumentParser(prog="cicd-cli gerrit")
    sub = parser.add_subparsers(dest="cmd")

    # +dashboard
    sub.add_parser("+dashboard", help="查看我的 Review")

    # +query
    q_p = sub.add_parser("+query", help="查询 changes")
    q_p.add_argument("query", nargs="?", default="is:open+owner:self", help="Gerrit 查询语句")
    q_p.add_argument("--limit", type=int, default=25, help="结果数量限制")

    # +review
    r_p = sub.add_parser("+review", help="提交 review")
    r_p.add_argument("change_id", help="Change ID 或编号")
    r_p.add_argument("--code-review", type=int, choices=[-2, -1, 0, 1, 2], help="Code-Review 分数")
    r_p.add_argument("--verified", type=int, choices=[-1, 0, 1], help="Verified 分数")
    r_p.add_argument("--message", help="Review 消息")

    # +cherry-pick
    cp_p = sub.add_parser("+cherry-pick", help="Cherry-pick")
    cp_p.add_argument("change_id", help="Change ID")
    cp_p.add_argument("--branch", required=True, help="目标分支")
    cp_p.add_argument("--message", help="Commit message")

    # +detail
    d_p = sub.add_parser("+detail", help="查看 change 详情")
    d_p.add_argument("change_id", help="Change ID")

    remaining = sys.argv[2:] if len(sys.argv) > 2 else []
    gerrit_args = parser.parse_args(remaining)

    project = getattr(args, "project", None)

    if not gerrit_args.cmd:
        parser.print_help()
        return

    try:
        client = create_client(project)

        if gerrit_args.cmd == "+dashboard":
            result = client.dashboard()
            out.output(result, fmt)

        elif gerrit_args.cmd == "+query":
            result = client.query_changes(gerrit_args.query, gerrit_args.limit)
            out.output(result, fmt)

        elif gerrit_args.cmd == "+review":
            labels = {}
            if gerrit_args.code_review is not None:
                labels["Code-Review"] = gerrit_args.code_review
            if gerrit_args.verified is not None:
                labels["Verified"] = gerrit_args.verified
            result = client.set_review(
                gerrit_args.change_id,
                labels=labels or None,
                message=gerrit_args.message,
            )
            out.output(result, fmt)

        elif gerrit_args.cmd == "+cherry-pick":
            result = client.cherry_pick(
                gerrit_args.change_id, "current",
                gerrit_args.branch, gerrit_args.message,
            )
            out.output(result, fmt)

        elif gerrit_args.cmd == "+detail":
            result = client.get_change(gerrit_args.change_id)
            out.output(result, fmt)

    except Exception as e:
        out.error(str(e), hint="检查 Gerrit 配置: cicd-cli auth status")
        sys.exit(1)
