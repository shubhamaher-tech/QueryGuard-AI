# ==============================================================================
# QueryGuard AI - Local SLM Bootstrap Script (PowerShell)
# Pulls the configured local code/instruct model into Ollama
# ==============================================================================

param (
    [string]$Model = $(if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "qwen2.5-coder:1.5b" })
)

Write-Host "==> [QueryGuard AI] Pulling local SLM: $Model via Ollama..." -ForegroundColor Cyan

$dockerRunning = docker ps 2>$null | Select-String "queryguard-ollama"
if ($dockerRunning) {
    Write-Host "==> Executing inside Docker container 'queryguard-ollama'..." -ForegroundColor Green
    docker exec -it queryguard-ollama ollama pull $Model
} elseif (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-Host "==> Executing via local Ollama CLI..." -ForegroundColor Green
    ollama pull $Model
} else {
    Write-Host "==> Triggering pull via HTTP API on http://localhost:11434/api/pull..." -ForegroundColor Yellow
    $body = @{ name = $Model } | ConvertTo-Json
    try {
        Invoke-RestMethod -Uri "http://localhost:11434/api/pull" -Method Post -Body $body -ContentType "application/json"
    } catch {
        Write-Warning "Could not reach Ollama at http://localhost:11434. Ensure Ollama container is running."
    }
}

Write-Host "==> [QueryGuard AI] Model $Model bootstrap complete!" -ForegroundColor Green
