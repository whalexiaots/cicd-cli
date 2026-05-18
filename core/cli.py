"""cicd-cli 主入口

三层命令体系:
  Shortcuts (+前缀) → Commands → 直接 API 调用

用法:
  cicd-cli <service> +<shortcut> [flags]
  cicd-cli <service> <command> [flags]
  cicd-cli api <METHOD> <service> <path> [--data JSON]
"""

import argparse
import os
import sys

from core import __version__
from core import output as out
from core.config import (
    get_current_project,
    list_projects,
    load_services_config,
    set_current_project,
)
from core.auth import auth_status, elink_login
from shortcuts.ssh_shortcuts import handle_ssh
from shortcuts.gerrit_shortcuts import handle_gerrit


# ── 服务域注册表（各 commit 逐步追加） ──────────────────────
_SERVICE_HANDLERS = {
    "ssh": handle_ssh,
    "gerrit": handle_gerrit,
}


def register_service(name, handler):
    """注册服务域处理函数"""
    _SERVICE_HANDLERS[name] = handler


# ── config 子命令 ────────────────────────────────────────
def _handle_config(args, fmt):
    if not args.config_cmd:
        out.output({"hint": "用法: cicd-cli config init|show"}, fmt)
        return

    if args.config_cmd == "show":
        config = load_services_config()
        if config:
            out.output(config, fmt)
        else:
            out.error("未找到 services.json 配置文件",
                      hint="运行 cicd-cli config init 创建配置")
    elif args.config_cmd == "init":
        from core.config import get_config_dir, get_project_root
        config_dir = get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        target = config_dir / "services.json"

        if target.is_file():
            out.output({"status": "exists", "path": str(target)}, fmt)
            return

        # 复制 example 到配置目录
        example = get_project_root() / "config" / "services.json.example"
        if example.is_file():
            import shutil
            shutil.copy2(example, target)
            out.output({"status": "created", "path": str(target),
                        "hint": "请编辑配置文件填入实际凭证"}, fmt)
        else:
            out.error("找不到 services.json.example 模板")


# ── auth 子命令 ──────────────────────────────────────────
def _handle_auth(args, fmt):
    if not args.auth_cmd:
        out.output({"hint": "用法: cicd-cli auth status|login [service]"}, fmt)
        return

    project = os.environ.get("CICD_CLI_PROJECT") or getattr(args, "project", None)

    if args.auth_cmd == "status":
        result = auth_status(project)
        out.output(result, fmt)
    elif args.auth_cmd == "login":
        service = getattr(args, "auth_service", None)
        if service == "elink":
            result = elink_login()
            out.output(result, fmt)
        else:
            out.output({"hint": "目前支持: cicd-cli auth login elink"}, fmt)


# ── project 子命令 ───────────────────────────────────────
def _handle_project(args, fmt):
    if not args.project_cmd:
        out.output({"hint": "用法: cicd-cli project list|use|show"}, fmt)
        return

    if args.project_cmd == "list":
        config = load_services_config()
        projects = list_projects(config)
        out.output({"projects": projects, "current": get_current_project()}, fmt)

    elif args.project_cmd == "use":
        name = getattr(args, "project_name", None)
        if not name:
            out.error("请指定项目名称: cicd-cli project use <name>")
            return
        config = load_services_config()
        available = list_projects(config)
        if name not in available:
            out.error(f"项目 '{name}' 不存在", hint=f"可用项目: {', '.join(available)}")
            return
        set_current_project(name)
        out.output({"status": "ok", "project": name}, fmt)

    elif args.project_cmd == "show":
        project = get_current_project()
        if not project:
            out.output({"project": None, "hint": "未设置当前项目，使用 cicd-cli project use <name>"}, fmt)
            return
        config = load_services_config()
        project_cfg = config.get("projects", {}).get(project, {})
        out.output({"project": project, "config": project_cfg}, fmt)


# ── 公共选项（所有子命令继承） ────────────────────────────
_common_parser = argparse.ArgumentParser(add_help=False)
_common_parser.add_argument(
    "--project", metavar="NAME", help="临时指定项目（覆盖当前项目）"
)
_common_parser.add_argument(
    "--format",
    choices=["json", "pretty", "table"],
    default="json",
    help="输出格式 (默认: json)",
)


# ── 主解析器构建 ─────────────────────────────────────────
def build_parser():
    parser = argparse.ArgumentParser(
        prog="cicd-cli",
        description="CI/CD 命令行工具 — 为人类和 AI Agent 构建",
        parents=[_common_parser],
    )
    parser.add_argument(
        "--version", action="version", version=f"cicd-cli {__version__}"
    )

    sub = parser.add_subparsers(dest="service", help="服务域")

    # config 子命令
    config_p = sub.add_parser("config", help="配置管理", parents=[_common_parser])
    config_sub = config_p.add_subparsers(dest="config_cmd")
    config_sub.add_parser("init", help="初始化配置文件", parents=[_common_parser])
    config_sub.add_parser("show", help="显示当前配置", parents=[_common_parser])

    # auth 子命令
    auth_p = sub.add_parser("auth", help="认证管理", parents=[_common_parser])
    auth_sub = auth_p.add_subparsers(dest="auth_cmd")
    auth_sub.add_parser("status", help="查看认证状态", parents=[_common_parser])
    login_p = auth_sub.add_parser("login", help="登录服务", parents=[_common_parser])
    login_p.add_argument("auth_service", nargs="?", help="服务名 (elink)")

    # project 子命令
    proj_p = sub.add_parser("project", help="项目切换", parents=[_common_parser])
    proj_sub = proj_p.add_subparsers(dest="project_cmd")
    proj_sub.add_parser("list", help="列出所有项目", parents=[_common_parser])
    use_p = proj_sub.add_parser("use", help="切换当前项目", parents=[_common_parser])
    use_p.add_argument("project_name", help="项目名称")
    proj_sub.add_parser("show", help="显示当前项目配置", parents=[_common_parser])

    # 服务域（后续 commit 逐步注册）
    sub.add_parser("gerrit", help="Gerrit 代码审查", parents=[_common_parser])
    sub.add_parser("jenkins", help="Jenkins 编译", parents=[_common_parser])
    sub.add_parser("jira", help="Jira 问题跟踪", parents=[_common_parser])
    sub.add_parser("ssh", help="SSH 远程操作", parents=[_common_parser])
    sub.add_parser("ftp", help="FTP 文件下载", parents=[_common_parser])
    sub.add_parser("elink", help="易链代码管理", parents=[_common_parser])
    sub.add_parser("build", help="远程编译", parents=[_common_parser])
    sub.add_parser("review", help="代码审查", parents=[_common_parser])
    sub.add_parser("patch", help="补丁应用", parents=[_common_parser])
    sub.add_parser("flash", help="刷机验证", parents=[_common_parser])
    sub.add_parser("api", help="直接 API 调用", parents=[_common_parser])

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.service:
        parser.print_help()
        sys.exit(0)

    # 临时项目覆盖
    if getattr(args, "project", None):
        os.environ["CICD_CLI_PROJECT"] = args.project

    fmt = getattr(args, "format", "json")

    # 内置命令
    if args.service == "config":
        _handle_config(args, fmt)
    elif args.service == "auth":
        _handle_auth(args, fmt)
    elif args.service == "project":
        _handle_project(args, fmt)
    elif args.service in _SERVICE_HANDLERS:
        _SERVICE_HANDLERS[args.service](args, fmt)
    else:
        out.error(f"服务 '{args.service}' 尚未实现")
        sys.exit(1)


if __name__ == "__main__":
    main()
