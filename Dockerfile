FROM ubuntu:24.04

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user
RUN groupadd -r lunch && useradd -r -g lunch -s /bin/bash -d /home/lunch lunch \
    && mkdir -p /home/lunch \
    && chown -R lunch:lunch /home/lunch

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app && chown -R lunch:lunch /app /opt

USER lunch
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/lunch/.local/bin:$PATH"
WORKDIR /app

RUN uv venv --python=3.13
COPY --chown=lunch:lunch . .

EXPOSE 8000
CMD ["./scripts/configure_data.sh"]
