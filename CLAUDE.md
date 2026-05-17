# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CodeForge is a multi-model AI code generation platform that generates code using multiple AI models in parallel, automatically generates pytest tests, and evaluates code quality using multiple metrics (BLEU scores, test pass rates, AST quality). The system recommends the best solution based on weighted scoring.

## Common Commands

### Development Setup
```bash
# First-time setup (recommended)
python tools/setup.py

# Install dependencies
pip install -r requirements.txt
```

### Starting the Application

```bash
# Cross-platform quick start
python start.py

# Manual start for debugging:
# Terminal 1: Backend
cd backend && uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd web && python start_server.py
```

Access points: Web UI at http://localhost:8080, API docs at http://localhost:8000/docs

### Testing
```bash
# Run Python tests
pytest

# Demo scripts (not pytest — run directly)
python scripts/demo_code_evaluation.py
python scripts/test_intelligent_generation.py
```

Note: `tests/test_realtime_status.html` and `tests/test_roles.html` are browser-based test pages, not pytest-runnable files.

## Architecture Overview

### Three-Layer Architecture

1. **Presentation Layer** ([web/](web/)) — SPA using Tailwind CSS, LocalStorage for history
2. **API Layer** ([backend/api/routes/](backend/api/routes/)) — FastAPI routes for generation, testing, evaluation, settings, system status
3. **Business Layer** ([backend/core/](backend/core/)) — Provider system and evaluation system

### Provider System

Plugin-based architecture for AI model integration:

- [backend/core/providers/base.py](backend/core/providers/base.py) — `ProviderBase` abstract class; all providers must inherit from this and implement async `generate_code()`; includes retry logic (3 attempts, exponential backoff)
- [backend/core/providers/manager.py](backend/core/providers/manager.py) — `ProviderManager` reads `config.json`, instantiates providers via `_create_provider()` factory based on `kind` field
- [backend/core/providers/openai_compatible.py](backend/core/providers/openai_compatible.py) — handles OpenAI-compatible APIs (OpenAI, DeepSeek, Qwen, Baichuan, ChatGLM)
- [backend/core/providers/anthropic.py](backend/core/providers/anthropic.py) — Claude integration
- [backend/core/providers/google.py](backend/core/providers/google.py) — Gemini integration
- [backend/core/providers/ollama_provider.py](backend/core/providers/ollama_provider.py) — Ollama local model integration (in progress; currently does not inherit `ProviderBase` or implement the required async interface — not yet wired into `manager.py`)

**Adding a New Provider:**
1. Create provider class inheriting from `ProviderBase`, implement async `generate_code()`
2. Add a `kind` handler in `manager.py` `_create_provider()`
3. Add entry to `config.json` `providers[]` with `name`, `kind`, `model`, and env var fields

**Config format for a provider entry:**
```json
{
  "name": "my_provider",
  "kind": "my_kind",
  "model": "model-name",
  "api_key_env": "MY_PROVIDER_API_KEY"
}
```

### Evaluation System

**Two-Tier Evaluation:**

1. **Basic** (always enabled) — BLEU score (35%), test pass rate (45%), AST quality (20%)
   - [backend/core/evaluators/code_quality.py](backend/core/evaluators/code_quality.py) — `ComprehensiveCodeEvaluator` with complexity, style, and security analyzers
   - [backend/core/evaluators/test_generator.py](backend/core/evaluators/test_generator.py) — `CodeAnalyzer` extracts structure; `TestGenerator` generates and runs pytest tests

2. **Enhanced** (optional) — requires `pylint`, `bandit`, `radon`; adds functionality, quality, style, security, maintainability metrics with configurable weights in `config.json`

**Scoring formula:**
```
final_score = (bleu * 0.35) + (test_pass_rate * 0.45) + (ast_quality * 0.20)
```

### Configuration System

Priority order (highest first):
1. Environment variables
2. [backend/.api_keys.json](backend/.api_keys.json) — runtime API key storage (do not commit)
3. [config.json](config.json) — system defaults: providers, scoring weights, enhanced evaluation weights, role definitions

### Role-Based Code Generation

Five roles defined in `config.json` `roles.available_roles`: `developer`, `software_engineer`, `system_analyst`, `senior_evaluator`, `software_analyst`. Each has a `prompt_template` prepended to generation requests.

## Key Development Patterns

### Async Code Generation Flow
`POST /api/v1/generate` → parallel provider calls (async/await) → evaluation + scoring → best result returned. Provider errors are caught and logged; failing providers are skipped without crashing.

### API Key Management
Keys are set via environment variables or the web UI settings panel. [backend/core/api_key_storage.py](backend/core/api_key_storage.py) handles storage in `backend/.api_keys.json`.

## Debugging

```bash
# Debug logging
cd backend && uvicorn app:app --host 0.0.0.0 --port 8000 --reload --log-level debug

# Health check
curl http://localhost:8000/health
```

Common issues:
- **Port in use**: `lsof -i :8000` (Mac/Linux) or `netstat -ano | findstr :8000` (Windows)
- **Provider failures**: check logs for API key issues or quota limits
- **Enhanced evaluation disabled**: `pip install pylint bandit radon`
