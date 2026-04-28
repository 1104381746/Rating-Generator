import logging
import traceback
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request

from generator.config import Config, load_config
from generator.service import AIShopReviewService

from .history_store import append_history_record, clear_history_file, read_history_records, utc_now_iso
from .settings import HISTORY_FILE

# 从 config.yaml 读取校验边界
_sys = load_config()
MAX_KEYWORD_LENGTH = _sys.get('max_keyword_length') or 100
MIN_WORD_LIMIT = _sys.get('min_word_count') or 10
MAX_WORD_LIMIT = _sys.get('max_word_count') or 1000

bp = Blueprint("web", __name__)


@bp.route("/")
def home():
    return render_template("index.html")


@bp.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.json or {}
        keyword = str(data.get("keyword", "")).strip()
        # 防止参数注入：关键词不能以 - 开头，长度限制
        if not keyword or len(keyword) < 2 or len(keyword) > MAX_KEYWORD_LENGTH:
            return jsonify({"success": False, "error": f"店铺名称长度需在 2-{MAX_KEYWORD_LENGTH} 字符之间"})
        if keyword.startswith("-"):
            return jsonify({"success": False, "error": "无效的店铺名称"})

        try:
            min_w = int(data.get("min_w", 50))
            max_w = int(data.get("max_w", 100))
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "字数范围必须为整数"})
        if not (MIN_WORD_LIMIT <= min_w <= max_w <= MAX_WORD_LIMIT):
            return jsonify({"success": False, "error": f"字数范围无效，需在 {MIN_WORD_LIMIT}-{MAX_WORD_LIMIT} 之间"})

        logger = logging.getLogger("webapp")
        logger.info("生成评价: keyword=%s, range=%d-%d", keyword, min_w, max_w)

        try:
            config_dict = load_config()
            config = Config(**config_dict)
            service = AIShopReviewService(config)
            shop_info, review = service.generate(keyword, (min_w, max_w))
        except Exception as e:
            logger.error(f"生成失败: {e}")
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

        return jsonify({"success": True, "review": review})
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

