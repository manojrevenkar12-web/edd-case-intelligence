FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 10001 edd
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
COPY config ./config
COPY experiments ./experiments
RUN pip install --no-cache-dir -e ".[claude]"
USER edd
EXPOSE 8000
ENV EDD_MODEL=claude
CMD ["uvicorn", "edd.api:app", "--host", "0.0.0.0", "--port", "8000"]
