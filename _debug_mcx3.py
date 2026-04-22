"""Find MCX Gold ticker on Yahoo Finance."""
import requests, json
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

tickers = ['GOLD.NS', 'GOLDM.NS', 'GOLDGUINEA.NS', 'GC=F', 'GOLDBEES.NS', 'GOLDBEES.BO']
for t in tickers:
    try:
        r = requests.get(
            f'https://query1.finance.yahoo.com/v8/finance/chart/{t}?interval=1d&range=5d',
            timeout=8, headers=headers
        )
        if r.status_code == 200:
            data = r.json()
            result = data.get('chart', {}).get('result', [{}])[0]
            meta = result.get('meta', {})
            price = meta.get('regularMarketPrice')
            currency = meta.get('currency', '?')
            name = meta.get('shortName', meta.get('symbol', ''))
            if price:
                print(f'{t}: {price} {currency} ({name})')
                closes = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
                recent = [round(c, 2) for c in closes[-5:] if c]
                print(f'  Last 5 closes: {recent}')
            else:
                print(f'{t}: no price data')
        else:
            print(f'{t}: HTTP {r.status_code}')
    except Exception as e:
        print(f'{t}: {e}')
