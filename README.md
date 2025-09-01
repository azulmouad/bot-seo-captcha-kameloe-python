# SEO Python Bot

A Google search automation bot with proxy rotation for SEO purposes. This bot simulates human-like behavior to search Google, find target domains, and visit them using rotating proxies.

## Features

- 🔄 **Proxy rotation support** - Automatically rotates through multiple proxies
- 🤖 **Anti-detection measures** - Uses undetected ChromeDriver and random user agents
- 👤 **Human-like behavior** - Random scrolling, typing delays, and realistic interactions
- 📊 **Detailed logging** - Comprehensive logging to file and console
- 🎯 **Target domain finding** - Automatically finds and visits specified domains
- ⏱️ **Configurable timing** - Stays on target sites for specified duration

## Prerequisites

- **Python 3.7+** (tested with Python 3.13.7)
- **Google Chrome browser** installed on your system
- **macOS/Linux/Windows** support
- Valid proxy list (optional but recommended for production use)

## Installation

### Method 1: Quick Setup (Recommended)

1. **Clone or download** this repository
2. **Navigate** to the project directory:
   ```bash
   cd seo-python-bot
   ```
3. **Run the installation script**:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

### Method 2: Manual Installation

1. **Install required packages**:

   ```bash
   python3 -m pip install selenium undetected-chromedriver fake-useragent requests setuptools --break-system-packages
   ```

2. **Verify installation**:
   ```bash
   python3 -c "import selenium, undetected_chromedriver, fake_useragent, requests; print('All packages installed successfully!')"
   ```

### Required Packages

- `selenium==4.15.2` - Web automation framework
- `undetected-chromedriver==3.5.5` - Anti-detection ChromeDriver
- `fake-useragent==1.4.0` - Random user agent generation
- `requests==2.31.0` - HTTP requests for proxy testing
- `setuptools` - Required for Python 3.12+ compatibility

## Usage

### Basic Usage

1. **Run the bot**:

   ```bash
   python3 bot.py
   ```

2. **Follow the prompts**:
   - Enter search keyword (e.g., "python tutorials")
   - Enter target domain (e.g., "example.com")
   - Enter proxy list (format: ip:port, one per line, press Enter twice when done)

### Example Session

```
Google Search Bot with Proxy Rotation
========================================
Enter search keyword: fotmob
Enter target domain (e.g., example.com): fotmob.com

Enter proxy list (format: ip:port, one per line, press Enter twice when done):
123.456.789.10:8080
98.765.432.10:3128

Configuration:
Keyword: fotmob
Target Domain: fotmob.com
Proxies: 2

Start the bot? (y/n): y
```

### Proxy Format

**Standard HTTP Proxies:**

```
123.456.789.10:8080
98.765.432.10:3128
111.222.333.44:8080
```

**Authenticated Proxies:**
For proxies requiring authentication, you may need to modify the code to include username:password format.

## How It Works

1. **Proxy Testing** - Tests each proxy for connectivity and speed
2. **IP Verification** - Verifies that the proxy is masking your real IP
3. **Browser Setup** - Launches Chrome with anti-detection measures
4. **Google Search** - Searches for your specified keyword
5. **Human Simulation** - Performs realistic scrolling and interactions
6. **Target Finding** - Locates your target domain in search results
7. **Site Visit** - Clicks on target domain and stays for 20 seconds
8. **Rotation** - Moves to next proxy and repeats the process

## Configuration

### Timing Settings

- **Search delay**: 5 seconds after loading Google
- **Typing speed**: 0.05-0.2 seconds between keystrokes
- **Scroll intervals**: 0.5-1.5 seconds between scroll actions
- **Site visit duration**: 20 seconds on target website
- **Proxy rotation delay**: 5-15 seconds between proxy switches

### Anti-Detection Features

- Random user agents
- Disabled automation indicators
- Random screen resolutions
- Human-like mouse movements
- Variable timing patterns

## Logs

All activity is logged to:

- **Console output** - Real-time progress updates
- **bot_activity.log** - Detailed log file with timestamps

## Troubleshooting

### Common Issues

1. **"No module named 'distutils'"**

   ```bash
   python3 -m pip install setuptools --break-system-packages
   ```

2. **"Chrome not found"**

   - Install Google Chrome from [chrome.google.com](https://chrome.google.com)

3. **"Proxy connection failed"**

   - Verify proxy format (ip:port)
   - Test proxy manually
   - Check proxy authentication requirements

4. **"Permission denied"**
   ```bash
   chmod +x install.sh
   ```

### Python Version Issues

If you're using Python 3.12+, make sure to install setuptools:

```bash
python3 -m pip install setuptools --break-system-packages
```

## File Structure

```
seo-python-bot/
├── bot.py              # Main bot script
├── requirements.txt    # Python dependencies
├── install.sh         # Installation script
├── README.md          # This file
└── bot_activity.log   # Generated log file
```

## Disclaimer

⚠️ **Important**: This tool is for educational and legitimate SEO research purposes only.

- Respect website terms of service and rate limits
- Use responsibly and ethically
- Don't overload servers with excessive requests
- Ensure compliance with local laws and regulations
- Test with your own websites first

## License

This project is for educational purposes. Use at your own risk and responsibility.
