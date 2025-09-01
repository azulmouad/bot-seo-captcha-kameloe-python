# SEO Python Bot

A Google search automation bot with proxy rotation for SEO purposes.

## Features

- 🔄 Proxy rotation support
- 🤖 Anti-detection measures
- 👤 Human-like behavior (scrolling, typing delays)
- 📊 Detailed logging
- 🎯 Target domain finding and visiting

## Installation

### Quick Setup

```bash
./install.sh
```

### Manual Installation

```bash
python3 -m pip install -r requirements.txt
```

### Required Packages

- `selenium` - Web automation framework
- `undetected-chromedriver` - Anti-detection ChromeDriver
- `fake-useragent` - Random user agent generation
- `requests` - HTTP requests for proxy testing

## Prerequisites

- Python 3.7+
- Google Chrome browser installed
- Valid proxy list (optional but recommended)

## Usage

1. Run the bot:

```bash
python3 bot.py
```

2. Enter required information:
   - Search keyword
   - Target domain (e.g., example.com)
   - Proxy list (format: ip:port, one per line)

## Example

```
Enter search keyword: python tutorials
Enter target domain: realpython.com

Enter proxy list (format: ip:port, one per line):
123.456.789.10:8080
98.765.432.10:3128
```

## How it Works

1. Tests each proxy for connectivity
2. Verifies IP masking is working
3. Opens Google with random user agent
4. Searches for the specified keyword
5. Performs human-like scrolling
6. Finds and clicks on target domain
7. Stays on target site for 20 seconds
8. Moves to next proxy and repeats

## Logs

Activity is logged to `bot_activity.log` and console output.

## Disclaimer

This tool is for educational and legitimate SEO research purposes only. Please respect website terms of service and rate limits.
