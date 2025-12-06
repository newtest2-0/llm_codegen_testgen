# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CodeForge is a multi-model AI code generation platform that generates code using 8 different AI models in parallel, automatically generates pytest tests, and evaluates code quality using multiple metrics (BLEU scores, test pass rates, AST quality). The system recommends the best solution based on weighted scoring.

## Common Commands

### Development Setup
```bash
# First-time setup (recommended)
python tools/setup.py

# Install dependencies
pip install -r requirements.txt
```

### Starting the Application

**Quick Start (Recommended):**
```bash
# Cross-platform
python start.py

# Windows
start.bat

# Advanced (with environment checks)
python tools/run.py
```

**Manual Start (for debugging):**
```bash
# Terminal 1: Backend (FastAPI)
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend (HTTP server)
cd web
python start_server.py
```

**Access Points:**
- Web UI: http://localhost:8080
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_realtime_status.html

# View demo of code evaluation
python scripts/demo_code_evaluation.py

# Test intelligent generation
python scripts/test_intelligent_generation.py
```

## Architecture Overview

### Three-Layer Architecture

1. **Presentation Layer** ([web/](web/))
   - Single-page application using Tailwind CSS
   - [web/templates/index.html](web/templates/index.html) - Main UI
   - [web/static/js/main.js](web/static/js/main.js) - Frontend logic and API calls
   - LocalStorage for history management

2. **API Layer** ([backend/api/](backend/api/))
   - FastAPI-based REST API
   - Route modules in [backend/api/routes/](backend/api/routes/)
     - [generation.py](backend/api/routes/generation.py) - Code generation endpoints
     - [testing.py](backend/api/routes/testing.py) - Test generation endpoints
     - [evaluation.py](backend/api/routes/evaluation.py) - Code evaluation endpoints
     - [settings.py](backend/api/routes/settings.py) - API key management
     - [system.py](backend/api/routes/system.py) - System status and health

3. **Business Layer** ([backend/core/](backend/core/))
   - Provider system for AI model abstraction
   - Evaluation system for code quality assessment

### Provider System Architecture

The provider system uses a **plugin-based architecture** for AI model integration:

**Key Files:**
- [backend/core/providers/base.py](backend/core/providers/base.py) - Abstract base class defining the provider interface
- [backend/core/providers/manager.py](backend/core/providers/manager.py) - ProviderManager orchestrates all providers
- [backend/core/providers/openai_compatible.py](backend/core/providers/openai_compatible.py) - Handles OpenAI-compatible APIs (OpenAI, DeepSeek, Qwen, Baichuan, ChatGLM, Ollama)
- [backend/core/providers/anthropic.py](backend/core/providers/anthropic.py) - Claude integration
- [backend/core/providers/google.py](backend/core/providers/google.py) - Gemini integration

**How It Works:**
1. [config.json](config.json) defines all providers with their `kind`, `model`, and environment variable names
2. ProviderManager reads config and instantiates providers based on their `kind` field
3. Each provider implements `generate_code()` with automatic retry logic (3 attempts with exponential backoff)
4. API keys are loaded from environment variables (defined in `*_API_KEY` env vars) or [backend/.api_keys.json](backend/.api_keys.json)

**Adding a New Provider:**
1. Create new provider class inheriting from `ProviderBase`
2. Implement `generate_code()` method
3. Add to [manager.py](backend/core/providers/manager.py) `_create_provider()` factory method
4. Add configuration to [config.json](config.json) `providers` array

### Evaluation System Architecture

**Two-Tier Evaluation:**

1. **Basic Evaluation** (always enabled):
   - [backend/core/evaluators/code_quality.py](backend/core/evaluators/code_quality.py) - CodeQualityEvaluator
     - BLEU score calculation (35% weight)
     - AST quality analysis (20% weight)
   - [backend/core/evaluators/test_generator.py](backend/core/evaluators/test_generator.py) - TestGenerator
     - Generates pytest tests for generated code
     - Calculates test pass rate (45% weight)

2. **Enhanced Evaluation** (optional, requires additional dependencies):
   - Enabled if pylint, bandit, radon are installed
   - Additional metrics: functionality, quality, style, security, maintainability
   - Weights configurable in [config.json](config.json) `enhanced_evaluation.weights`

**Scoring Formula:**
```
final_score = (bleu * 0.35) + (test_pass_rate * 0.45) + (ast_quality * 0.20)
```

The system recommends the provider with the highest final score.

### Configuration System

**Three-Level Configuration Priority:**
1. Environment variables (highest priority)
2. [backend/.api_keys.json](backend/.api_keys.json) (runtime API key storage)
3. [config.json](config.json) (system defaults)

**Key Configuration Areas:**
- `providers[]` - AI model provider configurations
- `scoring.weights` - Basic evaluation weights
- `enhanced_evaluation.weights` - Enhanced evaluation weights
- `roles.available_roles` - AI role configurations (affects prompt templates)

### Role-Based Code Generation

The system supports different AI personas via [config.json](config.json) `roles.available_roles`:
- **developer** - Focus on functionality and code quality
- **software_engineer** - Emphasis on architecture and best practices
- **system_analyst** - Deep requirements analysis and design
- **senior_evaluator** - Quality assessment and optimization
- **software_analyst** - Static analysis and improvement suggestions

Each role has a `prompt_template` that's prepended to code generation requests.

## Key Development Patterns

### API Key Management
- Keys can be set via environment variables or through the web UI settings panel
- [backend/core/api_key_storage.py](backend/core/api_key_storage.py) - Handles secure storage in [backend/.api_keys.json](backend/.api_keys.json)
- **Never commit** `.api_keys.json` or `.env` files (already in .gitignore)

### Async Code Generation
The generation endpoint in [backend/api/routes/generation.py](backend/api/routes/generation.py) calls providers asynchronously:
1. Client sends POST to `/api/v1/generate`
2. Backend calls selected providers in parallel (using async/await)
3. Each provider has 3 retry attempts with exponential backoff
4. Results are evaluated and scored
5. Best solution is recommended based on weighted scores

### Error Handling Pattern
All providers use try-except blocks with detailed logging:
- Provider errors are logged but don't crash the app
- Invalid providers are skipped gracefully
- Frontend shows user-friendly error messages

## Important Files

### Configuration
- [config.json](config.json) - Central system configuration
- [.env.example](.env.example) - Environment variable template
- [requirements.txt](requirements.txt) - Python dependencies

### Backend Core
- [backend/app.py](backend/app.py) - FastAPI application entry point with lifespan management
- [backend/core/config.py](backend/core/config.py) - Configuration loader and manager

### Frontend
- [web/templates/index.html](web/templates/index.html) - Complete SPA with Tailwind CSS
- [web/static/js/main.js](web/static/js/main.js) - API integration and UI logic

### Utilities
- [tools/run.py](tools/run.py) - Cross-platform startup with environment validation
- [tools/setup.py](tools/setup.py) - First-time setup and dependency installation
- [scripts/start.py](scripts/start.py) - Original startup script (legacy)

## Debugging

### Enable Debug Logging
```bash
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

### Check Provider Status
```bash
curl http://localhost:8000/health
```

### Common Issues
- **Port already in use**: Check for running instances with `netstat -ano | findstr :8000` (Windows) or `lsof -i :8000` (Linux/Mac)
- **Missing API keys**: Verify environment variables or [backend/.api_keys.json](backend/.api_keys.json)
- **Provider failures**: Check logs for API key issues, network problems, or quota limits
- **Enhanced evaluation disabled**: Install optional dependencies (`pip install pylint bandit radon`)

## Code Style

- Python: PEP 8 compliant
- Async/await for I/O operations
- Type hints used throughout core modules
- Logging instead of print statements
- Docstrings for all public functions and classes
