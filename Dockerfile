FROM python:3.11-slim

# Install uv for fast dependency management
RUN pip install uv

# Install system deps needed by cryptography (Lark adapter) and aiohttp
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY . .

# Install dependencies needed for Lighthouse (Lark + MCP + cron)
# Use [all] if you need every optional extra; [lark,mcp,cron] is sufficient
# for the Lighthouse gateway deployment.
RUN uv pip install --system -e ".[lark,mcp,cron]"

# Copy config to hermes data directory
RUN mkdir -p /root/.hermes && cp lighthouse-config.yaml /root/.hermes/config.yaml

# Copy Lighthouse skill
RUN mkdir -p /root/.hermes/skills && cp -r skills/lighthouse-analytics /root/.hermes/skills/

# The Lark webhook server listens on LARK_WEBHOOK_PORT (default 9800).
# Set to 4000 so Fly.io can route to it.
ENV LARK_WEBHOOK_PORT=4000

EXPOSE 4000

CMD ["hermes", "gateway"]
