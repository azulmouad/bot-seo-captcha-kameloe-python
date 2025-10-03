# Install requirements

pip install selenium kameleo.local-api-client 2captcha-python

# Make sure Kameleo.CLI is running on port 5050

# Run

python3 app.py

#

Perfect! I've fixed the code to use the raw 2captcha API instead of the Python library. This allows us to properly send the data-s parameter.
Key Changes:

Direct HTTP requests to 2captcha API:

Submit: POST https://2captcha.com/in.php with data-s parameter
Poll: GET https://2captcha.com/res.php every 10 seconds

Proper data-s handling:

python params = {
'key': self.api_key,
'method': 'userrecaptcha',
'googlekey': sitekey,
'pageurl': url,
'data-s': data_s, # Now properly sent!
'json': 1
}

Manual polling - Checks every 10 seconds for up to 3 minutes
Better progress feedback - Shows elapsed time while waiting

How it works now:

Detects Google /sorry page
Extracts data-s parameter from page HTML
Sends captcha to 2captcha with data-s via raw API
Polls for solution every 10 seconds
Injects solution and submits

The raw API properly supports the data-s parameter that Google requires. Try running it again - it should work now!
