# The Rizzistant

A real-time date coaching assistant that monitors conversations and provides intelligent feedback using Claude AI.

## Features

- Real-time conversation monitoring via live transcripts
- AI-powered analysis to detect conversation issues
- Smart warnings to help improve dating conversations
- Date session management (start/end)
- Post-date summaries with actionable tips
- Integration with OMI for memory storage

## Prerequisites

- Docker installed on your system
- Environment variables configured (see below)

## Environment Variables

Create a `.env` file in the parent directory (`/Users/alex/Personal/calhacks/`) with the following variables:

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OMI_APP_ID=your_omi_app_id_here
OMI_API_KEY=your_omi_api_key_here
```

## Quick Start

### Using Docker (Recommended)

1. **Build the Docker image:**
   ```bash
   make build
   ```

2. **Start the application:**
   ```bash
   make start
   ```
   The app will be running at `http://localhost:8000`

3. **Expose with ngrok (if running locally)**
   ```bash
   ngrok http 8000
   ```

## API Endpoints

### `POST /livetranscript`

Receives live transcript segments and provides real-time coaching.

### `POST /webhook`

Webhook endpoint for receiving memory data.

### `GET /` (root)

Health check endpoint.

## Docker Commands

| Command | Description |
|---------|-------------|
| `make build` | Build the Docker image |
| `make start` | Start the container (auto-stops existing) |
| `make stop` | Stop the running container |
| `make logs` | View container logs (follows output) |
| `make clean` | Remove container and image |

## How It Works

1. **Session Management**: Users can start/end date sessions with voice commands
2. **Real-time Analysis**: Each transcript batch is analyzed by Claude AI for conversation issues
3. **Smart Warnings**: The system detects problematic topics (especially CS-related) and provides coaching
4. **Warning Deduplication**: Prevents sending duplicate warnings for the same issue
5. **Post-Date Summary**: Generates a comprehensive summary with tips after each date
