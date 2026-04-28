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

    required = ["host", "port", "debug", "history_file"]
    missing = [k for k in required if k not in web]
    if missing:
        raise ValueError(f"config.yaml 的 web 段缺少以下配置项: {', '.join(missing)}")

    return {
        "host": str(web["host"]),
        "port": int(web["port"]),
        "debug": bool(web["debug"]),
        "history_file": str(web["history_file"]),
    }


_web = _load_web_config()

HOST = _web["host"]
PORT = _web["port"]
DEBUG = _web["debug"]
HISTORY_FILE = _web["history_file"]
