FROM python:3.12-slim
WORKDIR /app
COPY app.py seed.py seed.json ./
COPY static ./static
ENV HOST=0.0.0.0 PORT=8770 PORTAL_DB=/data/portal.db
EXPOSE 8770
VOLUME ["/data"]
CMD ["python3", "app.py"]
