"""补丁应用命令

支持 Gerrit cherry-pick、git format-patch、diff patch 等多种补丁方式。
通过 SSH 在远程代码服务器上执行补丁操作。
"""

import os
import tempfile

from commands.ssh import SSHClient
from core.config import get_ssh_config, get_gerrit_config, load_services_config, get_current_project
from core import output as out


def _get_repo_config(project=None):
    """获取仓库配置"""
    config = load_services_config()
    project = project or get_current_project()
    if not project:
        return {}
    proj_cfg = config.get("projects", {}).get(project, {})
    return {
        "root": proj_cfg.get("repo", {}).get("root", ""),
        "product": proj_cfg.get("repo", {}).get("product", ""),
    }


class PatchClient:
    """补丁应用客户端"""

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
        repo_cfg = _get_repo_config(project)
        self.repo_root = repo_cfg.get("root", "")

    def cherry_pick(self, refspec, repo_path, gerrit_project=None):
        """Gerrit cherry-pick

        Args:
            refspec: refs/changes/xx/xxxxx/N
            repo_path: 仓库相对路径 (如 frameworks/base)
            gerrit_project: Gerrit 项目路径 (如 general/platform/frameworks/base)
        """
        gerrit_cfg = get_gerrit_config(self.project)
        gerrit_host = gerrit_cfg.get("host", "")
        gerrit_port = gerrit_cfg.get("port", 29418)
        gerrit_user = gerrit_cfg.get("user", "")

        full_path = f"{self.repo_root}/{repo_path}" if repo_path else self.repo_root
        project = gerrit_project or repo_path

        cmd = (
            f"cd {full_path} && "
            f"git fetch ssh://{gerrit_user}@{gerrit_host}:{gerrit_port}/{project} {refspec} && "
            f"git cherry-pick FETCH_HEAD"
        )
        self.ssh.connect()
        try:
            return self.ssh.exec_command(cmd, timeout=120)
        finally:
            self.ssh.close()

    def apply_patch(self, patch_content, repo_path="", check_only=False):
        """应用 diff patch (git apply)

        Args:
            patch_content: patch 文件内容
            repo_path: 仓库相对路径
            check_only: 仅检查不真正应用
        """
        # 写入临时文件并上传
        full_path = f"{self.repo_root}/{repo_path}" if repo_path else self.repo_root
        remote_patch = "/tmp/cicd_cli_patch.patch"

        self.ssh.connect()
        try:
            # 通过 stdin 写入 patch
            cmd_write = f"cat > {remote_patch} << 'PATCH_EOF'\n{patch_content}\nPATCH_EOF"
            self.ssh.exec_command(cmd_write, timeout=30)

            if check_only:
                cmd = f"cd {full_path} && git apply --check {remote_patch}"
            else:
                cmd = f"cd {full_path} && git apply --check {remote_patch} && git apply {remote_patch}"

            result = self.ssh.exec_command(cmd, timeout=60)
            # 清理
            self.ssh.exec_command(f"rm -f {remote_patch}", timeout=10)
            return result
        finally:
            self.ssh.close()

    def git_am(self, patch_file_local, repo_path=""):
        """应用 format-patch (git am)

        先上传本地 patch 文件到远程，再 git am
        """
        full_path = f"{self.repo_root}/{repo_path}" if repo_path else self.repo_root
        remote_dir = "/tmp/cicd_cli_patches"
        filename = os.path.basename(patch_file_local)

        self.ssh.connect()
        try:
            self.ssh.exec_command(f"mkdir -p {remote_dir}", timeout=10)
            self.ssh.upload_file(patch_file_local, f"{remote_dir}/{filename}")
            cmd = f"cd {full_path} && git am {remote_dir}/{filename}"
            result = self.ssh.exec_command(cmd, timeout=60)
            self.ssh.exec_command(f"rm -rf {remote_dir}", timeout=10)
            return result
        finally:
            self.ssh.close()

    def upload_and_apply(self, local_path, repo_path="", method="apply"):
        """上传本地 patch 文件并应用

        Args:
            local_path: 本地 patch 文件路径
            repo_path: 远程仓库相对路径
            method: apply (git apply) 或 am (git am)
        """
        full_path = f"{self.repo_root}/{repo_path}" if repo_path else self.repo_root
        remote_patch = f"/tmp/{os.path.basename(local_path)}"

        self.ssh.connect()
        try:
            self.ssh.upload_file(local_path, remote_patch)
            if method == "am":
                cmd = f"cd {full_path} && git am {remote_patch}"
            else:
                cmd = f"cd {full_path} && git apply {remote_patch}"
            result = self.ssh.exec_command(cmd, timeout=60)
            self.ssh.exec_command(f"rm -f {remote_patch}", timeout=10)
            return result
        finally:
            self.ssh.close()

    def abort_cherry_pick(self, repo_path=""):
        """中止 cherry-pick"""
        full_path = f"{self.repo_root}/{repo_path}" if repo_path else self.repo_root
        self.ssh.connect()
        try:
            return self.ssh.exec_command(f"cd {full_path} && git cherry-pick --abort", timeout=30)
        finally:
            self.ssh.close()

    def abort_am(self, repo_path=""):
        """中止 git am"""
        full_path = f"{self.repo_root}/{repo_path}" if repo_path else self.repo_root
        self.ssh.connect()
        try:
            return self.ssh.exec_command(f"cd {full_path} && git am --abort", timeout=30)
        finally:
            self.ssh.close()


def create_client(project=None):
    """创建 PatchClient 实例"""
    return PatchClient(project)
