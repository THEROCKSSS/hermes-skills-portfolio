# ollama-local

Run large language models locally with Ollama — no API keys, no cloud, no per-token costs.

## What it does

The agent installs Ollama, pulls a model that fits your hardware, and shows you how to use it via the command line or REST API. Models run entirely on your machine — nothing leaves your network. You can use the local model for chat, code generation, embeddings, or as a provider for Hermes Agent.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/ollama-local/SKILL.md
```

## How to use

```
"Set up Ollama with a model that fits my 16GB RAM laptop"
```

The agent:
1. Installs Ollama (or verifies it's installed)
2. Recommends a model based on your RAM (llama3.1:8b for 16GB)
3. Pulls the model: `ollama pull llama3.1:8b`
4. Tests it: `ollama run llama3.1:8b "Hello"`
5. Shows you the REST API endpoint at http://localhost:11434

## Model selection

| Model | RAM needed | Best for |
|---|---|---|
| llama3.2:3b | 4 GB | Fast, simple tasks |
| llama3.1:8b | 8 GB | General purpose |
| qwen2.5-coder:7b | 8 GB | Code generation |
| llama3.1:70b | 64 GB | Complex reasoning |

## Example

```
User: "I want to use a local model for my Hermes agent instead of paying for API calls"

Agent:
  1. Checks RAM: 16 GB available
  2. Recommends: llama3.1:8b (fits in RAM, good quality)
  3. Pulls: ollama pull llama3.1:8b
  4. Configures Hermes:
     hermes config set model.provider custom
     hermes config set model.base_url http://localhost:11434/v1
     hermes config set model.default llama3.1:8b
  5. Returns: "Hermes is now using your local model. No API costs."
```
