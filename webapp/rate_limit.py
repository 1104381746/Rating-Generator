import json
import os
import threading
from datetime import date


class RateLimiter:
    def __init__(self, daily_limit: int, storage_file: str):
        self.daily_limit = int(daily_limit)
        self.storage_file = storage_file
        self._lock = threading.Lock()

    def _today_key(self) -> str:
        return date.today().isoformat()

    def _load(self) -> dict:
        if not os.path.exists(self.storage_file):
            return {}
        try:
            with open(self.storage_file, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save(self, data: dict) -> None:
        try:
            tmp = self.storage_file + ".tmp"
            with open(tmp, "w", encoding="utf-8", errors="replace") as f:
                json.dump(data, f, ensure_ascii=False)
            try:
                os.replace(tmp, self.storage_file)
            except OSError:
                # Windows 下 os.replace 可能因权限问题失败，回退到先删后改名
                try:
                    os.remove(self.storage_file)
                except FileNotFoundError:
                    pass
                os.rename(tmp, self.storage_file)
        except Exception:
            pass

    def get_remaining(self, ip: str) -> int:
        if self.daily_limit <= 0:
            return 0
        day = self._today_key()
        with self._lock:
            data = self._load()
            day_map = data.get(day) if isinstance(data.get(day), dict) else {}
            used = int((day_map or {}).get(ip, 0) or 0)
            return max(0, self.daily_limit - used)

    def check_and_consume(self, ip: str) -> tuple[bool, int]:
        if self.daily_limit <= 0:
            return True, 0

        day = self._today_key()
        with self._lock:
            data = self._load()
            if day not in data:
                data = {day: {}}
            if not isinstance(data.get(day), dict):
                data[day] = {}

            day_map: dict = data[day]
            used = int(day_map.get(ip, 0) or 0)
            if used >= self.daily_limit:
                return False, 0

            used += 1
            day_map[ip] = used
            data[day] = day_map
            self._save(data)

            remaining = max(0, self.daily_limit - used)
            return True, remaining

    def refund(self, ip: str) -> None:
        """生成失败时退还一次额度。"""
        if self.daily_limit <= 0:
            return
        day = self._today_key()
        with self._lock:
            data = self._load()
            day_map = data.get(day)
            if not isinstance(day_map, dict):
                return
            used = int(day_map.get(ip, 0) or 0)
            if used > 0:
                day_map[ip] = used - 1
                data[day] = day_map
                self._save(data)


def get_client_ip(flask_request) -> str:
    """
    获取客户端 IP。
    - 默认使用 request.remote_addr
    - 若存在 X-Forwarded-For（反向代理场景），取第一个 IP
    """
    try:
        xff = flask_request.headers.get("X-Forwarded-For", "")
        if xff:
            return xff.split(",")[0].strip() or (flask_request.remote_addr or "unknown")
    except Exception:
        pass
    return flask_request.remote_addr or "unknown"

