# SEO Python Bot with Kameleo

A Google search automation bot with advanced anti-detection using Kameleo's professional browser fingerprinting protection and proxy rotation.

> **Important**: This documentation is for `bot_kameleo.py` - the advanced Kameleo version. For the basic version, see `README.md`.

## Features

- 🛡️ **Professional Anti-Detection** - Uses Kameleo's real browser fingerprints
- 🔄 **Advanced Proxy Support** - Native proxy authentication with HTTP/SOCKS5
- 🎭 **Complete Fingerprint Protection** - Canvas, WebGL, Audio, Font protection
- 👤 **Human-like Behavior** - Random scrolling, typing delays, realistic interactions
- 📊 **Detailed Logging** - Comprehensive logging to file and console
- 🎯 **Target Domain Finding** - Automatically finds and visits specified domains

## Prerequisites

### 1. Kameleo Installation & Setup

**Step 1: Download and Install Kameleo**

1. Visit [https://kameleo.io](https://kameleo.io)
2. Download Kameleo for your operating system
3. Install the Kameleo application
4. Create a Kameleo account if you don't have one

**Step 2: Start Kameleo.CLI**

**On macOS:**

```bash
# Navigate to Kameleo CLI directory
cd /Applications/Kameleo.app/Contents/Resources/CLI/

# Start Kameleo.CLI with your account credentials
./Kameleo.CLI email=fuzz.chute_6o@icloud.com password=Aqzsed123..@@
```

**On Windows:**

```cmd
# Navigate to Kameleo CLI directory
cd "C:\Program Files\Kameleo\CLI"

# Start Kameleo.CLI with your account credentials
Kameleo.CLI.exe email=<YOUR_EMAIL> password=<YOUR_PASSWORD>
```

**Step 3: Verify Kameleo.CLI is Running**

```bash
# Test if Kameleo.CLI is running on port 5050
curl http://localhost:5050/api/v1/fingerprints
```

If successful, you should see JSON response with fingerprint data.

### 2. System Requirements

- **Python 3.7+** (tested with Python 3.13.7)
- **Kameleo.CLI** running on localhost:5050
- **Valid Kameleo license**
- **macOS/Linux/Windows** support

## Installation

### Quick Setup

1. **Navigate to project directory:**

   ```bash
   cd seo-python-bot
   ```

2. **Run Kameleo installation script:**

   ```bash
   chmod +x install_kameleo.sh
   ./install_kameleo.sh
   ```

3. **Start Kameleo.CLI** (see Prerequisites section above)

4. **Run the Kameleo bot:**
   ```bash
   python3 bot_kameleo.py
   ```

### Manual Installation

```bash
# Install required packages
python3 -m pip install selenium kameleo.local-api-client requests --break-system-packages

# Verify installation
python3 -c "import selenium, kameleo.local_api_client, requests; print('All packages installed!')"
```

## Usage

### 1. Start Kameleo.CLI

**IMPORTANT**: Make sure Kameleo.CLI is running before using the bot:

```bash
# macOS
cd /Applications/Kameleo.app/Contents/Resources/CLI/
./Kameleo.CLI email=your_email@example.com password=your_password

# Windows
cd "C:\Program Files\Kameleo\CLI"
Kameleo.CLI.exe email=your_email@example.com password=your_password
```

Wait for Kameleo.CLI to fully start (you should see it listening on port 5050).

### 2. Run the Kameleo Bot

```bash
# Run the Kameleo version of the bot
python3 bot_kameleo.py
```

**Note**: Make sure to use `bot_kameleo.py` (not `bot.py`) for the Kameleo version with advanced anti-detection.

### 3. Follow the Prompts

- **Search keyword**: e.g., "python tutorials"
- **Target domain**: e.g., "example.com"
- **Proxy list**: Enter proxies one per line, press Enter twice when done

### Example Session

```
Google Search Bot with Proxy Rotation
========================================
Enter search keyword: fotmob
Enter target domain (e.g., example.com): fotmob.com

Enter proxy list (format: ip:port, one per line, press Enter twice when done):
123.456.789.10:8080
98.765.432.10:3128:username:password

Configuration:
Keyword: fotmob
Target Domain: fotmob.com
Proxies: 2

Start the bot? (y/n): y
```

## Proxy Configuration

### Supported Formats

**Simple HTTP Proxy:**

```
123.456.789.10:8080
```

**Authenticated Proxy:**

```
123.456.789.10:8080:username:password
```

### Proxy Types

- **HTTP proxies** (default)
- **SOCKS5 proxies** (modify code to change `value='socks5'`)

## How It Works

1. **Profile Creation** - Creates Kameleo profile with real browser fingerprint
2. **Proxy Setup** - Configures proxy with authentication if needed
3. **Browser Launch** - Starts protected browser session
4. **Google Search** - Searches for keyword with human-like behavior
5. **Target Visit** - Finds and visits target domain
6. **Cleanup** - Properly closes browser and stops profile

## Kameleo Advantages

| Feature                  | Kameleo                       | Undetected ChromeDriver |
| ------------------------ | ----------------------------- | ----------------------- |
| **Browser Fingerprints** | ✅ Real database fingerprints | ❌ Simulated            |
| **Canvas Protection**    | ✅ Hardware-level             | ❌ Basic spoofing       |
| **WebGL Protection**     | ✅ Complete                   | ❌ Limited              |
| **Audio Fingerprinting** | ✅ Protected                  | ❌ Not protected        |
| **Font Fingerprinting**  | ✅ Protected                  | ❌ Not protected        |
| **Proxy Support**        | ✅ Native authentication      | ❌ Requires extensions  |
| **Detection Rate**       | ✅ Extremely low              | ❌ Higher risk          |

## Troubleshooting

### Common Issues

**1. "Failed to initialize Kameleo client"**

```bash
# Check if Kameleo.CLI is running
curl http://localhost:5050/api/v1/fingerprints

# If not running, start Kameleo.CLI with your credentials
```

**2. "No Chrome fingerprints found"**

- Ensure Kameleo.CLI has internet connection
- Check your Kameleo license is valid
- Restart Kameleo.CLI

**3. "Proxy connection failed"**

- Verify proxy format: `ip:port` or `ip:port:user:pass`
- Test proxy manually
- Check authentication credentials

**4. "Connection refused on port 5050"**

```bash
# Check if port is in use
lsof -i :5050

# Use custom port if needed
export KAMELEO_PORT=5051
```

### Kameleo.CLI Issues

- **Won't start**: Check system requirements, run as administrator
- **Port conflicts**: Change port in Kameleo settings
- **License issues**: Verify license validity and expiration

## Configuration

### Environment Variables

```bash
# Custom Kameleo port
export KAMELEO_PORT=5050

# Proxy settings (optional)
export PROXY_HOST=your_proxy_host
export PROXY_PORT=your_proxy_port
export PROXY_USERNAME=your_username
export PROXY_PASSWORD=your_password
```

### Timing Settings

- **Search delay**: 5 seconds after loading Google
- **Typing speed**: 0.05-0.2 seconds between keystrokes
- **Scroll intervals**: 0.5-1.5 seconds between actions
- **Site visit duration**: 20 seconds on target website
- **Proxy rotation delay**: 5-15 seconds between switches

## Advanced Features

### Headless Mode

```python
from kameleo.local_api_client.models import BrowserSettings

# Start profile in headless mode
client.profile.start_profile(profile.id, BrowserSettings(
    arguments=['headless']
))
```

### Custom Fingerprints

```python
# Filter fingerprints by specific criteria
fingerprints = client.fingerprint.search_fingerprints(
    device_type='desktop',
    browser_product='chrome',
    browser_version='>134',
    language='en-US'
)
```

## File Structure

```
seo-python-bot/
├── bot.py                      # Original bot (undetected-chromedriver)
├── bot_kameleo.py              # Main Kameleo bot (USE THIS ONE)
├── requirements.txt            # Original dependencies
├── requirements_kameleo.txt    # Kameleo dependencies
├── install.sh                  # Original installation
├── install_kameleo.sh         # Kameleo installation script
├── README.md                   # Original documentation
├── README_KAMELEO.md          # This Kameleo documentation
├── bot_activity.log           # Generated logs
└── example/                   # Kameleo examples
    ├── connect_with_selenium.py
    ├── start_with_proxy.py
    └── connect_with_puppeteer.py
```

**Important**: Use `bot_kameleo.py` for the advanced Kameleo version, not `bot.py`.

## Performance Tips

1. **Limit concurrent profiles** - Don't create too many at once
2. **Clean up profiles** - Always stop profiles when done
3. **Use quality proxies** - Fast, reliable proxies work best
4. **Monitor resources** - Watch CPU/RAM usage

## Disclaimer

⚠️ **Important**: This tool is for educational and legitimate SEO research purposes only.

- Respect website terms of service and rate limits
- Use responsibly and ethically
- Don't overload servers with requests
- Ensure compliance with local laws
- Test with your own websites first
- Kameleo license required for use

## Support

- **Kameleo Documentation**: [https://docs.kameleo.io](https://docs.kameleo.io)
- **Kameleo Support**: Contact through Kameleo.io
- **Python Client**: kameleo.local-api-client documentation

## License

This project is for educational purposes. Use at your own risk and responsibility. Kameleo.CLI requires a separate license from Kameleo.io.
