"""Debug MCX/COMEX scraping to fix regex patterns."""
import requests
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# ========= COMEX: Google Finance =========
print("=== GOOGLE FINANCE GC=F ===")
try:
    r = requests.get('https://www.google.com/finance/quote/GC=F:CME', timeout=10, headers=headers)
    print(f"Status: {r.status_code}, URL: {r.url}")
    m1 = re.findall(r'data-last-price="([^"]+)"', r.text)
    print(f"data-last-price: {m1}")
    m2 = re.findall(r'class="YMlKec fxKbKc">([^<]+)', r.text)
    print(f"YMlKec: {m2}")
    # Look for any dollar amounts
    m3 = re.findall(r'\$[\d,]+\.\d{2}', r.text[:5000])
    print(f"Dollar amounts: {m3[:5]}")
except Exception as e:
    print(f"Error: {e}")

# ========= Try Yahoo Finance =========
print("\n=== YAHOO FINANCE GC=F ===")
try:
    r = requests.get('https://finance.yahoo.com/quote/GC=F/', timeout=10, headers=headers)
    print(f"Status: {r.status_code}")
    m = re.findall(r'"regularMarketPrice":\{"raw":([\d.]+)', r.text)
    print(f"regularMarketPrice: {m}")
    m2 = re.findall(r'data-value="([\d,.]+)"', r.text[:5000])
    print(f"data-value: {m2[:5]}")
except Exception as e:
    print(f"Error: {e}")

# ========= Try metals-api alternative =========
print("\n=== GOLDPRICE.ORG ===")
try:
    r = requests.get('https://goldprice.org/', timeout=10, headers=headers)
    print(f"Status: {r.status_code}")
    m = re.findall(r'id="gpxtickerLeft_price"[^>]*>([\d,.]+)', r.text)
    print(f"Ticker price: {m}")
except Exception as e:
    print(f"Error: {e}")

# ========= Try livegoldprice =========
print("\n=== LIVEPRICEOFGOLD.COM ===")
try:
    r = requests.get('https://www.livepriceofgold.com/', timeout=10, headers=headers)
    print(f"Status: {r.status_code}")
    # Look for gold price patterns
    m = re.findall(r'[\d,]+\.?\d*\s*(?:USD|usd|\$)', r.text[:5000])
    print(f"USD prices: {m[:5]}")
    m2 = re.findall(r'(?:gold|Gold|GOLD).*?([\d,]+\.?\d+)', r.text[:5000])
    print(f"Gold prices: {m2[:5]}")
except Exception as e:
    print(f"Error: {e}")

# ========= Try metal price API - forex-metal =========
print("\n=== METALS.LIVE (API) ===")
try:
    r = requests.get('https://api.metals.live/v1/spot', timeout=10, headers=headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(f"Data: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# ========= MCX: moneycontrol =========
print("\n=== MONEYCONTROL MCX ===")
try:
    r = requests.get('https://www.moneycontrol.com/commodity/gold-price.html', timeout=10, headers=headers)
    print(f"Status: {r.status_code}")
    # Look for price in page
    m = re.findall(r'mcx.*?(?:₹|Rs\.?|INR)?\s*([\d,]+\.?\d*)', r.text[:5000], re.I)
    print(f"MCX prices: {m[:5]}")
    # Try broader pattern
    m2 = re.findall(r'(?:spot|futures?).*?([\d,]+\.?\d+)', r.text[:5000], re.I)
    print(f"Spot/futures: {m2[:5]}")
except Exception as e:
    print(f"Error: {e}")

# ========= MCX: goodreturns =========
print("\n=== GOODRETURNS MCX ===")
try:
    r = requests.get('https://www.goodreturns.in/gold-rates/', timeout=10, headers=headers)
    print(f"Status: {r.status_code}")
    m = re.findall(r'MCX.*?([\d,]+)', r.text[:10000], re.I)
    print(f"MCX prices: {m[:5]}")
    # Broader: any gold price
    m2 = re.findall(r'(?:22|24)\s*(?:Carat|karat|K).*?([\d,]+)', r.text[:10000], re.I)
    print(f"22/24K prices: {m2[:5]}")
except Exception as e:
    print(f"Error: {e}")

# ========= USD/INR =========
print("\n=== USD/INR ===")
try:
    r = requests.get('https://www.google.com/finance/quote/USD-INR', timeout=10, headers=headers)
    print(f"Status: {r.status_code}")
    m = re.findall(r'data-last-price="([^"]+)"', r.text)
    print(f"data-last-price: {m}")
except Exception as e:
    print(f"Error: {e}")

# ========= Try exchangerate-api =========
print("\n=== EXCHANGERATE-API ===")
try:
    r = requests.get('https://open.er-api.com/v6/latest/USD', timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"USD/INR: {data.get('rates', {}).get('INR', 'N/A')}")
except Exception as e:
    print(f"Error: {e}")
