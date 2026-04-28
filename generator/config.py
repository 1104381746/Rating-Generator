import os
from dataclasses import dataclass
from typing import Dict

import yaml


def load_config(config_path: str = "config.yaml") -> Dict:
    """从YAML配置文件加载配置"""
    try:
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}

        api_config = config.get('api', {})
        amap_config = config.get('amap', {})
        system_config = config.get('system', {})
        logging_config = config.get('logging', {})

        return {
            'api_key': api_config.get('api_key'),
            'api_base_url': api_config.get('base_url', 'https://api.deepseek.com'),
            'model_name': api_config.get('model_name', 'deepseek-v4-flash'),
            'amap_api_key': amap_config.get('api_key'),
            'amap_city': amap_config.get('city'),
            'max_keyword_length': system_config.get('max_keyword_length', 100),
            'min_word_count': system_config.get('min_word_count', 10),
            'max_word_count': system_config.get('max_word_count', 1000),
            'max_retry_attempts': system_config.get('max_retry_attempts', 3),
            'log_level': logging_config.get('level', 'INFO'),
            'log_to_file': logging_config.get('to_file', False),
            'log_file': logging_config.get('log_file', 'app.log')
        }
    except yaml.YAMLError as e:
        raise ValueError(f"配置文件格式错误: {e}")
    except Exception as e:
        raise ValueError(f"加载配置文件失败: {e}")


@dataclass
class Config:
    """配置类 - 从YAML文件加载"""
    api_key: str
    api_base_url: str = "https://api.deepseek.com"
    model_name: str = "deepseek-v4-flash"
    amap_api_key: str | None = None
    amap_city: str | None = None
    max_keyword_length: int = 100
    min_word_count: int = 10
    max_word_count: int = 1000
    max_retry_attempts: int = 3
    log_level: str = "INFO"
    log_to_file: bool = False
    log_file: str = "app.log"

    def __post_init__(self):
        self.validate()

    def validate(self):
        if not self.api_key:
            raise ValueError(
                "错误：未找到API密钥！\n"
                "请编辑 config.yaml 文件，在 api.api_key 字段中填入你的 API 密钥"
            )
        if self.max_keyword_length < 1:
            raise ValueError("max_keyword_length 必须大于0")
        if self.min_word_count < 1:
            raise ValueError("min_word_count 必须大于0")
        if self.max_word_count < 1:
            raise ValueError("max_word_count 必须大于0")
        if self.min_word_count > self.max_word_count:
            raise ValueError("min_word_count 不能大于 max_word_count")
        if self.max_retry_attempts < 1:
            raise ValueError("max_retry_attempts 必须大于0")

        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level not in valid_levels:
            raise ValueError(f"日志级别无效: {self.log_level}，必须是: {', '.join(valid_levels)}")
