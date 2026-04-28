# Rating Generator — AI 探店评价生成器

基于大语言模型的探店评价生成工具。输入店铺名称，自动生成口语化、真实感强的消费评价，适用于大众点评平台风格的种草文案。

---

## ✨ 功能特性

- **一键生成** — 输入店名，选择字数范围，即刻生成口语化评价。
- **高德地图 POI 集成** — 可选接入高德地图 API，自动补充店铺真实信息（名称、地址、类型等）。
- **单次 API 调用** — 店铺搜索与评价生成合并为一次调用，响应更快、成本更低。
- **历史记录** — 浏览器端 + 服务端双存储，支持复制和清空。
- **频率限制** — 基于 IP 的日调用次数控制，防止滥用。
- **多方式部署** — 支持本地 Python 环境、Docker 及 Docker Compose 快速部署。

---

## 🚀 部署指南

### 1. 本地开发部署

**环境要求：** Python 3.9+

```bash
# 克隆仓库
git clone https://github.com/<your-username>/rating-generator.git
cd rating-generator

# 创建并激活虚拟环境 (可选但推荐)
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置文件
cp config.yaml.example config.yaml
# 编辑 config.yaml，填入您的 API Key 及其他配置

# 启动服务
python app.py
```

访问 `http://localhost:5200` 即可使用。

---

### 2. Docker 部署

**环境要求：** 已安装 Docker

```bash
# 构建镜像
docker build -t rating-generator .

# 准备配置文件 (确保本地已有 config.yaml)
# 运行容器
docker run -d \
  --name rating-generator \
  -p 5200:5200 \
  -v ${PWD}/config.yaml:/app/config.yaml:ro \
  -v ${PWD}/logs:/app/logs \
  rating-generator
```

---

### 3. Docker Compose 部署 (推荐)

**环境要求：** 已安装 Docker 和 Docker Compose

```bash
# 1. 复制配置文件并修改
cp config.yaml.example config.yaml

# 2. 启动服务
docker-compose up -d
```

**停止服务：**
```bash
docker-compose down
```

---

## ⚙️ 配置说明

配置文件 `config.yaml` 详细参数如下：

```yaml
# API 配置 (必填)
api:
  api_key: "sk-xxx"                    # API 密钥
  base_url: "https://api.deepseek.com" # 或其他兼容 OpenAI 协议的 API 地址
  model_name: "deepseek-v4-flash"

# 系统参数
system:
  max_keyword_length: 100              # 店名最大长度
  min_word_count: 10                   # 评价最小字数
  max_word_count: 1000                 # 评价最大字数
  max_retry_attempts: 1                # API 调用失败重试次数

# 日志
logging:
  level: "INFO"                        # DEBUG / INFO / WARNING / ERROR
  to_file: true
  log_file: "app.log"

# 高德地图 POI 搜索 (可选，留空则由 AI 模拟店铺信息)
amap:
  api_key: ""                          # 高德 Web 服务 API Key
  city: ""                             # 搜索限定城市，如 "深圳"

# Web 服务
web:
  host: "0.0.0.0"                      # 容器部署建议使用 0.0.0.0
  port: 5200
  debug: false                         # 生产环境务必设为 false
  rate_limit_per_day: 10               # 每 IP 每天最大调用次数
  history_file: "history.jsonl"
  rate_limit_file: "rate_limits.json"
```

---

## 📂 项目结构

```text
├── app.py                  # Web 服务入口
├── config.yaml             # 统一配置文件 (不纳入版本控制)
├── config.yaml.example     # 配置文件示例
├── requirements.txt        # Python 依赖
├── Dockerfile              # Docker 构建文件
├── docker-compose.yml      # Docker Compose 配置文件
├── generator/              # 核心生成逻辑
│   ├── config.py           # 配置加载与校验
│   ├── models.py           # 数据模型 (Pydantic)
│   └── service.py          # AI 调用与逻辑处理
├── webapp/                 # Flask Web 层
│   ├── routes.py           # 路由定义
│   ├── rate_limit.py       # IP 频率限制
│   └── history_store.py    # 历史记录存取
├── templates/              # 前端页面模板
├── static/                 # 静态资源 (CSS/JS)
└── logs/                   # 日志持久化目录
```

---

## 🛠️ 技术栈

| 层次 | 技术 |
|------|------|
| 后端框架 | Flask 3.x (工厂模式 + Blueprint) |
| AI 客户端 | OpenAI Python SDK |
| 数据校验 | Pydantic v2 |
| 配置管理 | PyYAML |
| 前端 | 原生 JavaScript (无框架依赖) |
| 部署 | Docker / Docker Compose |

---

## 📄 开源协议

本项目采用 [MIT](LICENSE) 协议。
