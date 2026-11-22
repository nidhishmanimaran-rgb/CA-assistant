FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/app/data REQUIRE_PASSWORD=true
WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt && useradd --create-home --uid 10001 appuser
COPY --chown=appuser:appuser app.py ./
COPY --chown=appuser:appuser backend ./backend
COPY --chown=appuser:appuser config ./config
COPY --chown=appuser:appuser ui ./ui
COPY --chown=appuser:appuser .streamlit/config.toml ./.streamlit/config.toml
RUN mkdir -p /app/data && chown appuser:appuser /app/data
USER appuser
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)"
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
