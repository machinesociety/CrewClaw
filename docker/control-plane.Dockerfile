FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend backend

EXPOSE 8000

# TODO: 如需生产环境调优，可在此增加非 root 用户等设置。
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

