"""Jenkins Shortcuts

+trigger      触发编译
+poll         轮询编译状态
+info         查看编译信息
+console      查看控制台输出
"""

import argparse
import sys

from commands.jenkins import create_client
from core.config import get_jenkins_config
from core import output as out


def handle_jenkins(args, fmt):
    """Jenkins 服务域入口"""
    parser = argparse.ArgumentParser(prog="cicd-cli jenkins")
    sub = parser.add_subparsers(dest="cmd")

    # +trigger
    t_p = sub.add_parser("+trigger", help="触发编译")
    t_p.add_argument("--job", help="Job 名称（默认使用项目配置）")
    t_p.add_argument("--change-id", help="Gerrit Change ID（多个用空格分隔）")
    t_p.add_argument("--branch", help="分支名")
    t_p.add_argument("--params", help="额外参数 (JSON)")

    # +poll
    p_p = sub.add_parser("+poll", help="轮询编译状态")
    p_p.add_argument("--job", required=True, help="Job 名称")
    p_p.add_argument("--queue-id", required=True, help="队列 ID")
    p_p.add_argument("--interval", type=int, default=30, help="轮询间隔秒数")
    p_p.add_argument("--timeout", type=int, default=120, help="超时分钟数")

    # +info
    i_p = sub.add_parser("+info", help="查看编译信息")
    i_p.add_argument("--job", required=True, help="Job 名称")
    i_p.add_argument("--build", required=True, type=int, help="Build 编号")

    # +console
    c_p = sub.add_parser("+console", help="查看控制台输出")
    c_p.add_argument("--job", required=True, help="Job 名称")
    c_p.add_argument("--build", required=True, type=int, help="Build 编号")
    c_p.add_argument("--tail", type=int, default=100, help="尾部行数")

    remaining = sys.argv[3:] if len(sys.argv) > 3 else []
    j_args = parser.parse_args(remaining)

    project = getattr(args, "project", None)

    if not j_args.cmd:
        parser.print_help()
        return

    try:
        client = create_client(project)
        cfg = get_jenkins_config(project)

        if j_args.cmd == "+trigger":
            job_name = j_args.job or cfg.get("job_name", "")
            if not job_name:
                out.error("请指定 --job 或在配置中设置 job_name")
                return

            params = dict(cfg.get("default_params", {}))
            if j_args.change_id:
                params["GERRIT_ID"] = j_args.change_id
            if j_args.branch:
                params["BRANCH"] = j_args.branch
            if j_args.params:
                import json
                params.update(json.loads(j_args.params))

            result = client.trigger_build(job_name, params)
            out.output(result, fmt)

        elif j_args.cmd == "+poll":
            for event in client.poll_build(j_args.job, j_args.queue_id,
                                           j_args.interval, j_args.timeout):
                out.output(event, fmt)
                if event["event"] in ("completed", "cancelled", "timeout"):
                    break

        elif j_args.cmd == "+info":
            result = client.get_build_info(j_args.job, j_args.build)
            out.output(result, fmt)

        elif j_args.cmd == "+console":
            result = client.get_build_console(j_args.job, j_args.build)
            lines = result["text"].split("\n")
            tail_lines = lines[-j_args.tail:] if len(lines) > j_args.tail else lines
            out.output({"lines": tail_lines, "total": len(lines)}, fmt)

    except Exception as e:
        out.error(str(e), hint="检查 Jenkins 配置: cicd-cli auth status")
        sys.exit(1)
