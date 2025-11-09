# BrandAI - AI Critique Engine for Generated Ads

Build the AI That Critiques, Improves, and Trusts AI-Generated Ads

## Overview

BrandAI is an AI system that generates ads and evaluates them across multiple dimensions (brand alignment, visual quality, message clarity, and safety & ethics) to ensure they are ready for autonomous deployment.

## Features

- **Brand Kit Extraction**: Extract brand information from logos, images, and optional external sources
- **Ad Generation**: Generate 3-4 variations of ads using Google Vertex AI (Imagen 2, Veo)
- **Critique Engine**: Comprehensive evaluation using Gemini Vision, CLIP, and OpenCV
- **Refinement**: Automatic improvement through prompt refinement or image enhancement
- **Multi-Agent Workflow**: LangGraph-based orchestration

## Tech Stack

- **Backend**: FastAPI, Python 3.12
- **Orchestration**: LangGraph
- **AI Models**: Gemini 1.5 Pro Vision, Vertex AI (Imagen 2, Veo), CLIP
- **Image Processing**: OpenCV, Pillow
- **Containerization**: Docker

## Project Structure

See `ARCHITECTURE.md` for complete architecture documentation.

## Setup

1. Clone the repository
2. Set up GCP credentials in `config/gcp/`
3. Copy `.env.example` to `.env` and fill in your credentials
4. Build and run with Docker:
   ```bash
   docker-compose up --build
   ```

## API Endpoints

- `POST /generate` - Generate and critique ads
- `GET /status/{run_id}` - Check generation status
- `GET /health` - Health check

## Documentation

- `ARCHITECTURE.md` - System architecture
- `PROGRESS_TRACKER.md` - Implementation progress

## License

MIT

