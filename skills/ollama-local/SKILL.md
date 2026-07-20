---
name: ollama-local
description: "Run local LLMs with Ollama — agent + this skill = user gets a private, offline LLM running on their machine."
version: 1.0.0
---

# ollama-local

Set up and use Ollama for running large language models locally. Ollama runs models on your machine — no API keys, no cloud, no per-token costs. The agent installs Ollama, pulls models, and shows you how to use them via the REST API or command line.

## When to Use

- The user wants to run an LLM locally without paying for API access.
- The user wants privacy — no data leaves their machine.
- The user wants to use a local model with their agent or application.
- The user says "set up Ollama", "run a local LLM", or "I want offline AI".

## Installation

### Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### macOS

```bash
# Via Homebrew
brew install ollama

# Or download from https://ollama.com/download
```

### Windows

Download from https://ollama.com/download and run the installer. Ollama runs as a background service on Windows.

### Verify installation

```bash
ollama --version
# ollama version is 0.x.x
```

## Model Management

### Pull a model

```bash
# Small, fast model (good for testing)
ollama pull llama3.2:3b

# Medium model (good balance of speed and quality)
ollama pull llama3.1:8b

# Large model (best quality, needs 16GB+ RAM)
ollama pull llama3.1:70b

# Coding-focused model
ollama pull qwen2.5-coder:7b

# Embedding model
ollama pull nomic-embed-text
```

### List installed models

```bash
ollama list
```

### Run a model (interactive chat)

```bash
ollama run llama3.1:8b
>>> Tell me about quantum computing
```

### Remove a model

```bash
ollama rm llama3.2:3b
```

## API Usage

Ollama exposes a REST API at `http://localhost:11434`:

### Generate a response

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Explain recursion in one sentence.",
  "stream": false
}'
```

### Chat (multi-turn)

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.1:8b",
  "messages": [
    {"role": "user", "content": "What is 2+2?"},
    {"role": "assistant", "content": "4"},
    {"role": "user", "content": "What about 3+5?"}
  ],
  "stream": false
}'
```

### Generate embeddings

```bash
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "The quick brown fox jumps over the lazy dog."
}'
```

### Python client

```python
import requests

response = requests.post('http://localhost:11434/api/generate', json={
    'model': 'llama3.1:8b',
    'prompt': 'Write a haiku about the ocean.',
    'stream': False
})
print(response.json()['response'])
```

### Streaming responses

```python
import requests

response = requests.post('http://localhost:11434/api/generate', json={
    'model': 'llama3.1:8b',
    'prompt': 'Tell me a story.',
    'stream': True
}, stream=True)

for line in response.iter_lines():
    if line:
        import json
        chunk = json.loads(line)
        print(chunk.get('response', ''), end='', flush=True)
```

## Integration with Hermes

Configure Hermes to use the local Ollama instance as a provider:

```bash
# Set Ollama as a custom provider
hermes config set model.provider custom
hermes config set model.base_url http://localhost:11434/v1
hermes config set model.api_key ollama  # Ollama doesn't require a real key
hermes config set model.default llama3.1:8b
```

Or use Ollama for specific tasks (like auxiliary/compression) while keeping a cloud model for main reasoning:

```bash
hermes config set auxiliary.compression.provider custom
hermes config set auxiliary.compression.base_url http://localhost:11434/v1
hermes config set auxiliary.compression.model llama3.2:3b
```

## Model Selection Guide

| Model | Size | RAM needed | Best for |
|---|---|---|---|
| `llama3.2:3b` | 2 GB | 4 GB | Fast responses, simple tasks |
| `llama3.1:8b` | 5 GB | 8 GB | General purpose, good balance |
| `qwen2.5-coder:7b` | 5 GB | 8 GB | Code generation, debugging |
| `llama3.1:70b` | 40 GB | 64 GB | High quality, complex reasoning |
| `nomic-embed-text` | 0.3 GB | 1 GB | Embeddings for RAG/search |

## Performance Tips

- **Use GPU if available** — Ollama auto-detects NVIDIA/AMD GPUs and Apple Silicon. GPU inference is 5-10x faster than CPU.
- **Match model size to your RAM** — A model that doesn't fit in RAM will spill to disk and become extremely slow. Check `ollama ps` to see if the model is fully in memory.
- **Use smaller models for simple tasks** — Don't use a 70B model for a one-sentence answer. Use 3B or 8B for quick tasks.
- **Keep models loaded** — Ollama keeps models in memory for 5 minutes after last use by default. Increase this with `OLLAMA_KEEP_ALIVE` env var if you're making frequent requests.
- **Quantization** — Ollama uses 4-bit quantization by default, which reduces memory usage by ~70% with minimal quality loss. No configuration needed.

## Pitfalls

- **Out of memory** — If the model is larger than your available RAM, Ollama will try to use disk swap and performance will be unusable. Use a smaller model or add RAM.
- **First run is slow** — The first time you pull a model, it downloads the full model file. Subsequent runs are instant (model is cached).
- **Port conflicts** — Ollama uses port 11434 by default. If another service uses it, set `OLLAMA_HOST=0.0.0.0:11435` before starting.
- **No GPU detected** — On Linux, ensure NVIDIA drivers and CUDA toolkit are installed. On Windows, ensure the NVIDIA driver is up to date. On Mac, Apple Silicon is auto-detected.
- **Context length limits** — Local models have smaller context windows than cloud models. Llama 3.1 supports 128k tokens, but running at full context requires massive RAM. Keep prompts under 8k tokens for 8B models.
- **Concurrent requests** — Ollama processes requests sequentially by default. If you need concurrency, set `OLLAMA_NUM_PARALLEL` env var.
