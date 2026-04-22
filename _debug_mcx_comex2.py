"""Deep debug: extract gold data from working sources."""
import requests
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# ========= YAHOO FINANCE - GC=F specific =========
print("=== YAHOO FINANCE GC=F (targeted) ===")
try:
    r = requests.get('https://finance.yahoo.com/quote/GC=F/', timeout=10, headers=headers)
    # Find the JSON blob for GC=F specifically
    # Yahoo embeds data in script tags
    m = re.search(r'"GC=F".*?"regularMarketPrice":\{"raw":([\d.]+)', r.text)
    if m:
        print(f"GC=F price: ${m.group(1)}")
    else:
        # Try finding in page source
        m = re.search(r'"symbol":"GC=F"[^}]*"regularMarketPrice":\{"raw":([\d.]+)', r.text)
        if m:
            print(f"GC=F price (alt): ${m.group(1)}")
        else:
            # Try the v8 API
            print("Not found in page, trying API...")
            r2 = requests.get(
                'https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1d&range=1d',
                timeout=10, headers=headers
            )
            if r2.status_code == 200:
                data = r2.json()
                meta = data.get('chart', {}).get('result', [{}])[0].get('meta', {})
                print(f"GC=F price (API): ${meta.get('regularMarketPrice')}")
                print(f"Previous close: ${meta.get('previousClose')}")
                print(f"Currency: {meta.get('currency')}")
            else:
                print(f"API status: {r2.status_code}")
except Exception as e:
    print(f"Error: {e}")

# ========= YAHOO FINANCE - MCX Gold =========
print("\n=== YAHOO FINANCE GOLDM=F (MCX) ===")
try:
    r = requests.get(
        'https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1d&range=5d',
        timeout=10, headers=headers
    )
    if r.status_code == 200:
        data = r.json()
        result = data.get('chart', {}).get('result', [{}])[0]
        meta = result.get('meta', {})
        print(f"Symbol: {meta.get('symbol')}")
        print(f"Price: {meta.get('regularMarketPrice')}")
        print(f"Currency: {meta.get('currency')}")
        # Get historical
        timestamps = result.get('timestamp', [])
        closes = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
        for ts, cl in zip(timestamps[-5:], closes[-5:]):
            from datetime import datetime
            dt = datetime.fromtimestamp(ts)
            print(f"  {dt.strftime('%Y-%m-%d')}: ${cl:.2f}" if cl else f"  {dt}: None")
    else:
        print(f"Status: {r.status_code}")
except Exception as e:
    print(f"Error: {e}")

# ========= YAHOO FINANCE - Silver =========
print("\n=== YAHOO FINANCE SI=F (Silver) ===")
try:
    r = requests.get(
        'https://query1.finance.yahoo.com/v8/finance/chart/SI=F?interval=1d&range=1d',
        timeout=10, headers=headers
    )
    if r.status_code == 200:
        data = r.json()
        meta = data.get('chart', {}).get('result', [{}])[0].get('meta', {})
        print(f"Silver price: ${meta.get('regularMarketPrice')}")
    else:
        print(f"Status: {r.status_code}")
except Exception as e:
    print(f"Error: {e}")

# ========= MONEYCONTROL - deeper analysis =========
print("\n=== MONEYCONTROL (deeper) ===")
try:
    r = requests.get('https://www.moneycontrol.com/commodity/gold-price.html', timeout=10, headers=headers)
    # Save first 2000 chars for analysis
    text = r.text[:15000]
    # Look for structured data
    m = re.findall(r'(?:gold|mcx|spot).*?(\d{4,6}(?:\.\d+)?)', text, re.I)
    print(f"Gold-related numbers: {m[:10]}")
    # Look for table data
    m2 = re.findall(r'<td[^>]*>\s*(\d{4,6}(?:\.\d+)?)\s*</td>', text)
    print(f"Table numbers: {m2[:10]}")
    # Look for JSON data
    m3 = re.findall(r'"(?:last|price|ltp|close)":\s*"?([\d.]+)"?', text, re.I)
    print(f"JSON prices: {m3[:10]}")
except Exception as e:
    print(f"Error: {e}")

# ========= Try MCX from moneycontrol API =========
print("\n=== MONEYCONTROL MCX API ===")
try:
    r = requests.get(
        'https://priceapi.moneycontrol.com/techCharts/indianMarketData?symbol=GOLD&resolution=1D',
        timeout=10, headers=headers
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(f"Data: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# ========= Try MCX from NSE/BSE like endpoint =========
print("\n=== MCX Direct API attempt ===")
try:
    r = requests.get(
        'https://www.mcxindia.com/backpage.aspx/GetLiveData',
        timeout=10, headers={**headers, 'Content-Type': 'application/json'}
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(f"Data: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# ========= Try precious metals API =========
print("\n=== METALS-API.COM ===")
try:
    r = requests.get(
        'https://metals-api.com/api/latest?access_key=demo&base=USD&symbols=XAU,XAG',
        timeout=10
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(f"Data: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# ========= Try free gold API =========
print("\n=== GOLDAPI.IO (free) ===")
try:
    r = requests.get(
        'https://www.goldapi.io/api/XAU/USD',
        timeout=10, headers={**headers, 'x-access-token': 'demo'}
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(f"Data: {r.text[:300]}")
except Exception as e:
    print(f"Error: {e}")
