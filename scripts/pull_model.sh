#!/usr/bin/env bash
# ==============================================================================
# QueryGuard AI - Local SLM Bootstrap Script
# Pulls the configured local code/instruct model into Ollama
# ==============================================================================

set -euo pipefail

MODEL="${1:-${OLLAMA_MODEL:-qwen2.5-coder:1.5b}}"

echo "==> [QueryGuard AI] Pulling local SLM: ${MODEL} via Ollama..."
if command -v docker &> /dev/null && docker ps | grep -q "queryguard-ollama"; then
    echo "==> Executing inside Docker container 'queryguard-ollama'..."
    docker exec -it queryguard-ollama ollama pull "${MODEL}"
elif command -v ollama &> /dev/null; then
    echo "==> Executing via local Ollama CLI..."
    ollama pull "${MODEL}"
else
    echo "==> Using curl to trigger pull on http://localhost:11434/api/pull..."
    curl -X POST http://localhost:11434/api/pull -d "{\"name\": \"${MODEL}\"}"
fi

echo "==> [QueryGuard AI] Model ${MODEL} bootstrap complete!"
