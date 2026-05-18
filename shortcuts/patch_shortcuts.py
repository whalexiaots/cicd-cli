"""Patch Shortcuts

+cherry-pick   Gerrit cherry-pick
+apply         应用 diff patch
+am            应用 format-patch (git am)
+upload        上传并应用本地 patch
+abort         中止当前 patch 操作
"""

import argparse
import sys

from commands.patch import create_client
from core import output as out


def handle_patch(args, fmt):
    """Patch 服务域入口"""
    parser = argparse.ArgumentParser(prog="cicd-cli patch")
    sub = parser.add_subparsers(dest="cmd")

    # +cherry-pick
    cp_p = sub.add_parser("+cherry-pick", help="Gerrit cherry-pick")
    cp_p.add_argument("refspec", help="Gerrit refspec (如 refs/changes/45/543945/1)")
    cp_p.add_argument("--repo", required=True, help="仓库相对路径 (如 frameworks/base)")
    cp_p.add_argument("--gerrit-project", help="Gerrit 项目路径 (默认与 --repo 相同)")

    # +apply
    ap_p = sub.add_parser("+apply", help="应用 diff patch")
    ap_p.add_argument("--file", help="本地 patch 文件路径")
    ap_p.add_argument("--content", help="patch 内容 (stdin)")
    ap_p.add_argument("--repo", default="", help="仓库相对路径")
    ap_p.add_argument("--check", action="store_true", help="仅检查，不真正应用")

    # +am
    am_p = sub.add_parser("+am", help="应用 format-patch")
    am_p.add_argument("file", help="本地 .patch 文件路径")
    am_p.add_argument("--repo", default="", help="仓库相对路径")

    # +upload
    up_p = sub.add_parser("+upload", help="上传并应用 patch")
    up_p.add_argument("file", help="本地 patch 文件路径")
    up_p.add_argument("--repo", default="", help="仓库相对路径")
    up_p.add_argument("--method", choices=["apply", "am"], default="apply",
                      help="应用方式 (默认 apply)")

    # +abort
    ab_p = sub.add_parser("+abort", help="中止 patch 操作")
    ab_p.add_argument("--type", choices=["cherry-pick", "am"], default="cherry-pick",
                      help="操作类型")
    ab_p.add_argument("--repo", default="", help="仓库相对路径")

    remaining = sys.argv[3:] if len(sys.argv) > 3 else []
    p_args = parser.parse_args(remaining)

    project = getattr(args, "project", None)

    if not p_args.cmd:
        parser.print_help()
        return

    try:
        client = create_client(project)

        if p_args.cmd == "+cherry-pick":
            result = client.cherry_pick(
                p_args.refspec,
                p_args.repo,
                gerrit_project=p_args.gerrit_project,
            )
            out.output(result, fmt)

        elif p_args.cmd == "+apply":
            if p_args.file:
                import pathlib
                content = pathlib.Path(p_args.file).read_text()
            elif p_args.content:
                content = p_args.content
            else:
                content = sys.stdin.read()
            result = client.apply_patch(content, p_args.repo, check_only=p_args.check)
            out.output(result, fmt)

        elif p_args.cmd == "+am":
            result = client.git_am(p_args.file, p_args.repo)
            out.output(result, fmt)

        elif p_args.cmd == "+upload":
            result = client.upload_and_apply(p_args.file, p_args.repo, p_args.method)
            out.output(result, fmt)

        elif p_args.cmd == "+abort":
            if p_args.type == "am":
                result = client.abort_am(p_args.repo)
            else:
                result = client.abort_cherry_pick(p_args.repo)
            out.output(result, fmt)

    except Exception as e:
        out.error(str(e), hint="检查 SSH/Gerrit 配置: cicd-cli auth status")
        sys.exit(1)
