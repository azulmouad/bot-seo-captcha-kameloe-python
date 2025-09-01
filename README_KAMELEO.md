# SEO Python Bot with Kameleo

A Google search automation bot with advanced anti-detection using Kameleo's professional browser fingerprinting protection and proxy rotation.

## Features

- 🛡️ **Professional Anti-Detection** - Uses Kameleo's real browser fingerprints
- 🔄 **Advanced Proxy Support** - Native proxy authentication with HTTP/SOCKS5
- 🎭 **Complete Fingerprint Protection** - Canvas, WebGL, Audio, Font protection
- 👤 **Human-like Behavior** - Random scrolling, typing delays, realistic interactions
- 📊 **Detailed Logging** - Comprehensive logging to file and console
- 🎯 **Target Domain Finding** - Automatically finds and visits specified domains

## Prerequisites

### 1. Kameleo.CLI Installation

**Download and Install Kameleo.CLI:**

1. Visit [https://kameleo.io](https://kameleo.io)
2. Download Kameleo.CLI for your operating system
3. Install Kameleo application

**Starting Kameleo.CLI:**

**On macOS:**

```bash
# Navigate to Kameleo application folder
cd /Applications/Kameleo.app/Contents/Resources/CLI/

# Start Kameleo.CLI with your credentials
./Kameleo.CLI email=fuzz.chute_6o@icloud.com password=Aqzsed123..@@
```

**On Windows:**

```cmd
# Navigate to Kameleo application folder (default location)
cd "C:\Program Files\Kameleo\CLI"

# Start Kameleo.CLI with your credentials
Kameleo.CLI.exe email=<YOUR_EMAIL> password=<YOUR_PASSWORD>
```

**Verify Kameleo.CLI is Running:**

```bash
# Check if Kameleo.CLI is running on port 5050
curl http://localhost:5050/api/v1/fingerprints
```

If successful, you should see a JSON response with fingerprint data.

### 2. System Requirements

- **Python 3.7+** (tested with Python 3.13.7)
- **Kameleo.CLI** running on localhost:5050
- **macOS/Linux/Windows** support
- Valid proxy list (optional but recommended)

## Installation

### Method 1: Quick Setup (Recommended)

1. **Navigate to project directory:**

   ```bash
   cd seo-python-bot
   ```

2. **Run the Kameleo installation script:**
   ```bash
   chmod +x install_kameleo.sh
   ./install_kameleo.sh
   ```

### Method 2: Manual Installation

1. **Install required packages:**

   ```bash
   python3 -m pip install selenium kameleo.local-api-client requests --break-system-packages
   ```

2. **Verify installation:**
   ```bash
   python3 -c "import selenium, kameleo.local_api_client, requests; print('All packages installed successfully!')"
   ```

## Usage

### Starting Kameleo.CLI

**Before running the bot, make sure Kameleo.CLI is running:**

**On macOS:**

```bash
# Navigate to Kameleo CLI directory
cd /Applications/Kameleo.app/Contents/Resources/CLI/

# Start with your Kameleo account credentials
./Kameleo.CLI email=your_email@example.com password=your_password
```

**On Windows:**

```cmd
# Navigate to Kameleo CLI directory
cd "C:\Program Files\Kameleo\CLI"

# Start with your Kameleo account credentials
Kameleo.CLI.exe email=your_email@example.com password=your_password
```

**Verify it's running:**

```bash
# Test connection
curl http://localhost:5050/api/v1/fingerprints | head -5
```

**Set custom port** (if needed):

```bash
export KAMELEO_PORT=5050  # Default port
```

### Running the Bot

1. **Start the bot:**

   ```bash
   python3 bot_kameleo.py
   ```

2. **Follow the prompts:**
   - Enter search keyword (e.g., "python tutorials")
   - Enter target domain (e.g., "example.com")
   - Enter proxy list (format: ip:port or ip:port:username:password)

### Example Session

```
Google Search Bot with Proxy Rotation
========================================
Enter search keyword: fotmob
Enter target domain (e.g., example.com): fotmob.com

Enter proxy list (format: ip:port, one per line, press Enter twice when done):
123.456.789.10:8080
98.765.432.10:3128:myuser:mypass
111.222.333.44:1080

Configuration:
Keyword: fotmob
Target Domain: fotmob.com
Proxies: 3

Start the bot? (y/n): y
```

## Proxy Configuration

### Supported Proxy Formats

**Simple HTTP Proxy:**

```
123.456.789.10:8080
```

**Authenticated HTTP Proxy:**

```
123.456.789.10:8080:username:password
```

**SOCKS5 Proxy (modify code for socks5):**

```python
# In create_kameleo_profile method, change:
proxy_config = ProxyChoice(
    value='socks5',  # Change from 'http' to 'socks5'
    extra=Server(...)
)
```

### Proxy Testing

The bot automatically tests each proxy before use:

- ✅ Connectivity test via httpbin.org
- ✅ IP verification to ensure proxy is working
- ✅ Real IP masking verification

## How It Works

### 1. **Kameleo Profile Creation**

- Selects random Chrome fingerprint from Kameleo's database
- Creates profile with proxy configuration
- Applies real browser fingerprinting protection

### 2. **Browser Automation**

- Connects to Kameleo WebDriver endpoint
- Uses real browser with complete anti-detection
- Performs human-like interactions

### 3. **Search Process**

- Opens Google with protected fingerprint
- Searches for specified keyword
- Performs realistic scrolling and interactions
- Finds and visits target domain
- Stays on site for configured duration

### 4. **Cleanup**

- Properly closes browser session
- Stops Kameleo profile
- Cleans up resources

## Configuration

### Environment Variables

```bash
# Kameleo.CLI port (default: 5050)
export KAMELEO_PORT=5050

# Proxy configuration (for start_with_proxy.py example)
export PROXY_HOST=your_proxy_host
export PROXY_PORT=your_proxy_port
export PROXY_USERNAME=your_username
export PROXY_PASSWORD=your_password
```

### Timing Settings

The bot includes realistic timing patterns:

- **Search delay**: 5 seconds after loading Google
- **Typing speed**: 0.05-0.2 seconds between keystrokes
- **Scroll intervals**: 0.5-1.5 seconds between scroll actions
- **Site visit duration**: 20 seconds on target website
- **Proxy rotation delay**: 5-15 seconds between proxy switches

## Kameleo vs Undetected ChromeDriver

| Feature                  | Kameleo                            | Undetected ChromeDriver  |
| ------------------------ | ---------------------------------- | ------------------------ |
| **Browser Fingerprints** | ✅ Real fingerprints from database | ❌ Simulated/modified    |
| **Canvas Protection**    | ✅ Hardware-level protection       | ❌ Basic spoofing        |
| **WebGL Protection**     | ✅ Complete protection             | ❌ Limited               |
| **Audio Fingerprinting** | ✅ Protected                       | ❌ Not protected         |
| **Font Fingerprinting**  | ✅ Protected                       | ❌ Not protected         |
| **Proxy Authentication** | ✅ Native support                  | ❌ Requires extensions   |
| **Detection Rate**       | ✅ Extremely low                   | ❌ Higher detection risk |
| **Professional Use**     | ✅ Enterprise grade                | ❌ Hobbyist level        |

## Troubleshooting

### Common Issues

1. **"Failed to initialize Kameleo client"**

   ```bash
   # Check if Kameleo.CLI is running
   curl http://localhost:5050/api/v1/fingerprints

   # Start Kameleo.CLI if not running
   # Launch from applications or command line
   ```

2. **"No Chrome fingerprints found"**

   - Ensure Kameleo.CLI has internet connection
   - Check Kameleo.CLI logs for errors
   - Restart Kameleo.CLI

3. **"Proxy connection failed"**

   - Verify proxy format (ip:port or ip:port:user:pass)
   - Test proxy manually with curl
   - Check proxy authentication credentials

4. **"Connection refused on port 5050"**

   ```bash
   # Check if port is in use
   lsof -i :5050

   # Set custom port if needed
   export KAMELEO_PORT=5051
   ```

### Kameleo.CLI Issues

1. **Kameleo.CLI won't start:**

   - Check system requirements
   - Run as administrator (Windows) or with sudo (Linux/Mac)
   - Check firewall settings

2. **Port conflicts:**

   - Change port in Kameleo.CLI settings
   - Update KAMELEO_PORT environment variable

3. **License issues:**
   - Ensure valid Kameleo license
   - Check license expiration
   - Contact Kameleo support

## Logs and Monitoring

### Log Files

- **Console output** - Real-time progress updates
- **bot_activity.log** - Detailed log file with timestamps
- **Kameleo.CLI logs** - Check Kameleo.CLI interface for detailed logs

### Monitoring Proxy Performance

```bash
# Monitor log file in real-time
tail -f bot_activity.log

# Filter for proxy-related logs
grep "proxy\|Proxy" bot_activity.log
```

## File Structure

```
seo-python-bot/
├── bot_kameleo.py              # Main Kameleo bot script
├── requirements_kameleo.txt    # Kameleo dependencies
├── install_kameleo.sh         # Kameleo installation script
├── README_KAMELEO.md          # This file
├── bot_activity.log           # Generated log file
└── example/                   # Kameleo example files
    ├── connect_with_selenium.py
    ├── start_with_proxy.py
    └── connect_with_puppeteer.py
```

## Advanced Usage

### Custom Fingerprint Selection

```python
# Modify create_kameleo_profile method to select specific fingerprints
fingerprints = self.kameleo_client.fingerprint.search_fingerprints(
    device_type='desktop',
    browser_product='chrome',
    browser_version='>134',  # Recent Chrome versions
    language='en-US',  # Specific language
    resolution='1920x1080'  # Specific resolution
)
```

### Headless Mode Support

```python
# To run in headless mode for resource saving
from kameleo.local_api_client.models import BrowserSettings

# Start profile in headless mode
client.profile.start_profile(profile.id, BrowserSettings(
    arguments=['headless']
))
```

### Multiple Profile Management

```python
# Create multiple profiles for concurrent usage
profiles = []
for proxy in proxy_list[:5]:  # Limit concurrent profiles
    profile = self.create_kameleo_profile(proxy)
    profiles.append(profile)
```

## Performance Tips

1. **Limit Concurrent Profiles** - Don't create too many profiles simultaneously
2. **Profile Cleanup** - Always stop profiles when done
3. **Proxy Quality** - Use high-quality, fast proxies
4. **Resource Monitoring** - Monitor CPU/RAM usage with multiple profiles

## Disclaimer

⚠️ **Important**: This tool is for educational and legitimate SEO research purposes only.

- Respect website terms of service and rate limits
- Use responsibly and ethically
- Don't overload servers with excessive requests
- Ensure compliance with local laws and regulations
- Test with your own websites first
- Kameleo license required for commercial use

## Support

- **Kameleo Documentation**: [https://docs.kameleo.io](https://docs.kameleo.io)
- **Kameleo Support**: Contact through Kameleo.io
- **Python Client**: Check kameleo.local-api-client documentation

## License

This project is for educational purposes. Use at your own risk and responsibility. Kameleo.CLI requires a separate license from Kameleo.io.
