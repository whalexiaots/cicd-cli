"""结构化输出格式化

支持三种输出格式:
  - json: 完整 JSON (默认, AI Agent 友好)
  - pretty: 人类友好格式
  - table: 表格格式
"""

import json
import sys


def output_json(data, file=None):
    """输出 JSON 格式到 stdout"""
    print(json.dumps(data, indent=2, ensure_ascii=False), file=file or sys.stdout)


def output_pretty(data, file=None):
    """输出人类友好格式"""
    out = file or sys.stdout
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                print(f"{key}:", file=out)
                _pretty_nested(value, indent=2, file=out)
            else:
                print(f"{key}: {value}", file=out)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                for k, v in item.items():
                    print(f"  {k}: {v}", file=out)
                print("---", file=out)
            else:
                print(f"  {item}", file=out)
    else:
        print(data, file=out)


def _pretty_nested(data, indent=0, file=None):
    out = file or sys.stdout
    prefix = " " * indent
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (list, dict)):
                print(f"{prefix}{k}:", file=out)
                _pretty_nested(v, indent + 2, file=out)
            else:
                print(f"{prefix}{k}: {v}", file=out)
    elif isinstance(data, list):
        for item in data:
            _pretty_nested(item, indent, file=out)
            if isinstance(item, dict):
                print(f"{prefix}---", file=out)


def output_table(data, file=None):
    """输出表格格式"""
    out = file or sys.stdout

    if isinstance(data, dict) and "services" in data:
        # auth status 专用格式
        items = data["services"]
    elif isinstance(data, list):
        items = data
    else:
        output_pretty(data, file)
        return

    if not items:
        print("(无数据)", file=out)
        return

    # 收集所有列
    columns = []
    for item in items:
        if isinstance(item, dict):
            for k in item:
                if k not in columns:
                    columns.append(k)

    if not columns:
        for item in items:
            print(str(item), file=out)
        return

    # 计算列宽
    widths = {col: len(col) for col in columns}
    for item in items:
        if isinstance(item, dict):
            for col in columns:
                val = str(item.get(col, ""))
                widths[col] = max(widths[col], len(val))

    # 打印表头
    header = " | ".join(col.ljust(widths[col]) for col in columns)
    sep = "-+-".join("-" * widths[col] for col in columns)
    print(header, file=out)
    print(sep, file=out)

    # 打印数据行
    for item in items:
        if isinstance(item, dict):
            row = " | ".join(str(item.get(col, "")).ljust(widths[col]) for col in columns)
            print(row, file=out)


def output(data, fmt="json", file=None):
    """根据格式输出数据"""
    if fmt == "pretty":
        output_pretty(data, file)
    elif fmt == "table":
        output_table(data, file)
    else:
        output_json(data, file)


def error(message, hint=None):
    """输出结构化错误到 stderr"""
    err = {"error": message}
    if hint:
        err["hint"] = hint
    print(json.dumps(err, ensure_ascii=False), file=sys.stderr)


def warning(message):
    """输出警告到 stderr"""
    print(json.dumps({"warning": message}, ensure_ascii=False), file=sys.stderr)
