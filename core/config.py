"""多项目配置管理

配置加载优先级:
  显式参数 > services.json (项目级) > services.json (全局) > 环境变量

配置搜索路径:
  1. ~/.cicd-cli/config/services.json
  2. {project_root}/config/services.json
  3. CICD_CLI_CONFIG 环境变量指定的路径
"""

import json
import os
import sys
from pathlib import Path


def get_config_dir():
    """获取配置目录路径"""
    return Path.home() / ".cicd-cli" / "config"


def get_secrets_dir():
    """获取凭证目录路径"""
    d = Path.home() / ".cicd-cli" / "secrets"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_project_root():
    """获取 cicd-cli 项目根目录"""
    return Path(__file__).resolve().parent.parent


def _search_paths():
    """返回 services.json 搜索路径列表"""
    paths = []
    env_path = os.environ.get("CICD_CLI_CONFIG")
    if env_path:
        paths.append(Path(env_path))
    paths.append(get_config_dir() / "services.json")
    paths.append(get_project_root() / "config" / "services.json")
    return paths


def load_services_config():
    """加载 services.json 配置

    Returns:
        dict: 解析后的配置，找不到文件则返回空 dict
    """
    for path in _search_paths():
        if path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f'{{"warning": "配置文件解析失败: {path}: {e}"}}', file=sys.stderr)
                continue
    return {}


def get_current_project():
    """获取当前激活的项目名称

    优先级: CICD_CLI_PROJECT 环境变量 > ~/.cicd-cli/config/current_project
    """
    env_project = os.environ.get("CICD_CLI_PROJECT")
    if env_project:
        return env_project
    state_file = get_config_dir() / "current_project"
    if state_file.is_file():
        return state_file.read_text(encoding="utf-8").strip()
    return None


def set_current_project(name):
    """设置当前激活的项目"""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "current_project").write_text(name, encoding="utf-8")


def list_projects(config=None):
    """列出所有配置的项目名称"""
    if config is None:
        config = load_services_config()
    projects = config.get("projects", {})
    return [k for k in projects if not k.startswith("_")]


def _merge_config(global_cfg, project_cfg):
    """合并全局配置和项目级覆盖"""
    result = dict(global_cfg)
    for key, value in project_cfg.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_config(result[key], value)
        elif value:
            result[key] = value
    return result


def get_service_config(service, project=None, config=None):
    """获取指定服务的配置（合并全局 + 项目级覆盖）

    Args:
        service: 服务名 (jenkins/gerrit/jira/ssh/ftp/elink)
        project: 项目名，None 则使用当前项目
        config: 预加载的配置，None 则自动加载

    Returns:
        dict: 合并后的服务配置
    """
    if config is None:
        config = load_services_config()

    if project is None:
        project = get_current_project()

    global_cfg = config.get(service, {})

    if project:
        project_cfg = config.get("projects", {}).get(project, {}).get(service, {})
        return _merge_config(global_cfg, project_cfg)

    return dict(global_cfg)


# 便捷方法：各服务配置获取

def get_ssh_config(project=None, config=None):
    cfg = get_service_config("ssh", project, config)
    return {
        "host": cfg.get("host", ""),
        "port": cfg.get("port", 22),
        "user": cfg.get("user", ""),
        "password": cfg.get("password", ""),
        "remote_dir": cfg.get("remote_dir", ""),
    }


def get_gerrit_config(project=None, config=None):
    cfg = get_service_config("gerrit", project, config)
    return {
        "host": cfg.get("host", ""),
        "port": cfg.get("port", 29418),
        "protocol": cfg.get("protocol", "https"),
        "username": cfg.get("auth", {}).get("username", ""),
        "http_password": cfg.get("auth", {}).get("http_password", ""),
    }


def get_jenkins_config(project=None, config=None):
    cfg = get_service_config("jenkins", project, config)
    return {
        "host": cfg.get("host", ""),
        "port": cfg.get("port", 8080),
        "username": cfg.get("auth", {}).get("username", ""),
        "api_token": cfg.get("auth", {}).get("api_token", ""),
        "job_name": cfg.get("job_name", ""),
        "job_url": cfg.get("job_url", ""),
        "default_params": cfg.get("default_params", {}),
    }


def get_jira_config(project=None, config=None):
    cfg = get_service_config("jira", project, config)
    return {
        "host": cfg.get("host", ""),
        "port": cfg.get("port", 443),
        "username": cfg.get("auth", {}).get("username", ""),
        "api_token": cfg.get("auth", {}).get("api_token", ""),
    }


def get_ftp_config(project=None, config=None):
    cfg = get_service_config("ftp", project, config)
    return {
        "host": cfg.get("host", ""),
        "port": cfg.get("port", 21),
        "user": cfg.get("user", ""),
        "password": cfg.get("password", ""),
        "local_dir": cfg.get("local_dir", str(Path.home() / "Downloads")),
        "max_retries": cfg.get("max_retries", 3),
    }


def get_elink_config(project=None, config=None):
    cfg = get_service_config("elink", project, config)
    return {
        "host": cfg.get("host", "elink.thundersoft.com"),
        "protocol": cfg.get("protocol", "https"),
        "username": cfg.get("auth", {}).get("username", ""),
        "password": cfg.get("auth", {}).get("password", ""),
        "aes_key": cfg.get("auth", {}).get("aes_key", ""),
        "secrets_path": cfg.get("secrets_path", str(get_secrets_dir() / "elink.json")),
        "module": cfg.get("module", 2),
        "project_id": cfg.get("project_id", ""),
        "project_name": cfg.get("project_name", ""),
    }


def get_ftp_servers(config=None):
    """获取 FTP 服务器池"""
    if config is None:
        config = load_services_config()
    return config.get("ftp_servers", {})
