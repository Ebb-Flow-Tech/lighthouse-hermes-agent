FROM python:3.11-slim

# Install uv for fast dependency management
RUN pip install uv

# Install system deps:
#   build-essential, libffi-dev — needed by cryptography (Lark adapter) and aiohttp
#   psmisc — provides fuser, used by WhatsApp adapter to kill orphaned bridge processes
#   ca-certificates, curl, gnupg — needed for NodeSource APT repo setup
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    psmisc \
    ca-certificates \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20 LTS (required for WhatsApp Baileys bridge)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY . .

# Install WhatsApp bridge npm dependencies at build time
# (The adapter has a runtime fallback, but pre-installing is faster and deterministic)
RUN cd scripts/whatsapp-bridge && npm install --production && cd ../..

# Install dependencies needed for Lighthouse (Lark + MCP + cron + aiohttp for WhatsApp)
RUN uv pip install --system -e ".[lark,mcp,cron]" aiohttp>=3.9.0

# Copy config to hermes data directory
RUN mkdir -p /root/.hermes && cp lighthouse-config.yaml /root/.hermes/config.yaml

# Copy Lighthouse skill
RUN mkdir -p /root/.hermes/skills && cp -r skills/lighthouse-analytics /root/.hermes/skills/

# The Lark webhook server listens on LARK_WEBHOOK_PORT (default 9800).
# Set to 4000 so Fly.io can route to it.
ENV LARK_WEBHOOK_PORT=4000

EXPOSE 4000

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
