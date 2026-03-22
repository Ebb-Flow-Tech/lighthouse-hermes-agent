#!/bin/sh
# Resolve env vars in the hermes config before starting the gateway.
# hermes-agent doesn't interpolate ${VAR} in YAML, so we do it here.

CONFIG="/root/.hermes/config.yaml"

if [ -f "$CONFIG" ] && [ -n "$MCP_AUTH_TOKEN" ]; then
  sed -i "s|\${MCP_AUTH_TOKEN}|${MCP_AUTH_TOKEN}|g" "$CONFIG"
fi

exec hermes gateway
