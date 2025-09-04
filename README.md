# SEO Bot with Web Dashboard

A professional SEO automation bot with advanced anti-detection using Kameleo and a modern web dashboard for easy management.

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.7+**
- **Google Chrome** browser
- **Kameleo** application and license

### 2. Installation

```bash
# Clone or download this project
cd seo-bot-project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements_web.txt
```

### 3. Setup Kameleo

1. **Download Kameleo** from [kameleo.io](https://kameleo.io)
2. **Install** the application
3. **Start Kameleo.CLI** with your credentials:

```bash
# macOS/Linux
# Navigate to Kameleo CLI directory
cd /Applications/Kameleo.app/Contents/Resources/CLI/
# Start Kameleo.CLI with your account credentials
./Kameleo.CLI email=fuzz.chute_6o@icloud.com password=Aqzsed123..@@

```

### 4. Run the Dashboard

```bash
# Activate virtual environment
source venv/bin/activate

# Start the dashboard
python3 run_dashboard.py
```

Open your browser to: **http://localhost:8080**

## 📊 Using the Dashboard

### Configuration Card

1. **Keyword**: Enter your search term (e.g., "python tutorials")
2. **Domain**: Target domain to find (e.g., "example.com")
3. **Max Pages**: How many Google pages to search (1-30)
4. **Proxy List**: Add proxies in format `ip:port:username:password`

### Controls

- **Upload File**: Upload a .txt file with proxy list
- **Start Bot**: Begin the SEO bot execution
- **Stop Bot**: Stop the running bot
- **Export Results**: Download results as CSV

### Real-time Monitoring

- **Status**: Live bot status and progress
- **Live Logs**: Terminal-style output with color coding
- **Results**: Table showing found domains with page and position

## 📁 Project Structure

```
seo-bot/
├── bot_kameleo.py          # Main bot with Kameleo integration
├── app.py                  # Flask web server
├── dashboard.html          # Web dashboard interface
├── run_dashboard.py        # Easy startup script
├── requirements_web.txt    # Python dependencies
├── test_captcha_kameleo.py # Captcha testing utility
└── README.md              # This file
```

## 🔧 Configuration

### Proxy Format

```
# Simple proxy
123.456.789.10:8080

# Authenticated proxy
123.456.789.10:8080:username:password
```

### Environment Variables (Optional)

```bash
export KAMELEO_PORT=5050        # Kameleo CLI port
export TWOCAPTCHA_API_KEY=xxx   # 2captcha API key
```

## 🛠️ Troubleshooting

### Common Issues

**1. "Kameleo.CLI is not running"**

```bash
# Check if Kameleo.CLI is running
curl http://localhost:5050/api/v1/fingerprints

# If not running, start it with your credentials
./Kameleo.CLI email=your_email password=your_password
```

**2. "Port 8080 is in use"**

- Change port in `app.py` and `run_dashboard.py`
- Or kill the process using the port

**3. "Missing packages"**

```bash
# Make sure virtual environment is activated
source venv/bin/activate
pip install -r requirements_web.txt
```

**4. "Proxy connection failed"**

- Verify proxy format: `ip:port` or `ip:port:user:pass`
- Test proxy manually
- Check authentication credentials

### Kameleo Issues

**License Problems**

- Verify your Kameleo license is valid
- Check license expiration date
- Contact Kameleo support if needed

**Connection Issues**

- Ensure Kameleo.CLI is running before starting the bot
- Check firewall settings
- Verify port 5050 is not blocked

## 📈 Features

### Anti-Detection

- ✅ Real browser fingerprints from Kameleo database
- ✅ Canvas, WebGL, Audio fingerprint protection
- ✅ Unique fingerprint per proxy session
- ✅ Human-like behavior simulation

### Web Dashboard

- ✅ Real-time status monitoring
- ✅ Live log streaming
- ✅ Progress tracking with visual indicators
- ✅ Results export to CSV
- ✅ Proxy management with file upload

### Bot Capabilities

- ✅ Multi-page Google search (1-30 pages)
- ✅ Exact position tracking (where domain found)
- ✅ Proxy rotation with authentication
- ✅ Captcha solving integration
- ✅ Realistic website interaction

## 🔐 Security Notes

- Keep your Kameleo credentials secure
- Use quality proxies from trusted providers
- Respect website terms of service
- Don't overload servers with requests
- Use for legitimate SEO research only

## 📞 Support

### Prerequisites Check

```bash
# Check Python version
python3 --version

# Check if Kameleo.CLI is running
curl http://localhost:5050/api/v1/fingerprints

# Test proxy connection
curl --proxy ip:port http://httpbin.org/ip
```

### Logs Location

- Dashboard logs: Real-time in web interface
- Bot logs: `bot_activity.log` (auto-generated)
- Flask logs: Console output

## 🎯 Example Usage

1. **Start Kameleo.CLI** with your credentials
2. **Run the dashboard**: `python3 run_dashboard.py`
3. **Open browser**: http://localhost:8080
4. **Configure bot**:
   - Keyword: "best python courses"
   - Domain: "realpython.com"
   - Max Pages: 5
   - Add your proxy list
5. **Click Start** and monitor real-time results
6. **Export results** when complete

## 📄 License

This project is for educational and legitimate SEO research purposes only. Use responsibly and in compliance with applicable laws and website terms of service.

---

**Need help?** Check the troubleshooting section above or review the logs for detailed error messages.
