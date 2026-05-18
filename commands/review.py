"""代码审查命令

通过 SSH 在远程执行代码格式检查工具，
并提供 AI 辅助的代码逻辑审查能力。
"""

from commands.ssh import SSHClient
from core.config import get_ssh_config, load_services_config, get_current_project
from core import output as out


# 文件类型与检查工具映射
_TOOL_MAP = {
    ".c": ("clang-format", "clang-format --dry-run -Werror {file}"),
    ".h": ("clang-format", "clang-format --dry-run -Werror {file}"),
    ".cpp": ("clang-format", "clang-format --dry-run -Werror {file}"),
    ".cc": ("clang-format", "clang-format --dry-run -Werror {file}"),
    ".sh": ("shellcheck", "shellcheck {file}"),
    ".py": ("flake8", "flake8 {file}"),
    ".java": ("google-java-format", "google-java-format --dry-run {file}"),
    ".kt": ("google-java-format", "google-java-format --dry-run {file}"),
}

# kernel 路径下的 C 文件用 checkpatch
_KERNEL_PATHS = ("kernel/", "drivers/", "arch/", "include/linux/")


def _get_repo_root(project=None):
    """获取远程仓库根目录"""
    config = load_services_config()
    project = project or get_current_project()
    if not project:
        return ""
    proj_cfg = config.get("projects", {}).get(project, {})
    return proj_cfg.get("repo", {}).get("root", "")


class ReviewClient:
    """代码审查客户端"""

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
        self.repo_root = _get_repo_root(project)

    def get_diff(self, commits=1):
        """获取最近 N 个 commit 的 diff"""
        cmd = f"cd {self.repo_root} && git diff HEAD~{commits} --stat && echo '---FULL---' && git diff HEAD~{commits}"
        self.ssh.connect()
        try:
            result = self.ssh.exec_command(cmd, timeout=60)
            return result
        finally:
            self.ssh.close()

    def get_changed_files(self, commits=1):
        """获取变更文件列表"""
        cmd = f"cd {self.repo_root} && git diff HEAD~{commits} --name-only"
        self.ssh.connect()
        try:
            result = self.ssh.exec_command(cmd, timeout=30)
            files = [f for f in result.get("stdout", "").strip().split("\n") if f]
            return {"files": files, "count": len(files)}
        finally:
            self.ssh.close()

    def run_format_check(self, files=None, commits=1):
        """对变更文件执行格式检查"""
        if not files:
            changed = self.get_changed_files(commits)
            files = changed["files"]

        results = []
        commands = []

        for f in files:
            ext = "." + f.rsplit(".", 1)[-1] if "." in f else ""
            # kernel 路径下用 checkpatch
            if ext in (".c", ".h") and any(f.startswith(p) for p in _KERNEL_PATHS):
                tool = "checkpatch"
                cmd = f"scripts/checkpatch.pl --no-tree -f {f}"
            elif ext in _TOOL_MAP:
                tool, cmd_tpl = _TOOL_MAP[ext]
                cmd = cmd_tpl.format(file=f)
            else:
                continue
            commands.append((f, tool, cmd))

        if not commands:
            return {"status": "skip", "message": "无需检查的文件类型"}

        # 批量执行
        batch_cmd = " && ".join(
            f"echo '=== {f} ===' && (cd {self.repo_root} && {cmd} 2>&1) || true"
            for f, _, cmd in commands
        )
        self.ssh.connect()
        try:
            result = self.ssh.exec_command(batch_cmd, timeout=120)
            return {
                "status": "done",
                "checked_files": len(commands),
                "tools_used": list(set(t for _, t, _ in commands)),
                "output": result.get("stdout", ""),
            }
        finally:
            self.ssh.close()

    def get_commit_message(self, commits=1):
        """获取 commit message 用于审查"""
        cmd = f"cd {self.repo_root} && git log -{commits} --format='%H%n%s%n%b%n---COMMIT---'"
        self.ssh.connect()
        try:
            result = self.ssh.exec_command(cmd, timeout=30)
            return result
        finally:
            self.ssh.close()


def create_client(project=None):
    """创建 ReviewClient 实例"""
    return ReviewClient(project)
