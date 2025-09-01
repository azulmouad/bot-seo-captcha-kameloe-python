# 2captcha Integration Guide

This project now includes automatic captcha solving using the 2captcha service. The bots can automatically detect and solve reCAPTCHA v2, reCAPTCHA v3, and hCaptcha challenges.

## 🚀 Quick Setup

1. **Run the setup script:**

   ```bash
   python setup_captcha.py
   ```

2. **Set your 2captcha API key:**

   ```bash
   export APIKEY_2CAPTCHA='your_api_key_here'
   ```

3. **Run the bot:**
   ```bash
   python bot.py  # Regular version
   # or
   python bot_kameleo.py  # Kameleo version
   ```

## 📋 Manual Setup

### 1. Install Requirements

```bash
# For regular bot
pip install -r requirements.txt

# For Kameleo bot
pip install -r requirements_kameleo.txt
```

### 2. Get 2captcha API Key

1. Go to [2captcha.com](https://2captcha.com/)
2. Create an account
3. Add funds to your account
4. Get your API key from the dashboard

### 3. Configure API Key

**Option A: Environment Variable (Recommended)**

```bash
export APIKEY_2CAPTCHA='your_api_key_here'
```

**Option B: Add to shell profile**

```bash
echo 'export APIKEY_2CAPTCHA="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

## 🧪 Testing Captcha Solving

Test the captcha solver with the example script:

```bash
python example/captcha_example.py
```

This will test:

- reCAPTCHA v2 solving
- reCAPTCHA v3 solving
- hCaptcha solving

## 🔧 Configuration

### Basic Configuration

The captcha solver is automatically integrated into both bots. It will:

1. **Auto-detect** captcha types on pages
2. **Automatically solve** detected captchas
3. **Continue** bot operation after solving
4. **Log** all captcha solving activities

### Advanced Configuration

Create a `config.py` file from the example:

```bash
cp config_example.py config.py
```

Edit `config.py` to customize:

```python
CAPTCHA_CONFIG = {
    'api_key': 'your_api_key_here',
    'timeout': 120,  # Timeout for solving
    'recaptcha_v3': {
        'action': 'verify',
        'min_score': 0.3
    },
    'enabled': True,
    'auto_detect': True
}
```

## 📊 Supported Captcha Types

| Type         | Support | Cost (per 1000) | Notes            |
| ------------ | ------- | --------------- | ---------------- |
| reCAPTCHA v2 | ✅      | $1.00           | Most common type |
| reCAPTCHA v3 | ✅      | $2.00           | Score-based      |
| hCaptcha     | ✅      | $1.00           | Privacy-focused  |

## 🔄 How It Works

### Automatic Integration

The captcha solver is integrated at key points:

1. **Google Homepage** - Solves captchas when loading Google
2. **Search Results** - Solves captchas after search submission
3. **Target Website** - Solves captchas on the target domain

### Detection Process

```python
# The bot automatically:
1. Scans page for captcha elements
2. Detects captcha type (reCAPTCHA v2/v3, hCaptcha)
3. Extracts sitekey automatically
4. Sends to 2captcha service
5. Waits for solution
6. Injects solution into page
7. Continues normal operation
```

### Error Handling

- **API Key Missing**: Bot continues without captcha solving
- **Captcha Solve Failed**: Bot logs error and continues
- **Timeout**: Bot moves to next step after timeout
- **Invalid Response**: Bot retries or continues

## 💰 Pricing & Usage

### 2captcha Pricing

- **reCAPTCHA v2**: $1 per 1000 solves
- **reCAPTCHA v3**: $2 per 1000 solves
- **hCaptcha**: $1 per 1000 solves

### Cost Estimation

For typical SEO bot usage:

- **10 proxies × 3 captchas each = 30 captchas**
- **Cost: ~$0.03 - $0.06 per run**
- **Monthly (daily runs): ~$1 - $2**

### Balance Management

Check your balance:

```python
from twocaptcha import TwoCaptcha
solver = TwoCaptcha('your_api_key')
balance = solver.balance()
print(f"Balance: ${balance}")
```

## 🛠️ Troubleshooting

### Common Issues

**1. API Key Not Working**

```bash
# Check if key is set
echo $APIKEY_2CAPTCHA

# Test the key
python -c "from twocaptcha import TwoCaptcha; print(TwoCaptcha('$APIKEY_2CAPTCHA').balance())"
```

**2. Captcha Not Detected**

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

**3. Solve Timeout**

```python
# Increase timeout in config
CAPTCHA_CONFIG['timeout'] = 180  # 3 minutes
```

**4. Low Balance**

- Add funds to your 2captcha account
- Check balance with: `solver.balance()`

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 📝 Code Examples

### Manual Captcha Solving

```python
from captcha_solver import CaptchaSolver
from selenium import webdriver

driver = webdriver.Chrome()
solver = CaptchaSolver('your_api_key')

# Navigate to page with captcha
driver.get('https://example.com/captcha-page')

# Auto-detect and solve
if solver.detect_and_solve_captcha(driver):
    print("Captcha solved!")
else:
    print("Failed to solve captcha")
```

### Specific Captcha Types

```python
# reCAPTCHA v2
solver.solve_recaptcha_v2(driver, sitekey='6LfD3PIbAAAAAJs...')

# reCAPTCHA v3
solver.solve_recaptcha_v3(driver, sitekey='6LfD3PIbAAAAAJs...', action='submit')

# hCaptcha
solver.solve_hcaptcha(driver, sitekey='10000000-ffff-ffff...')
```

### Wait for Captcha

```python
# Wait up to 30 seconds for captcha to appear, then solve
solver.wait_for_captcha_and_solve(driver, max_wait=30, solve_timeout=120)
```

## 🔒 Security Notes

1. **Keep API key secure** - Don't commit to version control
2. **Use environment variables** - Don't hardcode in scripts
3. **Monitor usage** - Check your 2captcha balance regularly
4. **Rate limiting** - 2captcha has rate limits, bot handles this automatically

## 📚 Additional Resources

- [2captcha Documentation](https://2captcha.com/2captcha-api)
- [2captcha Python Library](https://github.com/2captcha/2captcha-python)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [reCAPTCHA Documentation](https://developers.google.com/recaptcha)

## 🆘 Support

If you encounter issues:

1. **Check the logs** - Look for captcha-related errors
2. **Test API key** - Use the test script
3. **Verify balance** - Make sure you have funds
4. **Update dependencies** - Keep packages current

For 2captcha specific issues, contact their support at [2captcha.com/support](https://2captcha.com/support).
