"""Flash Shortcuts

+download     下载产物
+fastboot     fastboot 刷机
+push         adb push
+reboot       重启设备
+check        检查设备状态
+verify       验证刷机结果
"""

import argparse
import sys

from commands.flash import create_client
from core import output as out


def handle_flash(args, fmt):
    """Flash 服务域入口"""
    parser = argparse.ArgumentParser(prog="cicd-cli flash")
    sub = parser.add_subparsers(dest="cmd")

    # +download
    dl_p = sub.add_parser("+download", help="下载构建产物")
    dl_p.add_argument("--images", nargs="+",
                      default=["boot.img"],
                      help="要下载的 image 文件 (默认 boot.img)")
    dl_p.add_argument("--dir", default="./artifacts", help="本地保存目录")
    dl_p.add_argument("--file", help="指定单个远程文件路径")

    # +fastboot
    fb_p = sub.add_parser("+fastboot", help="fastboot 刷机")
    fb_p.add_argument("--partition", help="分区名 (如 boot, system)")
    fb_p.add_argument("--image", help="Image 文件路径")
    fb_p.add_argument("--all", action="store_true", help="使用刷机脚本全量刷")
    fb_p.add_argument("--dir", default="./artifacts", help="产物目录")

    # +push
    push_p = sub.add_parser("+push", help="adb push")
    push_p.add_argument("local", help="本地文件路径")
    push_p.add_argument("remote", help="设备目标路径")

    # +reboot
    rb_p = sub.add_parser("+reboot", help="重启设备")
    rb_p.add_argument("--mode", choices=["", "bootloader", "recovery", "fastboot"],
                      default="", help="重启模式")

    # +check
    sub.add_parser("+check", help="检查设备连接")

    # +verify
    v_p = sub.add_parser("+verify", help="验证刷机结果")
    v_p.add_argument("--version", help="期望的版本号")

    remaining = sys.argv[2:] if len(sys.argv) > 2 else []
    f_args = parser.parse_args(remaining)

    project = getattr(args, "project", None)

    if not f_args.cmd:
        parser.print_help()
        return

    try:
        client = create_client(project)

        if f_args.cmd == "+download":
            if f_args.file:
                result = client.download_artifact(f_args.file, f_args.dir)
            else:
                result = client.download_images(f_args.images, f_args.dir)
            out.output(result, fmt)

        elif f_args.cmd == "+fastboot":
            if f_args.all:
                result = client.fastboot_flash_all(f_args.dir)
            elif f_args.partition and f_args.image:
                result = client.fastboot_flash(f_args.partition, f_args.image)
            else:
                out.error("请指定 --all 或 --partition + --image")
                return
            out.output(result, fmt)

        elif f_args.cmd == "+push":
            result = client.adb_push(f_args.local, f_args.remote)
            out.output(result, fmt)

        elif f_args.cmd == "+reboot":
            result = client.adb_reboot(f_args.mode)
            out.output(result, fmt)

        elif f_args.cmd == "+check":
            result = client.check_device()
            out.output(result, fmt)

        elif f_args.cmd == "+verify":
            result = client.verify_flash(expected_version=f_args.version)
            out.output(result, fmt)

    except Exception as e:
        out.error(str(e), hint="检查设备连接和配置")
        sys.exit(1)
