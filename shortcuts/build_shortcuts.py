"""Build Shortcuts

+module       增量编译单模块
+kernel       编译 kernel
+image        编译指定 image
+nonhlos      编译 nonHLOS 子系统
+hlos         全量 HLOS 编译
+all          完整编译 (HLOS + nonHLOS + 打包)
+custom       自定义编译参数
"""

import argparse
import sys

from commands.build import create_client
from core import output as out


def handle_build(args, fmt):
    """Build 服务域入口"""
    parser = argparse.ArgumentParser(prog="cicd-cli build")
    sub = parser.add_subparsers(dest="cmd")

    # +module
    m_p = sub.add_parser("+module", help="增量编译单模块")
    m_p.add_argument("module", help="模块路径 (如 frameworks/base/services)")
    m_p.add_argument("--clean", action="store_true", help="Clean 编译")
    m_p.add_argument("--jobs", type=int, help="并发数 (默认 8)")
    m_p.add_argument("--no-log", action="store_true", help="不保存日志")

    # +kernel
    k_p = sub.add_parser("+kernel", help="编译 kernel")
    k_p.add_argument("--defconfig", help="defconfig 名称")
    k_p.add_argument("--no-log", action="store_true", help="不保存日志")

    # +image
    i_p = sub.add_parser("+image", help="编译指定 image")
    i_p.add_argument("type", choices=["bootimg", "sysimg", "usrimg"],
                     help="Image 类型")
    i_p.add_argument("--no-log", action="store_true", help="不保存日志")

    # +nonhlos
    n_p = sub.add_parser("+nonhlos", help="编译 nonHLOS")
    n_p.add_argument("--sub", choices=[
        "bl", "rpm", "aop", "tz", "adsp", "cdsp", "mpss", "soccp", "uefi"
    ], help="指定子系统 (不指定则全量 nonHLOS)")
    n_p.add_argument("--no-log", action="store_true", help="不保存日志")

    # +hlos
    h_p = sub.add_parser("+hlos", help="全量 HLOS 编译")
    h_p.add_argument("--clean", action="store_true", help="Clean 编译")
    h_p.add_argument("--jobs", type=int, help="并发数")
    h_p.add_argument("--no-ccache", action="store_true", help="关闭 CCACHE")
    h_p.add_argument("--no-log", action="store_true", help="不保存日志")

    # +all
    a_p = sub.add_parser("+all", help="完整编译")
    a_p.add_argument("--clean", action="store_true", help="Clean 编译")
    a_p.add_argument("--sign", action="store_true", help="编译后签名")
    a_p.add_argument("--pack", choices=[
        "fastboot", "flat", "meta", "ota", "sdk"
    ], help="编译后打包类型")
    a_p.add_argument("--no-log", action="store_true", help="不保存日志")

    # +custom
    c_p = sub.add_parser("+custom", help="自定义编译参数")
    c_p.add_argument("build_args", nargs=argparse.REMAINDER,
                     help="传递给 turbox_build.sh 的参数")
    c_p.add_argument("--timeout", type=int, default=7200, help="超时秒数")

    remaining = sys.argv[2:] if len(sys.argv) > 2 else []
    b_args = parser.parse_args(remaining)

    project = getattr(args, "project", None)

    if not b_args.cmd:
        parser.print_help()
        return

    try:
        client = create_client(project)

        if b_args.cmd == "+module":
            result = client.build_module(
                b_args.module,
                log=not b_args.no_log,
                clean=b_args.clean,
                jobs=b_args.jobs,
            )
            out.output(result, fmt)

        elif b_args.cmd == "+kernel":
            result = client.build_kernel(
                defconfig=b_args.defconfig,
                log=not b_args.no_log,
            )
            out.output(result, fmt)

        elif b_args.cmd == "+image":
            result = client.build_image(
                b_args.type,
                log=not b_args.no_log,
            )
            out.output(result, fmt)

        elif b_args.cmd == "+nonhlos":
            result = client.build_nonhlos(
                subsystem=b_args.sub,
                log=not b_args.no_log,
            )
            out.output(result, fmt)

        elif b_args.cmd == "+hlos":
            result = client.build_hlos(
                log=not b_args.no_log,
                clean=b_args.clean,
                jobs=b_args.jobs,
                no_ccache=b_args.no_ccache,
            )
            out.output(result, fmt)

        elif b_args.cmd == "+all":
            result = client.build_all(
                log=not b_args.no_log,
                clean=b_args.clean,
                sign=b_args.sign,
                pack=b_args.pack,
            )
            out.output(result, fmt)

        elif b_args.cmd == "+custom":
            custom = " ".join(b_args.build_args)
            result = client.build_custom(custom, timeout=b_args.timeout)
            out.output(result, fmt)

    except Exception as e:
        out.error(str(e), hint="检查 SSH/编译配置: cicd-cli config show")
        sys.exit(1)
