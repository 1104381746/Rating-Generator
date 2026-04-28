# 使用Python 3.11 slim镜像作为基础
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 1. 复制依赖文件并安装依赖 (利用缓存层)
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 2. 复制应用代码 (当代码改变时，上面的依赖安装层会被缓存)
COPY app.py .
COPY generator ./generator
COPY webapp ./webapp
COPY templates ./templates
COPY static ./static

# 创建日志目录
RUN mkdir -p /app/logs

# 暴露端口
EXPOSE 5200

# 设置启动命令
CMD ["python", "app.py"]
