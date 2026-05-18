"""刷机验证命令

从远程服务器下载构建产物，通过 fastboot/adb push 刷入设备。
"""

import os
import subprocess
import shutil

from commands.ssh import SSHClient
from core.config import get_ssh_config, load_services_config, get_current_project
from core import output as out


def _get_device_config(project=None):
    """获取设备相关配置"""
    config = load_services_config()
    project = project or get_current_project()
    if not project:
        return {}
    proj_cfg = config.get("projects", {}).get(project, {})
    return proj_cfg.get("device", {})


def _get_artifact_path(project=None):
    """获取远程产物路径"""
    config = load_services_config()
    project = project or get_current_project()
    if not project:
        return ""
    proj_cfg = config.get("projects", {}).get(project, {})
    repo_root = proj_cfg.get("repo", {}).get("root", "")
    product = proj_cfg.get("repo", {}).get("product", "")
    return f"{repo_root}/out/target/product/{product}"


def _run_local(cmd, timeout=60):
    """执行本地命令"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True,
            text=True, timeout=timeout
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except subprocess.TimeoutExpired:
        return {"returncode": -1, "stdout": "", "stderr": "timeout"}


class FlashClient:
    """刷机客户端"""

    def __init__(self, project=None):
        self.project = project
        ssh_cfg = get_ssh_config(project)
        self.ssh = SSHClient(
            host=ssh_cfg.get("host", ""),
            port=ssh_cfg.get("port", 22),
            user=ssh_cfg.get("user", ""),
            password=ssh_cfg.get("password", ""),
            key_file=ssh_cfg.get("key_file"),
        )
        self.device_cfg = _get_device_config(project)
        self.artifact_path = _get_artifact_path(project)

    def _serial_flag(self):
        """获取设备序列号标志"""
        serial = self.device_cfg.get("serial", "")
        return f"-s {serial}" if serial else ""

    def download_artifact(self, remote_file, local_dir="./artifacts"):
        """从远程下载单个产物"""
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, os.path.basename(remote_file))

        remote_full = remote_file if remote_file.startswith("/") else f"{self.artifact_path}/{remote_file}"

        self.ssh.connect()
        try:
            self.ssh.download_file(remote_full, local_path)
            return {"status": "ok", "local_path": local_path, "remote": remote_full}
        finally:
            self.ssh.close()

    def download_images(self, images, local_dir="./artifacts"):
        """批量下载 image 文件"""
        results = []
        self.ssh.connect()
        try:
            os.makedirs(local_dir, exist_ok=True)
            for img in images:
                remote = f"{self.artifact_path}/{img}"
                local = os.path.join(local_dir, img)
                try:
                    self.ssh.download_file(remote, local)
                    results.append({"file": img, "status": "ok"})
                except Exception as e:
                    results.append({"file": img, "status": "error", "error": str(e)})
            return {"downloaded": results}
        finally:
            self.ssh.close()

    def fastboot_flash(self, partition, image_path):
        """fastboot 刷单个分区"""
        serial = self._serial_flag()
        cmd = f"fastboot {serial} flash {partition} {image_path}"
        return _run_local(cmd, timeout=120)

    def fastboot_flash_all(self, artifact_dir="./artifacts", script="turbox_flash.sh"):
        """使用刷机脚本全量刷机"""
        script_path = os.path.join(artifact_dir, script)
        if not os.path.isfile(script_path):
            return {"status": "error", "error": f"找不到刷机脚本: {script_path}"}
        cmd = f"cd {artifact_dir} && bash {script} --all"
        return _run_local(cmd, timeout=600)

    def adb_push(self, local_path, remote_path):
        """adb push 文件到设备"""
        serial = self._serial_flag()
        cmd = f"adb {serial} push {local_path} {remote_path}"
        return _run_local(cmd, timeout=120)

    def adb_reboot(self, mode=""):
        """adb 重启设备"""
        serial = self._serial_flag()
        target = f" {mode}" if mode else ""
        cmd = f"adb {serial} reboot{target}"
        return _run_local(cmd, timeout=30)

    def check_device(self):
        """检查设备连接状态"""
        serial = self._serial_flag()
        # 先检查 adb
        adb_result = _run_local(f"adb {serial} devices")
        # 再检查 fastboot
        fb_result = _run_local(f"fastboot {serial} devices")
        return {
            "adb": adb_result.get("stdout", ""),
            "fastboot": fb_result.get("stdout", ""),
        }

    def verify_flash(self, expected_version=None):
        """验证刷机结果"""
        serial = self._serial_flag()
        results = {}

        # 获取设备属性
        props = [
            ("build.display.id", "版本号"),
            ("ro.build.date", "编译日期"),
            ("ro.build.type", "编译类型"),
        ]
        for prop, label in props:
            r = _run_local(f"adb {serial} shell getprop {prop}")
            results[label] = r.get("stdout", "N/A")

        if expected_version:
            results["version_match"] = expected_version in results.get("版本号", "")

        return results


def create_client(project=None):
    """创建 FlashClient 实例"""
    return FlashClient(project)
