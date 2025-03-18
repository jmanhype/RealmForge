# Realm Forge

A procedurally generated RPG with AI-powered narrative, world building, and NPCs using AFLOW and Three.js.

## Overview

Realm Forge uses advanced AI workflows to create dynamic game experiences:

- **Evolving Narrative**: Stories that adapt based on player choices and history
- **Dynamic World Generation**: Procedurally created landscapes, dungeons, towns, and quests
- **Intelligent NPCs**: Characters with personality, memory, and evolving relationships
- **Adaptive Difficulty**: Game challenges that adjust to player skill level
- **Engagement Optimization**: AI systems that learn from player engagement metrics

## Architecture

The system integrates AFLOW (Automated Flow) with Three.js through a RESTful API:

- **AFLOW Workflows**: Specialized AI workflows for narrative, world content, NPCs, and difficulty
- **REST API**: FastAPI-based endpoints for Three.js integration
- **Optimization Pipeline**: Automatic workflow improvements based on player metrics
- **Asynchronous Generation**: Non-blocking content creation to maintain performance

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -e .
   ```
3. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```
4. Run the API server:
   ```bash
   python src/api/main.py
   ```

## API Documentation

API documentation is available at `/docs` when the server is running.

## Development

For development setup:
```bash
pip install -e ".[dev]"
pre-commit install
```

Run tests:
```bash
pytest
```

## License

MIT License
