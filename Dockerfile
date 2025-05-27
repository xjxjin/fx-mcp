FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
# COPY env.example .env

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV TRANSPORT_MODE=http
ENV HOST=0.0.0.0
ENV PORT=8080

# 暴露HTTP端口
EXPOSE 8080

CMD ["python", "app.py"] 