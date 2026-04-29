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
    gosu \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app && chown -R lunch:lunch /app /opt

USER lunch
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/lunch/.local/bin:$PATH"
WORKDIR /app

RUN uv venv --python=3.13
COPY --chown=lunch:lunch . .

# Switch back to root so the entrypoint can fix /data ownership before
# dropping privileges to the lunch user at runtime.
USER root

EXPOSE 8000
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["./scripts/configure_data.sh"]
