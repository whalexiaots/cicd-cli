"""elink Shortcuts

+login          登录易链
+status         检查 Token 状态
+project-list   查询项目
+ignore-review  一键忽略 Gerrit Review -2
"""

import argparse
import sys

from commands.elink import create_client, KNOWN_PROJECTS
from core.auth import elink_login
from core.config import get_elink_config, get_gerrit_config
from core import output as out


def handle_elink(args, fmt):
    """易链服务域入口"""
    parser = argparse.ArgumentParser(prog="cicd-cli elink")
    sub = parser.add_subparsers(dest="cmd")

    # +login
    sub.add_parser("+login", help="登录易链")

    # +status
    sub.add_parser("+status", help="检查 Token 状态")

    # +project-list
    pl_p = sub.add_parser("+project-list", help="查询项目")
    pl_p.add_argument("--name", help="按名称筛选")

    # +ignore-review
    ir_p = sub.add_parser("+ignore-review", help="忽略 Gerrit Review -2")
    ir_p.add_argument("change_id", help="Gerrit change number")
    ir_p.add_argument("--project-name", help="易链项目名称 (可自动推断)")
    ir_p.add_argument("--project-id", help="易链项目 ID (可自动推断)")
    ir_p.add_argument("--accounts", nargs="+", default=["checklog"],
                      help="忽略的检查账号 (默认: checklog)")
    ir_p.add_argument("--reason", default="c代码忽略cppcheck 检查",
                      help="忽略理由")

    remaining = sys.argv[3:] if len(sys.argv) > 3 else []
    e_args = parser.parse_args(remaining)

    project = getattr(args, "project", None)

    if not e_args.cmd:
        parser.print_help()
        return

    try:
        if e_args.cmd == "+login":
            result = elink_login()
            out.output(result, fmt)

        elif e_args.cmd == "+status":
            client = create_client(project)
            result = client.check_token()
            out.output(result, fmt)

        elif e_args.cmd == "+project-list":
            client = create_client(project)
            projects = client.project_list(getattr(e_args, "name", None))
            out.output({"projects": projects}, fmt)

        elif e_args.cmd == "+ignore-review":
            client = create_client(project)
            cfg = get_elink_config(project)
            gerrit_cfg = get_gerrit_config(project)

            # 确定项目信息
            project_id = e_args.project_id or cfg.get("project_id", "")
            project_name = e_args.project_name or cfg.get("project_name", "")

            # 从已知映射推断
            if not project_id and project_name and project_name in KNOWN_PROJECTS:
                project_id = KNOWN_PROJECTS[project_name]

            if not project_id or not project_name:
                out.error("请指定 --project-name 和 --project-id，或在配置中设置 elink.project_id/project_name")
                return

            gerrit_url = gerrit_cfg.get("host", "https://dev.example-corp.com/gerrit")
            module = cfg.get("module", 2)

            result = client.submit_ignore_check(
                project_id=project_id,
                project_name=project_name,
                commit_id=e_args.change_id,
                gerrit_url=gerrit_url,
                account_list=e_args.accounts,
                remark=e_args.reason,
                module=module,
            )
            out.output(result, fmt)

    except ValueError as e:
        out.error(str(e), hint="运行 cicd-cli auth login elink 登录")
        sys.exit(1)
    except Exception as e:
        out.error(str(e))
        sys.exit(1)
