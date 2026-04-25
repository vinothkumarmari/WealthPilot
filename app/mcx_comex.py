"""
MCX & COMEX Gold Data Fetcher for MyWealthPilot
Fetches live gold data from Yahoo Finance API (COMEX GC=F, GOLDBEES.NS).
Provides international price comparison, India premium, and crisis awareness.
Caches results for 120 seconds.
"""
import re
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_cache = {'mcx': None, 'comex': None, 'timestamp': 0, 'ttl': 120}

OZ_TO_GRAM = 31.1035

# --- Historical crisis data: how gold reacted during major events ---
CRISIS_SAMPLES = [
    # COVID-19 pandemic (2020)
    {'event': 'COVID-19 Lockdown', 'date': '2020-03-24', 'gold_usd': 1660, 'gold_inr_gram': 4180, 'change_1w': '+8.2%',
     'context': 'India lockdown announced. Gold spiked as markets crashed. Stocks fell 13% same day.'},
    {'event': 'COVID-19 Peak Fear', 'date': '2020-08-07', 'gold_usd': 2075, 'gold_inr_gram': 5650, 'change_1w': '+3.5%',
     'context': 'Gold hit all-time high $2,075/oz as second COVID wave fears grew. Best safe-haven rally in decades.'},
    {'event': 'COVID-19 Vaccine Approval', 'date': '2020-11-09', 'gold_usd': 1850, 'gold_inr_gram': 4950, 'change_1w': '-4.8%',
     'context': 'Pfizer vaccine announced 90% effective. Gold dropped sharply as risk appetite returned.'},
    # Russia-Ukraine War (2022)
    {'event': 'Russia Invades Ukraine', 'date': '2022-02-24', 'gold_usd': 1940, 'gold_inr_gram': 5180, 'change_1w': '+3.1%',
     'context': 'War began. Gold surged as investors fled to safety. Crude oil spiked above $100/barrel.'},
    {'event': 'Ukraine War Escalation', 'date': '2022-03-08', 'gold_usd': 2043, 'gold_inr_gram': 5500, 'change_1w': '+5.3%',
     'context': 'Nuclear threat fears. Gold near all-time high. Russian sanctions pushed demand for safe havens.'},
    # Israel-Hamas War (2023)
    {'event': 'Israel-Hamas Conflict', 'date': '2023-10-09', 'gold_usd': 1860, 'gold_inr_gram': 5700, 'change_1w': '+3.4%',
     'context': 'Surprise Hamas attack on Israel. Gold spiked on Middle East instability and oil supply fears.'},
    {'event': 'Israel-Hamas Escalation', 'date': '2023-10-27', 'gold_usd': 2005, 'gold_inr_gram': 6100, 'change_1w': '+2.8%',
     'context': 'Ground invasion of Gaza. Gold crossed $2,000 as wider regional conflict fears grew.'},
    # US Banking Crisis (2023)
    {'event': 'SVB Bank Collapse', 'date': '2023-03-13', 'gold_usd': 1910, 'gold_inr_gram': 5350, 'change_1w': '+6.1%',
     'context': 'Silicon Valley Bank collapsed. Banking panic spread globally. Gold surged as bank stocks crashed.'},
    # India-specific: Demonetization (2016)
    {'event': 'India Demonetization', 'date': '2016-11-08', 'gold_usd': 1275, 'gold_inr_gram': 2900, 'change_1w': '-2.5%',
     'context': 'PM Modi announced demonetization. Cash crunch initially depressed gold demand, then premium spiked in physical market.'},
    # US-China Trade War (2019)
    {'event': 'US-China Trade War Peak', 'date': '2019-08-07', 'gold_usd': 1500, 'gold_inr_gram': 3650, 'change_1w': '+4.2%',
     'context': 'China devalued yuan in retaliation. Gold broke $1,500 for first time since 2013. Safe-haven demand surged.'},
]


def _yahoo_chart(symbol, range_str='1d', interval='1d'):
    """Fetch data from Yahoo Finance chart API."""
    try:
        import requests
        r = requests.get(
            f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={range_str}',
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        if r.status_code == 200:
            data = r.json()
            result = data.get('chart', {}).get('result', [None])[0]
            return result
    except Exception as e:
        logger.debug(f'Yahoo Finance {symbol}: {e}')
    return None


def fetch_mcx_gold():
    """Fetch MCX Gold data via GOLDBEES ETF (Nippon India Gold ETF on NSE).
    GOLDBEES tracks physical gold price in India, closely correlated with MCX."""
    result = {
        'gold_per_gram': 0,
        'gold_change': 0,
        'gold_change_pct': 0,
        'gold_history': [],
        'success': False,
        'source': 'GOLDBEES.NS (MCX proxy)',
    }

    data = _yahoo_chart('GOLDBEES.NS', '1mo', '1d')
    if not data:
        return result

    meta = data.get('meta', {})
    price = meta.get('regularMarketPrice', 0)
    prev_close = meta.get('chartPreviousClose', 0)

    if price:
        # GOLDBEES 1 unit ≈ 0.01g of gold (approx). Derive per-gram price.
        # Actual MCX gold per gram ≈ GOLDBEES × 121-122 (varies with premium)
        # We use GOLDBEES as a directional proxy, not exact MCX price.
        result['gold_etf_price'] = round(price, 2)
        result['gold_per_gram'] = round(price * 121.5, 2)  # approximate MCX per gram
        result['success'] = True

        if prev_close:
            change = price - prev_close
            result['gold_change'] = round(change, 2)
            result['gold_change_pct'] = round(change / prev_close * 100, 2)

    # Get 1-month history for trend
    closes = data.get('indicators', {}).get('quote', [{}])[0].get('close', [])
    timestamps = data.get('timestamp', [])
    for ts, cl in zip(timestamps, closes):
        if cl:
            result['gold_history'].append({
                'date': datetime.fromtimestamp(ts).strftime('%Y-%m-%d'),
                'price': round(cl * 121.5, 2),
                'etf_price': round(cl, 2),
            })

    return result


def fetch_comex_gold():
    """Fetch COMEX Gold futures (GC=F) and Silver (SI=F) from Yahoo Finance."""
    result = {
        'gold_oz_usd': 0,
        'gold_change_usd': 0,
        'gold_change_pct': 0,
        'silver_oz_usd': 0,
        'usd_inr': 0,
        'gold_inr_gram': 0,
        'gold_history_usd': [],
        'success': False,
        'source': 'COMEX (Yahoo Finance)',
    }

    # --- Gold futures GC=F ---
    gold_data = _yahoo_chart('GC=F', '1mo', '1d')
    if gold_data:
        meta = gold_data.get('meta', {})
        price = meta.get('regularMarketPrice', 0)
        prev_close = meta.get('chartPreviousClose', 0)

        if price:
            result['gold_oz_usd'] = round(price, 2)
            if prev_close:
                result['gold_change_usd'] = round(price - prev_close, 2)
                result['gold_change_pct'] = round((price - prev_close) / prev_close * 100, 2)

        # History
        closes = gold_data.get('indicators', {}).get('quote', [{}])[0].get('close', [])
        timestamps = gold_data.get('timestamp', [])
        for ts, cl in zip(timestamps, closes):
            if cl:
                result['gold_history_usd'].append({
                    'date': datetime.fromtimestamp(ts).strftime('%Y-%m-%d'),
                    'price_usd': round(cl, 2),
                })

    # --- Silver futures SI=F ---
    silver_data = _yahoo_chart('SI=F', '1d', '1d')
    if silver_data:
        s_price = silver_data.get('meta', {}).get('regularMarketPrice', 0)
        if s_price:
            result['silver_oz_usd'] = round(s_price, 2)

    # --- USD/INR rate ---
    # Primary: exchangerate API (reliable, no scraping)
    try:
        import requests
        r = requests.get('https://open.er-api.com/v6/latest/USD', timeout=8)
        if r.status_code == 200:
            rates = r.json().get('rates', {})
            inr = rates.get('INR', 0)
            if inr:
                result['usd_inr'] = round(inr, 2)
    except Exception as e:
        logger.debug(f'Exchangerate API: {e}')

    # Fallback: Google Finance
    if not result['usd_inr']:
        try:
            import requests
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            r = requests.get('https://www.google.com/finance/quote/USD-INR', timeout=8, headers=headers)
            if r.status_code == 200:
                m = re.search(r'data-last-price="([\d.]+)"', r.text)
                if m:
                    result['usd_inr'] = round(float(m.group(1)), 2)
        except Exception as e:
            logger.debug(f'Google Finance USD/INR: {e}')

    if not result['usd_inr']:
        result['usd_inr'] = 93.5  # fallback

    # Convert COMEX gold to INR per gram
    if result['gold_oz_usd']:
        result['gold_inr_gram'] = round(
            result['gold_oz_usd'] * result['usd_inr'] / OZ_TO_GRAM, 2
        )
        result['success'] = True

    return result


def fetch_market_data():
    """Fetch both MCX and COMEX data. Returns combined dict with crisis samples."""
    now = time.time()
    if _cache['mcx'] and _cache['comex'] and (now - _cache['timestamp']) < _cache['ttl']:
        return {'mcx': _cache['mcx'], 'comex': _cache['comex'], 'crisis_samples': CRISIS_SAMPLES}

    mcx = fetch_mcx_gold()
    comex = fetch_comex_gold()

    _cache['mcx'] = mcx
    _cache['comex'] = comex
    _cache['timestamp'] = now

    return {'mcx': mcx, 'comex': comex, 'crisis_samples': CRISIS_SAMPLES}
