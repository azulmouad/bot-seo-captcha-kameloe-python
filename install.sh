#!/bin/bash

echo "🚀 Setting up SEO Python Bot..."
echo "================================"

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

# Install required packages
echo ""
echo "📦 Installing required packages..."
python3 -m pip install -r requirements.txt --break-system-packages

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All packages installed successfully!"
    echo ""
    echo "🎯 To run the bot:"
    echo "   python3 bot.py"
    echo ""
    echo "📋 Required packages installed:"
    echo "   - selenium (web automation)"
    echo "   - undetected-chromedriver (anti-detection)"
    echo "   - fake-useragent (random user agents)"
    echo "   - requests (HTTP requests)"
    echo ""
    echo "⚠️  Make sure Google Chrome is installed on your system!"
else
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi