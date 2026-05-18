"""远程编译命令

通过 SSH 在代码服务器上执行 turbox_build.sh 编译脚本。
支持增量/全量/单模块/nonHLOS 子系统编译。
"""

import time

from commands.ssh import SSHClient
from core.config import get_ssh_config, load_services_config, get_current_project
from core import output as out


# 默认超时（秒）
_TIMEOUT_MAP = {
    "module": 1800,       # 30 min
    "kernel": 2700,       # 45 min
    "nonhlos_single": 2700,
    "hlos": 7200,         # 120 min
    "nonhlos": 5400,      # 90 min
    "all": 10800,         # 180 min
    "clean": 14400,       # 240 min
}


def _get_build_config(project=None):
    """获取编译相关配置"""
    config = load_services_config()
    project = project or get_current_project()
    if not project:
        return {}
    proj_cfg = config.get("projects", {}).get(project, {})
    return {
        "repo_root": proj_cfg.get("repo", {}).get("root", ""),
        "product": proj_cfg.get("repo", {}).get("product", ""),
        "variant": proj_cfg.get("repo", {}).get("variant", "userdebug"),
        "ssh": proj_cfg.get("ssh", config.get("ssh", {})),
    }


def _build_command(repo_root, product, variant, build_args):
    """构造完整编译命令"""
    parts = [
        f"cd {repo_root}",
        "source build/envsetup.sh",
        f"lunch {product}-{variant}",
        f"./turbox_build.sh {build_args}",
    ]
    return " && ".join(parts)


class BuildClient:
    """远程编译客户端"""

    def __init__(self, project=None):
        self.project = project
        self.build_cfg = _get_build_config(project)
        ssh_cfg = self.build_cfg.get("ssh", {})
        if not ssh_cfg:
            ssh_cfg = get_ssh_config(project)
        self.ssh = SSHClient(
            host=ssh_cfg.get("host", ""),
            port=ssh_cfg.get("port", 22),
            user=ssh_cfg.get("user", ""),
            password=ssh_cfg.get("password", ""),
            key_file=ssh_cfg.get("key_file"),
        )
        self.repo_root = self.build_cfg.get("repo_root", "")
        self.product = self.build_cfg.get("product", "")
        self.variant = self.build_cfg.get("variant", "userdebug")

    def _exec_build(self, build_args, timeout=7200):
        """执行编译命令"""
        if not self.repo_root:
            raise ValueError("未配置 repo root，请在 services.json 中设置 projects.<name>.repo.root")
        if not self.product:
            raise ValueError("未配置 product，请在 services.json 中设置 projects.<name>.repo.product")

        cmd = _build_command(self.repo_root, self.product, self.variant, build_args)
        self.ssh.connect()
        try:
            result = self.ssh.exec_command(cmd, timeout=timeout)
            return result
        finally:
            self.ssh.close()

    def build_module(self, module, log=True, clean=False, jobs=None):
        """增量编译单模块"""
        args = "-a --ap-m " + module
        if log:
            args += " -l"
        if clean:
            args += " -c"
        if jobs:
            args += f" --ap-j {jobs}"
        timeout = _TIMEOUT_MAP["module"]
        return self._exec_build(args, timeout)

    def build_kernel(self, defconfig=None, log=True):
        """编译 kernel"""
        args = "-a --ap-k"
        if defconfig:
            args += f" {defconfig}"
        if log:
            args += " -l"
        return self._exec_build(args, _TIMEOUT_MAP["kernel"])

    def build_image(self, image_type, log=True):
        """编译指定 image (bootimg/sysimg/usrimg)"""
        args = f"-a --ap-i {image_type}"
        if log:
            args += " -l"
        return self._exec_build(args, _TIMEOUT_MAP["module"])

    def build_nonhlos(self, subsystem=None, log=True):
        """编译 nonHLOS (单个子系统或全量)"""
        if subsystem:
            args = f"--{subsystem}"
            timeout = _TIMEOUT_MAP["nonhlos_single"]
        else:
            args = "-b"
            timeout = _TIMEOUT_MAP["nonhlos"]
        if log:
            args += " -l"
        return self._exec_build(args, timeout)

    def build_hlos(self, log=True, clean=False, jobs=None, no_ccache=False):
        """全量 HLOS 编译"""
        args = "-a"
        if log:
            args += " -l"
        if clean:
            args += " -c"
        if jobs:
            args += f" --ap-j {jobs}"
        if no_ccache:
            args += " --ap-s false"
        return self._exec_build(args, _TIMEOUT_MAP["hlos"])

    def build_all(self, log=True, clean=False, sign=False, pack=None):
        """完整编译 (HLOS + nonHLOS)"""
        args = "--all"
        if log:
            args += " -l"
        if clean:
            args += " -c"
        if sign:
            args += " --sign"
        if pack:
            args += f" --zip_{pack}_build"
        timeout = _TIMEOUT_MAP["clean"] if clean else _TIMEOUT_MAP["all"]
        return self._exec_build(args, timeout)

    def build_custom(self, custom_args, timeout=7200):
        """自定义编译参数"""
        return self._exec_build(custom_args, timeout)


def create_client(project=None):
    """创建 BuildClient 实例"""
    return BuildClient(project)
