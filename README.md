# RealmForge 🏰✨

RealmForge is an advanced AI-driven procedural content generation system for game development. It leverages artificial intelligence to dynamically create immersive game world elements including detailed 3D scenes, characters, compelling narratives, and interactive NPCs with unique personalities.

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688.svg)](https://fastapi.tiangolo.com/)
[![Three.js](https://img.shields.io/badge/Three.js-Latest-black.svg)](https://threejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## ✨ Features

- **🌳 Scene Generation** - Create rich, dynamic 3D environments with various settings (forests, towns, caves, dungeons)
- **👤 Character Generation** - Design detailed character models with customizable attributes and appearances
- **🤖 NPC Generation** - Develop non-player characters with unique personalities, behaviors, and backstories
- **🎮 Quest System** - Generate engaging quests with objectives, narratives, and rewards
- **🔄 Procedural Content** - Dynamically create game content that's different with each generation
- **🖥️ 3D Visualization** - View and interact with generated content in real-time using Three.js
- **🔌 RESTful API** - Comprehensive, well-documented API for seamless integration into game development pipelines

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- FastAPI
- Three.js (for visualization)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/jmanhype/RealmForge.git
cd RealmForge
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (copy from example file):
```bash
cp .env.example .env
# Edit .env file to add your API keys and configuration
```

### Running the Server

```bash
python -m src.api.main
```

The server will start on http://localhost:8001

## 📚 API Documentation

Once the server is running, you can access the interactive API documentation at:
```
http://localhost:8001/docs
```

## 🎮 Visualization

The 3D visualization frontend is available at:
```
http://localhost:8001/visualizer
```

## 🧪 Testing

To run the test suite:
```bash
pytest
```

## 🛠️ Development

RealmForge follows a modular architecture:

- `src/api` - FastAPI endpoints and server configuration
- `src/models` - Data models and schemas
- `src/services` - Business logic and AI integration
- `src/utils` - Helper functions and utilities
- `static` - Frontend assets for visualization

## 📋 Project Structure

```
RealmForge/
├── src/
│   ├── api/          # API endpoints and server
│   ├── models/       # Data models
│   ├── services/     # Business logic
│   └── utils/        # Utility functions
├── tests/            # Test suite
├── static/           # Frontend assets
├── .env.example      # Example environment file
├── pyproject.toml    # Project configuration
└── README.md         # This file
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [Three.js](https://threejs.org/)
- Uses OpenAI for content generation
- Developed as part of the AFLOW project

---

<div align="center">
  <p>Made with 💻 and ❤️ by the RealmForge Team</p>
</div>
