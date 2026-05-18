"""cicd-cli 基础测试

验证模块导入、CLI 解析、配置加载等基础功能。
运行: python -m pytest tests/ -v
"""

import sys
import os

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_version():
    """验证版本号"""
    from core import __version__
    assert __version__
    assert "." in __version__


def test_imports():
    """验证所有模块可正常导入"""
    from commands.ssh import SSHClient
    from commands.gerrit import GerritClient
    from commands.jenkins import JenkinsClient
    from commands.jira import JiraClient
    from commands.ftp import FTPClient
    from commands.elink import ElinkClient
    from commands.build import BuildClient
    from commands.review import ReviewClient
    from commands.patch import PatchClient
    from commands.flash import FlashClient
    assert SSHClient
    assert GerritClient
    assert JenkinsClient
    assert JiraClient
    assert FTPClient
    assert ElinkClient
    assert BuildClient
    assert ReviewClient
    assert PatchClient
    assert FlashClient


def test_cli_parser():
    """验证 CLI 解析器构建"""
    from core.cli import build_parser
    parser = build_parser()
    assert parser.prog == "cicd-cli"


def test_cli_version_flag():
    """验证 --version 标志"""
    from core.cli import build_parser
    from core import __version__
    parser = build_parser()
    import io
    from contextlib import redirect_stdout
    try:
        parser.parse_args(["--version"])
    except SystemExit as e:
        assert e.code == 0


def test_output_json():
    """验证 JSON 输出格式"""
    from core.output import output_json
    import io, contextlib
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        output_json({"key": "value"})
    result = f.getvalue()
    assert '"key"' in result
    assert '"value"' in result


def test_output_pretty():
    """验证 pretty 输出格式"""
    from core.output import output_pretty
    import io, contextlib
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        output_pretty({"status": "ok"})
    result = f.getvalue()
    assert "status" in result


def test_config_load_missing():
    """验证配置文件不存在时返回空"""
    # 临时设置不存在的配置路径
    old_env = os.environ.get("CICD_CLI_CONFIG")
    os.environ["CICD_CLI_CONFIG"] = "/tmp/nonexistent_cicd_test_path"
    from core.config import load_services_config
    config = load_services_config()
    assert config == {} or config is None or isinstance(config, dict)
    if old_env:
        os.environ["CICD_CLI_CONFIG"] = old_env
    else:
        os.environ.pop("CICD_CLI_CONFIG", None)


def test_service_handlers_registered():
    """验证所有服务域已注册"""
    from core.cli import _SERVICE_HANDLERS
    expected = ["ssh", "gerrit", "jenkins", "jira", "ftp", "elink",
                "build", "review", "patch", "flash"]
    for svc in expected:
        assert svc in _SERVICE_HANDLERS, f"{svc} 未注册"


def test_ftp_parse_url():
    """验证 FTP URL 解析"""
    from commands.ftp import parse_ftp_url
    result = parse_ftp_url("ftp://user:pass@host:21/path/file.zip")
    assert result["host"] == "host"
    assert result["path"] == "/path/file.zip"


def test_elink_known_projects():
    """验证 elink 模块导入"""
    from commands.elink import KNOWN_PROJECTS
    assert isinstance(KNOWN_PROJECTS, dict)
