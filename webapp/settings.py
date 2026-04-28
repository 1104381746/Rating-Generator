import yaml


def _load_web_config():
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        raise FileNotFoundError("config.yaml 文件不存在，请先复制 config.yaml.example 并填入配置")
    except yaml.YAMLError as e:
        raise ValueError(f"config.yaml 格式错误: {e}")

    web = data.get("web")
    if not isinstance(web, dict):
        raise ValueError("config.yaml 中缺少 web 配置段")

    required = ["host", "port", "debug", "rate_limit_per_day", "history_file", "rate_limit_file"]
    missing = [k for k in required if k not in web]
    if missing:
        raise ValueError(f"config.yaml 的 web 段缺少以下配置项: {', '.join(missing)}")

    return {
        "host": str(web["host"]),
        "port": int(web["port"]),
        "debug": bool(web["debug"]),
        "rate_limit_per_day": int(web["rate_limit_per_day"]),
        "history_file": str(web["history_file"]),
        "rate_limit_file": str(web["rate_limit_file"]),
    }


_web = _load_web_config()

HOST = _web["host"]
PORT = _web["port"]
DEBUG = _web["debug"]
RATE_LIMIT_PER_IP_PER_DAY = _web["rate_limit_per_day"]
HISTORY_FILE = _web["history_file"]
RATE_LIMIT_FILE = _web["rate_limit_file"]
