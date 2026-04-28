import json
import logging
import os
import urllib.parse
import urllib.request

from openai import OpenAI, OpenAIError
from pydantic import ValidationError

from .config import Config
from .models import ReviewError, ShopInfo


class AIShopReviewService:
    def __init__(self, config: Config):
        self.config = config
        self.client = OpenAI(api_key=self.config.api_key, base_url=self.config.api_base_url)
        self.logger = logging.getLogger("generator")
        self._setup_logging()

    def _setup_logging(self):
        """仅配置 generator logger，避免影响全局 logging 状态。"""
        logger = logging.getLogger("generator")
        logger.setLevel(getattr(logging, self.config.log_level))
        if self.config.log_to_file and not logger.handlers:
            os.makedirs(os.path.dirname(self.config.log_file) or '.', exist_ok=True)
            fh = logging.FileHandler(self.config.log_file, encoding='utf-8', errors='replace')
            fh.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
            ))
            logger.addHandler(fh)

    def _clean_json_response(self, content):
        content = content.strip()
        # 移除 Markdown 代码块标记（支持 ```json, ``` 等）
        if content.startswith("```"):
            first_line_end = content.find("\n")
            if first_line_end != -1:
                content = content[first_line_end + 1:]
            else:
                content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()

    def _validate_shop_info(self, data):
        try:
            return ShopInfo(**data)
        except ValidationError as e:
            self.logger.error(f"数据验证失败: {e}")
            raise ReviewError(f"店铺数据格式无效: {e}")

    def _amap_poi_text_search(self, keyword: str) -> dict | None:
        if not self.config.amap_api_key:
            self.logger.debug("未配置高德 Key，跳过 POI 搜索")
            return None

        params = {
            "key": self.config.amap_api_key,
            "keywords": keyword,
            "extensions": "base",
            "offset": "1",
            "page": "1",
        }
        if self.config.amap_city:
            params["city"] = self.config.amap_city
            params["citylimit"] = "true"

        url = "https://restapi.amap.com/v3/place/text?" + urllib.parse.urlencode(params)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Rating-Generator/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
            if str(data.get("status")) != "1":
                self.logger.warning(f"高德 POI 搜索失败: {data.get('info')}")
                return None
            pois = data.get("pois") or []
            if not pois:
                self.logger.debug("高德 POI 搜索无结果")
                return None
            self.logger.info("高德 POI 命中: %s", pois[0].get('name'))
            return pois[0]
        except Exception as e:
            self.logger.warning(f"高德 POI 搜索异常: {e}")
            return None

    def generate(self, keyword: str, word_range: tuple[int, int]):
        """单次 API 调用完成店铺搜索和评价生成。"""
        min_words, max_words = word_range

        poi = self._amap_poi_text_search(keyword.strip())
        poi_hint = ""
        poi_instruction = ""
        if poi:
            poi_hint = f"""
以下是从高德地图 POI 搜索得到的结果：
- 店名: {poi.get('name')}
- 类型: {poi.get('type')}
- 地址: {poi.get('address')}
- 行政区: {poi.get('pname', '')}{poi.get('cityname', '')}{poi.get('adname', '')}
- 商圈: {poi.get('business_area')}
"""
            poi_instruction = """
重要：上述 POI 信息是真实地图数据，店名、类型、地址必须严格采用 POI 的值，不得自行更改或编造。
- shop_name 必须等于 POI 店名
- category 必须等于 POI 类型（不要自己猜一个不同的类型）
- address 必须等于 POI 地址
如果 POI 类型看起来不像是餐饮/消费场所（如"汽车养护"），按其实际类型输出即可，评价内容也相应调整（写养护体验而非菜品口味）。
"""
        else:
            poi_instruction = """
未找到 POI 数据，请根据店铺名称常识推断类型。注意：不是所有店铺都是餐厅——从店名判断是否存在"餐饮/奶茶/火锅/烧烤"等食物关键词，如果没有，则可能是零售、服务等非餐饮业态。
"""

        prompt = f"""
你是一个专业的探店数据助手兼大众点评用户。请完成两项任务：

【任务1】查询名为"{keyword}"的店铺信息，以 JSON 格式输出：
- shop_name: 店铺全称
- category: 菜系或店铺类型
- avg_price: 人均消费（如"35元"）
- signature_dishes: 3-5个招牌菜/特色产品（列表，非餐饮类则为特色服务项目）
- environment: 环境特点
- service_style: 服务风格
- location_vibe: 位置氛围
- address: 地址（如已知）
{poi_hint}
{poi_instruction}
若无法确定某字段，基于该类型店铺典型特征编造逼真数据。

【任务2】基于以上店铺信息，写一篇口语化消费评价。

硬性字数要求：评价正文字数必须严格控制在 {min_words}-{max_words} 字之间（含标点，不含空格）。
请在完成后自查字数，不足 {min_words} 字或超过 {max_words} 字均为不合格，必须删减或补充到范围内。

写作风格要求——必须以真实大众点评用户的即兴口吻来写，消除 AI 感：
1. 句式多变：长短句混搭，偶尔用断句、倒装、省略，自然停顿。不要每句话都完整工整。
2. 真实的逻辑跳跃：不要写"总-分-总"或"先环境-再菜品-后服务"的结构化评论。想到哪写到哪，可以突然从一个菜跳到另一个话题，中间加点个人碎碎念。
3. 有微妙的不满或吐槽点也没关系（比如"等得有点久""价格小贵"），真人不会只夸不挑。
4. 适当使用 Emoji，但不要每句都加。😂🤤👍✨ 之类穿插在句子里，不是装饰在开头。
5. 不要用"总的来说""综上所述""个人认为"等书面语开头/结尾。

内容要求：必须提到具体招牌菜和环境感受。直接输出评价内容，不要任何标题或前缀。

请严格按以下格式输出（不要包含其他内容）：
---SHOP_INFO---
{{"shop_name": "...", "category": "...", ...}}
---REVIEW---
评价正文内容...
"""

        retry_count = 0
        last_error = None

        while retry_count < self.config.max_retry_attempts:
            try:
                response = self.client.chat.completions.create(
                    model=self.config.model_name,
                    messages=[
                        {"role": "system", "content": "你是一个精准的数据提取助手兼种草文案达人。"},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                )

                content = response.choices[0].message.content
                if not content:
                    raise ReviewError("API 返回空内容")

                shop_json_str = ""
                review_text = ""

                if "---SHOP_INFO---" in content and "---REVIEW---" in content:
                    parts = content.split("---REVIEW---", 1)
                    shop_part = parts[0].split("---SHOP_INFO---", 1)[1].strip()
                    shop_json_str = self._clean_json_response(shop_part)
                    review_text = parts[1].strip()
                else:
                    self.logger.warning("未找到标准分隔标记，尝试容错解析")

                if not shop_json_str or not review_text:
                    raise ReviewError("解析响应格式失败")

                data = json.loads(shop_json_str)
                shop_info = self._validate_shop_info(data)
                review = review_text

                self.logger.info("生成成功: %s, %d字", shop_info.shop_name, len(review))
                return shop_info, review

            except (json.JSONDecodeError, ValidationError) as e:
                last_error = e
                self.logger.warning(f"解析失败 (尝试 {retry_count + 1}/{self.config.max_retry_attempts}): {e}")
                retry_count += 1
            except OpenAIError as e:
                last_error = e
                self.logger.error(f"API 调用失败 (尝试 {retry_count + 1}/{self.config.max_retry_attempts}): {e}")
                retry_count += 1
            except ReviewError:
                raise

        raise ReviewError(f"生成失败，已重试 {self.config.max_retry_attempts} 次: {last_error}")
