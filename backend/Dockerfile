# Phase 6：EC2 上跑這個 image。跟本機 .venv 用同一個 Python 版本(3.13)。
#
# migration 故意不放進 CMD——一次性的 `alembic upgrade head` 是 deploy.sh 自己另外
# 用這個 image 跑一次 `docker run --rm ... alembic upgrade head`,跟長駐的 app container
# 分開,避免多個 container 同時啟動時搶著跑 migration。
FROM python:3.13-slim

WORKDIR /app

# 先只複製 requirements.txt 裝套件,善用 Docker layer cache——改 app 程式碼不會讓這層重跑
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
