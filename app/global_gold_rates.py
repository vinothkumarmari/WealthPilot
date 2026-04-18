"""
Global Gold & Silver Rates Scraper
Fetches live global gold/silver prices from livepriceofgold.com
Covers: 15 countries/currencies, multiple purities (24K–6K), units (gram/oz/tola/kg),
exchange rates in INR, and silver purities.
Caches results for 120 seconds. Falls back to cached data on errors.
"""
import re
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_cache = {'data': None, 'timestamp': 0, 'ttl': 120}

OZ_TO_GRAM = 31.1035
TOLA_TO_GRAM = 11.6638


def _pn(text):
    """Parse numeric value from text like '155.369 USD' or '14,396'."""
    if not text:
        return 0.0
    s = re.sub(r'[^\d.\-]', '', str(text).replace(',', ''))
    try:
        return float(s) if s else 0.0
    except (ValueError, TypeError):
        return 0.0


_COUNTRY_PATTERNS = [
    ('usa', 'USA', 'USD'),
    ('dubai', 'Dubai', 'AED'),
    ('saudi', 'Saudi Arabia', 'SAR'),
    ('singapore', 'Singapore', 'SGD'),
    ('canada', 'Canada', 'CAD'),
    ('australia', 'Australia', 'AUD'),
    ('qatar', 'Qatar', 'QAR'),
    ('british', 'UK', 'GBP'),
    ('kuwait', 'Kuwait', 'KWD'),
    ('euro', 'Europe', 'EUR'),
    ('pakistan', 'Pakistan', 'PKR'),
    ('india', 'India', 'INR'),
    ('malaysia', 'Malaysia', 'MYR'),
    ('philippines', 'Philippines', 'PHP'),
]


def _match_country(cell_text):
    """Match cell text to country info. Returns (name, currency) or None.
    Handles concatenated text like 'USAUnited States Dollar'."""
    t = cell_text.strip().lower()
    for key, name, cur in _COUNTRY_PATTERNS:
        if key in t:
            return name, cur
    return None


def _parse_spot(text):
    """Parse spot gold/silver prices from page text."""
    s = {}
    m = re.search(r'SPOT\s*GOLD\s*[▲▼⬆⬇]?\s*([\d,]+\.?\d*)\s*\$', text)
    if m:
        s['gold_oz'] = _pn(m.group(1))
    m = re.search(r'PER\s*GRAM\s*[▲▼⬆⬇]?\s*([\d,]+\.?\d*)\s*\$', text)
    if m:
        s['gold_gram'] = _pn(m.group(1))
    m = re.search(r'PER\s*TOLA\s*[▲▼⬆⬇]?\s*([\d,]+\.?\d*)\s*\$', text)
    if m:
        s['gold_tola'] = _pn(m.group(1))
    m = re.search(r'SPOT\s*SILVER\s*[▲▼⬆⬇]?\s*([\d,]+\.?\d*)\s*\$', text)
    if m:
        s['silver_oz'] = _pn(m.group(1))
    m = re.search(r'EURO/DOLLAR\s*[▲▼⬆⬇]?\s*([\d,]+\.?\d*)', text)
    if m:
        s['euro_dollar'] = _pn(m.group(1))

    # High / Low
    m = re.search(r'SPOT\s*GOLD.*?High:([\d,.]+).*?Low:([\d,.]+)', text, re.S)
    if m:
        s['gold_high'] = _pn(m.group(1))
        s['gold_low'] = _pn(m.group(2))
    m = re.search(r'SPOT\s*SILVER.*?High:([\d,.]+).*?Low:([\d,.]+)', text, re.S)
    if m:
        s['silver_high'] = _pn(m.group(1))
        s['silver_low'] = _pn(m.group(2))

    # % change
    m = re.search(r'SPOT\s*GOLD.*?([\-+]?\d+\.?\d*)\s*%', text)
    if m:
        s['gold_change_pct'] = _pn(m.group(1))
    m = re.search(r'SPOT\s*SILVER.*?([\-+]?\d+\.?\d*)\s*%', text)
    if m:
        s['silver_change_pct'] = _pn(m.group(1))

    # Derive missing values
    if s.get('gold_oz') and not s.get('gold_gram'):
        s['gold_gram'] = round(s['gold_oz'] / OZ_TO_GRAM, 3)
    if s.get('gold_gram') and not s.get('gold_tola'):
        s['gold_tola'] = round(s['gold_gram'] * TOLA_TO_GRAM, 2)
    if s.get('silver_oz'):
        s['silver_gram'] = round(s['silver_oz'] / OZ_TO_GRAM, 4)
        s['silver_tola'] = round(s.get('silver_gram', 0) * TOLA_TO_GRAM, 4)
        s['silver_kg'] = round(s.get('silver_gram', 0) * 1000, 2)
    return s


def _parse_country_tables(soup):
    """Extract global gold and silver price tables using table IDs."""
    gold = _parse_price_table(soup.find(id='indexgold'))
    silver = _parse_price_table(soup.find(id='indexsilver'), is_silver=True)
    return gold, silver


def _parse_price_table(table, is_silver=False):
    """Parse a country price table (gold or silver)."""
    if not table:
        return []
    data, seen = [], set()
    for row in table.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) < 3:
            continue
        m = _match_country(cells[0].get_text(strip=True))
        if m and m[0] not in seen:
            name, cur = m
            gram = _pn(cells[1].get_text())
            ounce = _pn(cells[2].get_text())
            if gram > 0:
                entry = {
                    'name': name, 'currency': cur,
                    'gram': gram, 'ounce': ounce,
                    'tola': round(gram * TOLA_TO_GRAM, 2),
                    'kg': round(gram * 1000, 2),
                }
                data.append(entry)
                seen.add(name)
    return data


def _parse_exchange_rates(soup):
    """Parse exchange-rate table from the India page.
    Cell format: 'USD/INR0.00%' in column 1, rate in column 2, bid/ask in 3/4."""
    rates = []
    for table in soup.find_all('table'):
        rows = table.find_all('tr')
        if not rows:
            continue
        # Check header for 'Currency' and 'Rate'
        header = rows[0].get_text(strip=True).lower()
        if 'currency' not in header or 'rate' not in header:
            continue
        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) < 3:
                continue
            # Find cell containing /INR (may have trailing %change)
            pair_text = ''
            for c in cells:
                t = c.get_text(strip=True)
                if '/INR' in t:
                    pair_text = t
                    break
            if not pair_text:
                continue
            # Extract pair: "USD/INR0.00%" → "USD/INR"
            m = re.match(r'([A-Z]{3}/INR)', pair_text)
            if not m:
                continue
            pair = m.group(1)
            # Rate is in the next cell after the pair cell
            rate_idx = next((i for i, c in enumerate(cells)
                             if '/INR' in c.get_text(strip=True)), -1)
            if rate_idx < 0 or rate_idx + 1 >= len(cells):
                continue
            rate = _pn(cells[rate_idx + 1].get_text())
            bid = _pn(cells[rate_idx + 2].get_text()) if rate_idx + 2 < len(cells) else 0
            ask = _pn(cells[rate_idx + 3].get_text()) if rate_idx + 3 < len(cells) else 0
            if rate > 0:
                rates.append({'pair': pair, 'rate': rate, 'bid': bid, 'ask': ask})
    return rates


def _parse_india_purity_tables(soup):
    """Parse India gold purity tables (Gram, Ounce, Tola, KG) with High/Low/Change."""
    purities = []
    karat_map = {
        '24k': '24K', '22k': '22K', '21k': '21K',
        '18k': '18K', '14k': '14K', '10k': '10K', '6k': '6K',
    }
    # Find the Gram table (has 'Gram/INR' header)
    for table in soup.find_all('table', class_='data-table-price'):
        rows = table.find_all('tr')
        if not rows:
            continue
        header = rows[0].get_text(strip=True).lower()
        if 'gram' not in header:
            continue
        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) < 5:
                continue
            label = cells[0].get_text(strip=True).lower()
            karat = None
            for k, v in karat_map.items():
                if k in label:
                    karat = v
                    break
            if not karat:
                continue
            price = _pn(cells[1].get_text())
            high = _pn(cells[2].get_text())
            low = _pn(cells[3].get_text())
            change = _pn(cells[4].get_text())
            if price > 0:
                purities.append({
                    'karat': karat, 'gram': price,
                    'high': high, 'low': low, 'change': change,
                })
        break
    return purities


def _derive_exchange_from_gold(global_gold):
    """Derive exchange rates from gold price table (USD as base)."""
    rates = []
    usd_g = next((d['gram'] for d in global_gold if d['currency'] == 'USD'), 0)
    if not usd_g:
        return rates
    seen = set()
    for d in global_gold:
        if d['currency'] == 'USD' or d['currency'] in seen:
            continue
        rate = round(d['gram'] / usd_g, 4)
        rates.append({
            'pair': f"USD/{d['currency']}",
            'rate': rate, 'bid': 0, 'ask': 0,
        })
        seen.add(d['currency'])
    return rates


def fetch_global_gold_rates():
    """Fetch and return global gold/silver rates + exchange data."""
    now = time.time()
    if _cache['data'] and (now - _cache['timestamp']) < _cache['ttl']:
        return _cache['data']

    try:
        import requests
        from bs4 import BeautifulSoup

        ua = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 WealthPilot/1.0'
        }

        # ── 1. Main page — spot prices + global tables ──
        r = requests.get('https://www.livepriceofgold.com/',
                         timeout=12, headers=ua)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')

        spot = _parse_spot(soup.get_text())
        global_gold, global_silver = _parse_country_tables(soup)

        # ── 2. India page — exchange rates, purities with high/low/change ──
        exchange_rates = []
        india_purity_data = []
        try:
            r2 = requests.get(
                'https://www.livepriceofgold.com/india-gold-price.html',
                timeout=10, headers=ua)
            r2.raise_for_status()
            soup2 = BeautifulSoup(r2.text, 'html.parser')
            exchange_rates = _parse_exchange_rates(soup2)
            india_purity_data = _parse_india_purity_tables(soup2)
        except Exception as e2:
            logger.warning('India page fetch failed: %s', e2)

        # Fall back to deriving exchange rates from gold table
        if not exchange_rates and global_gold:
            exchange_rates = _derive_exchange_from_gold(global_gold)

        # ── INR rate ──
        inr_rate = 0
        for ex in exchange_rates:
            if 'INR' in ex.get('pair', ''):
                inr_rate = ex['rate']
                break
        if not inr_rate and global_gold:
            inr_row = next((d for d in global_gold
                            if d['currency'] == 'INR'), None)
            usd_row = next((d for d in global_gold
                            if d['currency'] == 'USD'), None)
            if inr_row and usd_row and usd_row['gram']:
                inr_rate = round(inr_row['gram'] / usd_row['gram'], 4)

        # ── 3. Gold purities for India ──
        gold_purities = []
        base_24k = spot.get('gold_gram', 0)
        if base_24k and inr_rate:
            base_inr = base_24k * inr_rate
            # Build map of scraped high/low/change from India page
            scraped = {p['karat']: p for p in india_purity_data}
            for karat, pcode, frac, desc in [
                ('24K', '999', 0.999, 'Investment (Coins, Bars, ETF, SGB)'),
                ('22K', '916', 0.916, 'Jewelry Standard (Indian)'),
                ('21K', '875', 0.875, 'Gulf Standard'),
                ('18K', '750', 0.750, 'Daily Wear Jewelry'),
                ('14K', '585', 0.585, 'Affordable Jewelry'),
                ('10K', '417', 0.417, 'Budget Jewelry'),
                ('6K',  '250', 0.250, 'Fashion Jewelry'),
            ]:
                pg = round(base_inr * frac / 0.999, 2)
                sc = scraped.get(karat, {})
                # Prefer scraped price if available
                if sc.get('gram'):
                    pg = sc['gram']
                gold_purities.append({
                    'karat': karat, 'purity': pcode, 'desc': desc,
                    'gram': pg,
                    'ounce': round(pg * OZ_TO_GRAM, 2),
                    'tola': round(pg * TOLA_TO_GRAM, 2),
                    'kg': round(pg * 1000, 2),
                    'high': sc.get('high', 0),
                    'low': sc.get('low', 0),
                    'change': sc.get('change', 0),
                })

        # ── 4. Silver purities for India ──
        silver_purities = []
        base_silver = spot.get('silver_gram', 0)
        if base_silver and inr_rate:
            bs_inr = base_silver * inr_rate
            for name, pcode, frac in [
                ('Fine Silver', '999', 0.999),
                ('Britannia',   '958', 0.958),
                ('Sterling',    '925', 0.925),
                ('22K Silver',  '916', 0.916),
                ('21K Silver',  '875', 0.875),
                ('Jewelry',     '800', 0.800),
                ('14K Silver',  '585', 0.585),
            ]:
                pg = round(bs_inr * frac / 0.999, 2)
                silver_purities.append({
                    'name': name, 'purity': pcode,
                    'gram': pg,
                    'ounce': round(pg * OZ_TO_GRAM, 2),
                    'tola': round(pg * TOLA_TO_GRAM, 2),
                    'kg': round(pg * 1000, 2),
                })

        # ── 5. Global silver (derive from spot silver + exchange rates) ──
        if not global_silver and spot.get('silver_gram') and global_gold:
            usd_gg = next((d['gram'] for d in global_gold
                           if d['currency'] == 'USD'), 0)
            if usd_gg:
                sg = spot['silver_gram']
                so = spot.get('silver_oz', 0)
                for d in global_gold:
                    fx = d['gram'] / usd_gg
                    global_silver.append({
                        'name': d['name'], 'currency': d['currency'],
                        'gram': round(sg * fx, 3),
                        'ounce': round(so * fx, 2) if so else 0,
                        'tola': round(sg * fx * TOLA_TO_GRAM, 2),
                        'kg': round(sg * fx * 1000, 2),
                    })

        result = {
            'success': True,
            'spot': spot,
            'global_gold': global_gold,
            'global_silver': global_silver,
            'gold_purities': gold_purities,
            'silver_purities': silver_purities,
            'exchange_rates': exchange_rates,
            'last_updated': datetime.now().strftime('%d %b %Y, %H:%M:%S'),
            'source': 'LivePriceOfGold.com',
        }
        _cache['data'] = result
        _cache['timestamp'] = now
        return result

    except Exception as e:
        logger.error('Global gold rates error: %s', e)
        if _cache['data']:
            return _cache['data']
        return {
            'success': False, 'error': str(e),
            'spot': {}, 'global_gold': [], 'global_silver': [],
            'gold_purities': [], 'silver_purities': [],
            'exchange_rates': [],
            'last_updated': datetime.now().strftime('%d %b %Y, %H:%M:%S'),
            'source': 'Unavailable',
        }
