import logging
import traceback
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request

from generator.config import Config, load_config
from generator.service import AIShopReviewService

from .history_store import append_history_record, clear_history_file, read_history_records, utc_now_iso
from .rate_limit import RateLimiter, get_client_ip
from .settings import HISTORY_FILE, RATE_LIMIT_FILE, RATE_LIMIT_PER_IP_PER_DAY


bp = Blueprint("web", __name__)
rate_limiter = RateLimiter(daily_limit=RATE_LIMIT_PER_IP_PER_DAY, storage_file=RATE_LIMIT_FILE)


@bp.route("/")
def home():
    return render_template("index.html")


@bp.route("/generate", methods=["POST"])
def generate():
    client_ip = "unknown"
    try:
        data = request.json or {}
        keyword = str(data.get("keyword", "")).strip()
        # 防止参数注入：关键词不能以 - 开头，长度限制
        if not keyword or len(keyword) < 2 or len(keyword) > 100:
            return jsonify({"success": False, "error": "店铺名称长度需在 2-100 字符之间"})
        if keyword.startswith("-"):
            return jsonify({"success": False, "error": "无效的店铺名称"})

        try:
            min_w = int(data.get("min_w", 50))
            max_w = int(data.get("max_w", 100))
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "字数范围必须为整数"})
        if not (10 <= min_w <= max_w <= 1000):
            return jsonify({"success": False, "error": f"字数范围无效 ({min_w}-{max_w})"})

        client_ip = get_client_ip(request)
        allowed, remaining = rate_limiter.check_and_consume(client_ip)
        if not allowed:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"今日该 IP 的生成次数已用完（每天最多 {RATE_LIMIT_PER_IP_PER_DAY} 次），请明天再试。",
                        "rate_limit": {
                            "ip": client_ip,
                            "daily_limit": RATE_LIMIT_PER_IP_PER_DAY,
                            "remaining_today": 0,
                        },
                    }
                ),
                429,
            )

        logger = logging.getLogger("webapp")
        logger.info("生成评价: keyword=%s, range=%d-%d", keyword, min_w, max_w)

        try:
            config_dict = load_config()
            config = Config(**config_dict)
            service = AIShopReviewService(config)
            shop_info, review = service.generate(keyword, (min_w, max_w))
        except Exception as e:
            logger.error(f"生成失败: {e}")
            rate_limiter.refund(client_ip)
            return jsonify({"success": False, "error": str(e)})

        # 记录到服务端历史
        append_history_record(
            HISTORY_FILE,
            {
                "ts_utc": utc_now_iso(),
                "keyword": keyword,
                "min_w": min_w,
                "max_w": max_w,
                "review": review,
                "shop_name": shop_info.shop_name,
                "category": shop_info.category,
                "address": getattr(shop_info, "address", "") or "",
            },
        )

        return jsonify(
            {
                "success": True,
                "review": review,
                "rate_limit": {
                    "ip": client_ip,
                    "daily_limit": RATE_LIMIT_PER_IP_PER_DAY,
                    "remaining_today": remaining,
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()})


@bp.route("/history", methods=["GET"])
def history():
    try:
        limit_raw = request.args.get("limit", "50")
        try:
            limit = int(limit_raw)
        except Exception:
            limit = 50

        records = read_history_records(HISTORY_FILE, limit=limit)
        for r in records:
            ts_utc = r.get("ts_utc")
            if ts_utc and isinstance(ts_utc, str):
                try:
                    dt = datetime.fromisoformat(ts_utc.replace("Z", "+00:00"))
                    r["ts_local"] = dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    r["ts_local"] = ts_utc
        return jsonify({"success": True, "records": records})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@bp.route("/history/clear", methods=["POST"])
def history_clear():
    try:
        clear_history_file(HISTORY_FILE)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@bp.route("/rate_limit", methods=["GET"])
def rate_limit_status():
    try:
        client_ip = get_client_ip(request)
        remaining = rate_limiter.get_remaining(client_ip)
        return jsonify(
            {
                "success": True,
                "rate_limit": {
                    "ip": client_ip,
                    "daily_limit": RATE_LIMIT_PER_IP_PER_DAY,
                    "remaining_today": remaining,
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

