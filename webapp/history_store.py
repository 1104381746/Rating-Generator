import json
import os
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_history_record(history_file: str, record: dict) -> None:
    try:
        with open(history_file, "a", encoding="utf-8", errors="replace") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        # 历史写入失败不应影响主流程
        pass


def read_history_records(history_file: str, limit: int = 50) -> list[dict]:
    if limit < 1:
        return []
    if limit > 200:
        limit = 200

    if not os.path.exists(history_file):
        return []

    records: list[dict] = []
    try:
        with open(history_file, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        return []

    return records[-limit:][::-1]


def clear_history_file(history_file: str) -> None:
    if os.path.exists(history_file):
        with open(history_file, "w", encoding="utf-8"):
            pass

