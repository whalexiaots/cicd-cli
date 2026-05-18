"""cicd-cli 主入口

三层命令体系:
  Shortcuts (+前缀) → Commands → 直接 API 调用

用法:
  cicd-cli <service> +<shortcut> [flags]
  cicd-cli <service> <command> [flags]
  cicd-cli api <METHOD> <service> <path> [--data JSON]
"""

import argparse
import sys

from core import __version__


def build_parser():
    parser = argparse.ArgumentParser(
        prog="cicd-cli",
        description="CI/CD 命令行工具 — 为人类和 AI Agent 构建",
    )
    parser.add_argument(
        "--version", action="version", version=f"cicd-cli {__version__}"
    )
    parser.add_argument(
        "--project", metavar="NAME", help="临时指定项目（覆盖当前项目）"
    )
    parser.add_argument(
        "--format",
        choices=["json", "pretty", "table"],
        default="json",
        help="输出格式 (默认: json)",
    )

    sub = parser.add_subparsers(dest="service", help="服务域")

    # 顶层命令
    sub.add_parser("config", help="配置管理")
    sub.add_parser("auth", help="认证管理")
    sub.add_parser("project", help="项目切换")

    # 服务域（后续 commit 逐步注册）
    sub.add_parser("gerrit", help="Gerrit 代码审查")
    sub.add_parser("jenkins", help="Jenkins 编译")
    sub.add_parser("jira", help="Jira 问题跟踪")
    sub.add_parser("ssh", help="SSH 远程操作")
    sub.add_parser("ftp", help="FTP 文件下载")
    sub.add_parser("elink", help="易链代码管理")
    sub.add_parser("build", help="远程编译")
    sub.add_parser("review", help="代码审查")
    sub.add_parser("patch", help="补丁应用")
    sub.add_parser("flash", help="刷机验证")
    sub.add_parser("api", help="直接 API 调用")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.service:
        parser.print_help()
        sys.exit(0)

    # 后续各 commit 会注册具体的 service handler
    print(f'{{"error": "service \'{args.service}\' not yet implemented"}}')
    sys.exit(1)


if __name__ == "__main__":
    main()
