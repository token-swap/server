# TokenHub Server

A Python aiohttp WebSocket server that coordinates token exchanges between LLM API providers.

## Overview

The server matches clients offering and requesting specific model access. It calculates exchange rates based on real-world input and output pricing for 20 models from OpenAI, Anthropic, and Gemini.

### Features
- Peer matching based on model availability and demand.
- Real-time exchange rate calculation from `pricing.py`.
- Usage report relaying between connected peers.
- Support for advanced token budgeting (separate input/output rates).

## Requirements

- Python 3.11+
- aiohttp >= 3.11.0

## Installation

```bash
pip install -e .
```

Test: `python -m pytest -q`

## Running the Server

Start the server using the entry point:
```bash
tokenhub-server
```

Or run the module directly:
```bash
python -m server.main
```

### Docker

Build and run via Docker:
```bash
docker build -t tokenhub-server .
docker run -p 8080:8080 tokenhub-server
```

## Configuration

Configure the server using environment variables:

- `HOST`: Bind address (default: `0.0.0.0`)
- `PORT`: Listen port (default: `8080`)

## How the Exchange Works

The server facilitates "fair swap" matching. If Alice offers OpenAI and wants Anthropic, and Bob offers Anthropic and wants OpenAI, the server pairs them. It calculates a metered budget based on the relative cost of the models. For simple budgets, it uses total token counts. For advanced budgets, it uses specific input and output pricing.
