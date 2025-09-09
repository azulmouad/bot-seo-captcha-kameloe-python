# SEO Bot Project Structure

## Overview

This project has been refactored into a well-organized, modular structure for better maintainability and scalability.

## Directory Structure

```
seo-bot/
├── main.py                     # Main application entry point
├── requirements.txt            # Python dependencies
├── dashboard.html             # Frontend dashboard
├── bot_kameleo.py            # Original Kameleo bot (kept for compatibility)
├── app.py                    # Legacy file (can be removed after migration)
│
├── src/                      # Source code package
│   ├── __init__.py
│   │
│   ├── api/                  # API layer
│   │   ├── __init__.py
│   │   ├── routes.py         # Flask API routes
│   │   └── websocket.py      # WebSocket handlers
│   │
│   ├── bot/                  # Bot logic
│   │   ├── __init__.py
│   │   ├── enhanced_bot.py   # Enhanced Google Search Bot
│   │   ├── bot_runner.py     # Bot execution and management
│   │   ├── target_finder.py  # Target domain finding logic
│   │   └── website_interactor.py # Website interaction logic
│   │
│   └── utils/                # Utilities
│       ├── __init__.py
│       ├── bot_status.py     # Global state management
│       ├── helpers.py        # Helper functions
│       └── logging_config.py # Logging configuration
│
└── PROJECT_STRUCTURE.md      # This file
```

## Module Descriptions

### Main Application (`main.py`)

- Entry point for the application
- Sets up Flask app, SocketIO, and logging
- Configures routes and WebSocket handlers

### API Layer (`src/api/`)

- **routes.py**: All Flask API endpoints (start, stop, pause, resume, status)
- **websocket.py**: WebSocket event handlers for real-time communication

### Bot Logic (`src/bot/`)

- **enhanced_bot.py**: Enhanced Google Search Bot with web integration
- **bot_runner.py**: Manages bot execution, pause/resume, and web updates
- **target_finder.py**: Handles finding and visiting target domains
- **website_interactor.py**: Realistic human-like website interactions

### Utilities (`src/utils/`)

- **bot_status.py**: Global state management (bot_status, bot_results, bot_logs)
- **helpers.py**: Utility functions (JSON serialization, etc.)
- **logging_config.py**: Logging setup and WebSocket log handler

## Key Features

### Modular Design

- Each module has a single responsibility
- Easy to test and maintain individual components
- Clear separation of concerns

### Pause/Resume Functionality

- Comprehensive pause checks throughout all bot operations
- Browser remains open during pause for manual interaction
- Seamless resume from any point in execution

### Device Profile Support

- Desktop profiles (Chrome fingerprints)
- Mobile profiles (Safari on iOS fingerprints)
- Automatic fallback for unsupported profiles

### Real-time Web Interface

- Live status updates via WebSocket
- Real-time logging and results
- Responsive dashboard with pause/resume controls

## Running the Application

### Start the server:

```bash
python main.py
```

### Access the dashboard:

```
http://localhost:8080
```

## Migration Notes

The original `app.py` file has been split into multiple focused modules:

- API routes → `src/api/routes.py`
- Bot logic → `src/bot/enhanced_bot.py`, `src/bot/bot_runner.py`
- Target finding → `src/bot/target_finder.py`
- Website interaction → `src/bot/website_interactor.py`
- Utilities → `src/utils/`

This structure makes the codebase much more maintainable and allows for easier testing and future enhancements.
