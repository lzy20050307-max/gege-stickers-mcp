FROM python:3.12-slim
WORKDIR /app
COPY server.py stickers_core.py ./
ENV PORT=8000 PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "server.py"]
