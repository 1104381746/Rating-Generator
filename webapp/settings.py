import os

import yaml


def _load_web_config():
    cfg = {
        "host": "127.0.0.1",
        "port": 5000,
        "debug": False,
        "rate_limit_per_day": 10,
        "history_file": "history.jsonl",
        "rate_limit_file": "rate_limits.json",
    }
    try:
        if os.path.exists("config.yaml"):
            with open("config.yaml", "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            web = data.get("web", {})
            if isinstance(web, dict):
                for k in cfg:
                    if k in web:
                        cfg[k] = web[k]
                # 类型转换
                cfg["port"] = int(cfg["port"])
                cfg["debug"] = bool(cfg["debug"])
                cfg["rate_limit_per_day"] = int(cfg["rate_limit_per_day"])
    except Exception:
        pass
    return cfg


_web = _load_web_config()

HOST = _web["host"]
PORT = _web["port"]
DEBUG = _web["debug"]
RATE_LIMIT_PER_IP_PER_DAY = _web["rate_limit_per_day"]
HISTORY_FILE = _web["history_file"]
RATE_LIMIT_FILE = _web["rate_limit_file"]
