# The Rizzistant

A real-time date coaching assistant powered by **Letta AI** that monitors conversations and provides intelligent, context-aware feedback with persistent memory across all your dates.

## Features

- **Stateful AI Coaching**: Powered by Letta AI with persistent memory across ALL dates
- **Real-time conversation monitoring** via live transcripts with speaker detection
- **Context-aware analysis** that remembers past dates and tracks improvement
- **Smart warnings** to help avoid conversation pitfalls (especially CS topics!)
- **Pattern recognition** across multiple dates to identify recurring issues
- **Historical comparison** - see how each date compares to previous ones
- **Personalized coaching** that adapts to your strengths and weaknesses
- **Emergency exit** with code word and phone call
- Integration with OMI for cross-platform memory storage

## Prerequisites

- Docker installed on your system
- Python 3.9+ (for local development)
- Letta Cloud account (sign up at https://app.letta.com/)
- OMI account for memory integration
- Twilio account for emergency phone calls

## Environment Variables

Create a `.env` file in the project root with your actual credentials. You can use `.env.example` as a template.

### Required Variables

```bash
# Letta AI - Get your API key from https://app.letta.com/
LETTA_API_KEY=your_letta_api_key_here

# OMI Integration - Get from https://omi.me/
OMI_APP_ID=your_omi_app_id_here
OMI_API_KEY=your_omi_api_key_here

# Twilio - For emergency exit phone calls
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number_here
PHONE_NUMBER=your_personal_phone_number_here

# Optional: Anthropic (legacy, now using Letta)
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### Getting Your Letta API Key

1. Visit https://app.letta.com/
2. Create an account or sign in
3. Navigate to Settings → API Keys
4. Create a new API key
5. Copy and paste it into your `.env` file

## Quick Start

### Using Docker (Recommended)

1. **Start Server**
   ```bash
   make dev
   ```
   The app will be running at `http://localhost:8000`

2. **Expose with ngrok (if running locally)**
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

### Letta AI Architecture

The Rizzistant uses **Letta's stateful agent system** to maintain persistent memory and context:

1. **One Agent Per User**: Each user gets a dedicated Letta agent with memory that persists forever
2. **Stateful Real-Time Analysis**: The agent maintains conversation context automatically
3. **Memory Blocks**: Tracks current date status, warnings given, code word, and date count
4. **Archival Memory**: Stores complete transcripts and summaries from ALL past dates
5. **Historical Awareness**: Compares current performance against patterns from all previous dates

### User Flow

1. **Start Date**: Say "start date" to begin monitoring
2. **Real-Time Coaching**:
   - Agent analyzes each transcript batch with full context
   - Detects problematic topics (especially CS-related)
   - Sends casual, funny warnings when needed
   - Automatically prevents duplicate warnings
3. **Stuck Detection**: Say "yeah okay so" to get a helpful conversation tip
4. **Emergency Exit**: Say your code word (default: "peanuts") for instant phone rescue
5. **End Date**: Say "end date" to get a comprehensive performance report with:
   - Overall scores across 8 categories
   - Comparison to all past dates
   - Pattern recognition (recurring issues)
   - Specific examples from the conversation
   - Actionable improvement plan

### Why Letta?

Unlike traditional chatbots that forget everything after each interaction:
- **Persistent Memory**: Never forgets any date or insight
- **Pattern Recognition**: Identifies trends across 5, 10, 20+ dates
- **No Manual State Management**: Letta handles all context automatically
- **Scalable**: Handles infinitely long conversation histories
- **Personalized**: Learns your specific strengths and weaknesses over time

## Voice Commands

| Command | Action |
|---------|--------|
| "start date" | Begin a new date session |
| "end date" | Finish date and get summary |
| "edit code word [word]" | Update emergency code word |
| "[code word]" | Trigger emergency exit |
| "yeah okay so" | Get unstuck with a conversation tip |

## Architecture

```
User Device (Omi Transcription)
        ↓
POST /livetranscript
        ↓
Letta Agent (Stateful AI)
    ├── Memory Blocks (active state)
    ├── Archival Memory (all past dates)
    └── Autonomous Decision Making
        ↓
Real-time Warnings / Tips / Summaries
        ↓
OMI Memory Storage (cross-platform sync)
```
