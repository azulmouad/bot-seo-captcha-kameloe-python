#!/bin/bash

echo "🚀 Setting up SEO Python Bot with Kameleo..."
echo "============================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is available
if ! python3 -m pip --version &> /dev/null; then
    echo "❌ pip is not available. Please install pip first."
    exit 1
fi

echo "✅ pip found: $(python3 -m pip --version)"

# Install required packages for Kameleo version
echo ""
echo "📦 Installing required packages for Kameleo..."
python3 -m pip install -r requirements_kameleo.txt --break-system-packages

echo ""
echo "📦 Installing Kameleo Python client..."
echo "⚠️  Note: The Kameleo Python client should be installed with Kameleo.CLI"
echo "   If you don't have it, you may need to:"
echo "   1. Download Kameleo.CLI from https://kameleo.io"
echo "   2. The Python client is typically included with Kameleo.CLI"
echo "   3. Or install from local wheel file if provided"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All packages installed successfully!"
    echo ""
    echo "⚠️  IMPORTANT PREREQUISITES:"
    echo "   1. Install Kameleo.CLI from https://kameleo.io"
    echo "   2. Start Kameleo.CLI (it should run on port 5050 by default)"
    echo "   3. Make sure Kameleo.CLI is running before using the bot"
    echo ""
    echo "🎯 To run the Kameleo bot:"
    echo "   python3 bot_kameleo.py"
    echo ""
    echo "📋 Required packages installed:"
    echo "   - selenium (web automation)"
    echo "   - kameleo.local-api-client (advanced anti-detection)"
    echo "   - requests (HTTP requests)"
    echo ""
    echo "🔧 Environment variables (optional):"
    echo "   export KAMELEO_PORT=5050  # Default port"
    echo ""
    echo "🌟 Kameleo provides superior anti-detection:"
    echo "   - Real browser fingerprints"
    echo "   - Canvas/WebGL/Audio fingerprint protection"
    echo "   - Font fingerprint protection"
    echo "   - Much more advanced than undetected-chromedriver"
else
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi