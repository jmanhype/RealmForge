# Realm Forge 🏰✨

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



## 🗺️ Roadmap

Realm Forge is actively being developed with the following roadmap:

### Current Status

- ✅ **Basic AFLOW Integration** - Core AFLOW workflows for content generation
- ✅ **Workflow Configuration** - Settings for narrative, world, NPC, and difficulty workflows
- ✅ **Optimization Pipeline** - Framework for workflow improvement based on player feedback
- ✅ **Multi-LLM Support** - Different LLM models for various generation tasks

### Short-term Goals (Q2-Q3 2025)

- 🔄 **Enhanced AFLOW Workflow Optimization** - Improve workflow performance based on user engagement metrics
- 🔄 **Custom AFLOW Operators** - Develop game-specific operators for specialized content generation
- 🔄 **Benchmark Suite** - Create game-specific benchmarks for evaluating content quality
- 🔄 **Performance Optimization** - Reduce latency and improve throughput for real-time game experiences
- 🔄 **OSA Gallery Integration** - Incorporate [Open Source Avatars Gallery](https://github.com/ToxSam/osa-gallery) for ready-to-use 3D characters
- 🔄 **CharacterStudio Integration** - Add [CharacterStudio](https://github.com/ToxSam/CharacterStudio) functionality for custom avatar creation

### Long-term Vision (Q4 2025+)

- 📅 **Expanded Content Types** - Add support for music, sound effects, animations, and more
- 📅 **User-friendly Workflow Editor** - GUI for designing and testing custom workflows
- 📅 **Community Workflow Repository** - Platform for sharing and discovering workflows
- 📅 **Advanced Integration Options** - Support for popular game engines (Unity, Unreal)
- 📅 **Distributed Generation** - Scale content generation across multiple servers
- 📅 **VRM Format Support** - Full implementation of the VRM avatar format for cross-platform compatibility
- 📅 **Advanced Avatar Customization** - Enhanced character creation with point-and-click building and texture editing
- 📅 **Avatar Optimization Pipeline** - Automatic mesh merging and texture atlassing for game-ready characters

### Planned External Integrations

#### OSA Gallery Integration
- Access to 300+ CC0 and open-source 3D avatars
- Support for VRM, FBX, and voxel formats
- VRM Inspector tool for analyzing and validating avatars
- Permanent avatar storage options
- Multilingual support for global accessibility

#### CharacterStudio Integration
- Web-based custom VRM avatar creation interface
- Drag-and-drop 3D files and textures
- Dynamic real-time animations for character previews
- VRM optimization tools (mesh merging, texture atlassing)
- Export capabilities for GLB and VRM formats
- Face auto-culling for performance optimization

## License

MIT License

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [Three.js](https://threejs.org/)
- Uses [AFLOW](https://github.com/metagpt-ai/metagpt/tree/main/metagpt/ext/aflow) for AI workflow optimization
- Developed as part of the MetaGPT AFLOW project
- Integration plans with [OSA Gallery](https://github.com/ToxSam/osa-gallery) and [CharacterStudio](https://github.com/ToxSam/CharacterStudio) for enhanced avatar functionality
