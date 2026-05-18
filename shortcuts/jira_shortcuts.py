"""Jira Shortcuts

+my-bugs      查看我的未关闭 Bug
+create-bug   创建 Bug
+resolve      Resolve Issue
+search       JQL 搜索
+comment      添加评论
+transition   状态流转
"""

import argparse
import sys

from commands.jira import create_client
from core import output as out


def handle_jira(args, fmt):
    """Jira 服务域入口"""
    parser = argparse.ArgumentParser(prog="cicd-cli jira")
    sub = parser.add_subparsers(dest="cmd")

    # +my-bugs
    mb_p = sub.add_parser("+my-bugs", help="查看我的未关闭 Bug")
    mb_p.add_argument("--project", dest="jira_project", help="筛选项目")

    # +create-bug
    cb_p = sub.add_parser("+create-bug", help="创建 Bug")
    cb_p.add_argument("--project", dest="jira_project", required=True, help="项目 key")
    cb_p.add_argument("--summary", required=True, help="标题")
    cb_p.add_argument("--description", default="", help="描述")
    cb_p.add_argument("--priority", default="Major", help="优先级")
    cb_p.add_argument("--assignee", help="经办人")

    # +resolve
    r_p = sub.add_parser("+resolve", help="Resolve Issue")
    r_p.add_argument("key", help="Issue key (如 SILKY-123)")
    r_p.add_argument("--transition-id", default="771", help="Transition ID")
    r_p.add_argument("--comment", help="Resolve 评论")

    # +search
    s_p = sub.add_parser("+search", help="JQL 搜索")
    s_p.add_argument("jql", help="JQL 查询语句")
    s_p.add_argument("--limit", type=int, default=50, help="结果数量")

    # +comment
    c_p = sub.add_parser("+comment", help="添加评论")
    c_p.add_argument("key", help="Issue key")
    c_p.add_argument("--body", required=True, help="评论内容")

    # +transition
    t_p = sub.add_parser("+transition", help="状态流转")
    t_p.add_argument("key", help="Issue key")
    t_p.add_argument("--id", required=True, help="Transition ID")
    t_p.add_argument("--comment", help="流转评论")

    remaining = sys.argv[3:] if len(sys.argv) > 3 else []
    j_args = parser.parse_args(remaining)

    project = getattr(args, "project", None)

    if not j_args.cmd:
        parser.print_help()
        return

    try:
        client = create_client(project)

        if j_args.cmd == "+my-bugs":
            result = client.my_open_bugs(getattr(j_args, "jira_project", None))
            issues = result.get("issues", [])
            summary = [{
                "key": i["key"],
                "summary": i["fields"]["summary"],
                "status": i["fields"]["status"]["name"],
                "priority": i["fields"]["priority"]["name"],
            } for i in issues]
            out.output({"total": result.get("total", 0), "issues": summary}, fmt)

        elif j_args.cmd == "+create-bug":
            result = client.create_issue(
                project=j_args.jira_project,
                summary=j_args.summary,
                description=j_args.description,
                priority=j_args.priority,
                assignee=j_args.assignee,
            )
            out.output(result, fmt)

        elif j_args.cmd == "+resolve":
            result = client.transition_issue(
                j_args.key, j_args.transition_id, comment=j_args.comment,
            )
            out.output(result, fmt)

        elif j_args.cmd == "+search":
            result = client.search(j_args.jql, j_args.limit)
            out.output(result, fmt)

        elif j_args.cmd == "+comment":
            result = client.add_comment(j_args.key, j_args.body)
            out.output(result, fmt)

        elif j_args.cmd == "+transition":
            result = client.transition_issue(j_args.key, j_args.id, comment=j_args.comment)
            out.output(result, fmt)

    except Exception as e:
        out.error(str(e), hint="检查 Jira 配置: cicd-cli auth status")
        sys.exit(1)
