"""
IBJA Live Rates Scraper
Fetches live gold, silver & platinum rates from ibjarates.com
Includes: current prices, AM/PM table history, chart history (~80 days).
All data is real — sourced directly from IBJA. No fabricated history.
Caches results for 60 seconds to stay close to real-time.
"""
import re
import json
import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

_cache = {'data': None, 'timestamp': 0, 'ttl': 60}


def fetch_ibja_rates():
    """Fetch live rates from ibjarates.com. Returns cached data if fresh."""
    now = time.time()
    if _cache['data'] and (now - _cache['timestamp']) < _cache['ttl']:
        return _cache['data']

    try:
        import requests
        from bs4 import BeautifulSoup

        r = requests.get(
            'https://ibjarates.com/',
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) WealthPilot/1.0'}
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')

        # --- Current gold rates per gram from h3 tags ---
        h3s = soup.find_all('h3')
        gram_prices = []
        for h3 in h3s:
            text = h3.get_text(strip=True).replace(',', '').replace('₹', '')
            m = re.search(r'(\d+)\s*\(1\s*Gram\)', text)
            if m:
                gram_prices.append(float(m.group(1)))

        gold_999 = gram_prices[0] if len(gram_prices) > 0 else None
        gold_995 = gram_prices[1] if len(gram_prices) > 1 else None
        gold_916 = gram_prices[2] if len(gram_prices) > 2 else None
        gold_750 = gram_prices[3] if len(gram_prices) > 3 else None
        gold_585 = gram_prices[4] if len(gram_prices) > 4 else None

        # --- Chart data from hidden fields (HdnGold/HdnSilver — ~80 data points) ---
        chart_gold = []
        chart_silver = []

        hdn_gold = soup.find(id='HdnGold')
        if hdn_gold and hdn_gold.get('value'):
            try:
                gd = json.loads(hdn_gold['value'])
                labels = gd.get('labels', [])
                p999 = gd.get('purity999', [])
                p916 = gd.get('purity916', [])
                for i, lbl in enumerate(labels):
                    try:
                        dt = datetime.strptime(lbl, '%d/%m/%Y')
                        v999 = float(p999[i]) / 10 if i < len(p999) else None  # per 10g → per gram
                        v916 = float(p916[i]) / 10 if i < len(p916) else None
                        v750 = round(v999 * 0.750 / 0.999, 2) if v999 else None
                        chart_gold.append({
                            'date': dt.strftime('%d %b'),
                            'full_date': dt.strftime('%d/%m/%Y'),
                            '24K': round(v999, 2) if v999 else None,
                            '22K': round(v916, 2) if v916 else None,
                            '18K': v750,
                        })
                    except (ValueError, IndexError):
                        continue
            except (json.JSONDecodeError, KeyError):
                pass

        hdn_silver = soup.find(id='HdnSilver')
        if hdn_silver and hdn_silver.get('value'):
            try:
                sd = json.loads(hdn_silver['value'])
                labels = sd.get('labels', [])
                rates = sd.get('silverRate', [])
                for i, lbl in enumerate(labels):
                    try:
                        dt = datetime.strptime(lbl, '%d/%m/%Y')
                        price = float(rates[i]) / 1000 if i < len(rates) else None  # per kg → per gram
                        chart_silver.append({
                            'date': dt.strftime('%d %b'),
                            'full_date': dt.strftime('%d/%m/%Y'),
                            'price': round(price, 2) if price else None,
                        })
                    except (ValueError, IndexError):
                        continue
            except (json.JSONDecodeError, KeyError):
                pass

        # --- AM/PM table history (all purities + silver + platinum) ---
        history_am = []
        history_pm = []

        def _parse_rate_table(table_el):
            """Parse an IBJA rate table into a list of dicts."""
            entries = []
            if not table_el:
                return entries
            for row in table_el.find_all('tr'):
                cells = [c.get_text(strip=True) for c in row.find_all(['th', 'td'])]
                if not cells or not re.match(r'\d{2}/\d{2}/\d{4}', cells[0]):
                    continue
                if len(cells) >= 8:
                    try:
                        entries.append({
                            'date': cells[0],
                            'gold_999': float(cells[1].replace(',', '')),
                            'gold_995': float(cells[2].replace(',', '')),
                            'gold_916': float(cells[3].replace(',', '')),
                            'gold_750': float(cells[4].replace(',', '')),
                            'gold_585': float(cells[5].replace(',', '')),
                            'silver_999': float(cells[6].replace(',', '')),
                            'platinum_999': float(cells[7].replace(',', '')) if len(cells) > 7 else None,
                        })
                    except (ValueError, IndexError):
                        continue
            return entries

        # Use tab IDs to reliably distinguish AM from PM tables
        tab_am = soup.find(id='tab-am')
        tab_pm = soup.find(id='tab-pm')
        if tab_am:
            am_table = tab_am.find('table') if tab_am.name != 'table' else tab_am
            history_am = _parse_rate_table(am_table) if am_table else _parse_rate_table(tab_am)
        if tab_pm:
            pm_table = tab_pm.find('table') if tab_pm.name != 'table' else tab_pm
            history_pm = _parse_rate_table(pm_table) if pm_table else _parse_rate_table(tab_pm)

        # Fallback: if tab IDs not found, scan all tables by order
        if not history_am and not history_pm:
            tables_found = 0
            for table in soup.find_all('table'):
                rows = table.find_all('tr')
                has_header = False
                for row in rows:
                    cells = [c.get_text(strip=True) for c in row.find_all(['th', 'td'])]
                    if 'Silver 999' in cells or 'Platinum 999' in cells:
                        has_header = True
                        break
                if has_header:
                    entries = _parse_rate_table(table)
                    if entries:
                        tables_found += 1
                        if tables_found == 1:
                            history_am = entries
                        elif tables_found == 2:
                            history_pm = entries

        # Current silver & platinum from table
        silver_per_kg = None
        platinum_per_10g = None
        if history_pm:
            silver_per_kg = history_pm[0].get('silver_999')
            platinum_per_10g = history_pm[0].get('platinum_999')
        elif history_am:
            silver_per_kg = history_am[0].get('silver_999')
            platinum_per_10g = history_am[0].get('platinum_999')

        silver_per_gram = round(silver_per_kg / 1000, 2) if silver_per_kg else None

        # --- Build chart histories ---
        # Day history: use chart data (~80 points) or fall back to table
        gold_history_day = chart_gold if chart_gold else []
        silver_history_day = chart_silver if chart_silver else []

        # If chart data is empty, build from table
        if not gold_history_day:
            entries = history_pm if history_pm else history_am
            for entry in reversed(entries):
                try:
                    d = datetime.strptime(entry['date'], '%d/%m/%Y')
                    gold_history_day.append({
                        'date': d.strftime('%d %b'),
                        '24K': round(entry['gold_999'] / 10, 2),
                        '22K': round(entry['gold_916'] / 10, 2),
                        '18K': round(entry['gold_750'] / 10, 2),
                    })
                    silver_history_day.append({
                        'date': d.strftime('%d %b'),
                        'price': round(entry['silver_999'] / 1000, 2),
                    })
                except (ValueError, KeyError):
                    continue

        # --- AM/PM comparison (convert to per-gram for display) ---
        am_pm_data = []
        # Build a merged view: dates that have both AM and PM
        am_by_date = {e['date']: e for e in history_am}
        pm_by_date = {e['date']: e for e in history_pm}
        all_dates = sorted(set(list(am_by_date.keys()) + list(pm_by_date.keys())),
                           key=lambda d: datetime.strptime(d, '%d/%m/%Y'), reverse=True)
        for dt_str in all_dates[:10]:  # last 10 dates
            am = am_by_date.get(dt_str)
            pm = pm_by_date.get(dt_str)
            row = {'date': dt_str}
            if am:
                row['am'] = {
                    'gold_999': round(am['gold_999'] / 10, 2),
                    'gold_995': round(am['gold_995'] / 10, 2),
                    'gold_916': round(am['gold_916'] / 10, 2),
                    'gold_750': round(am['gold_750'] / 10, 2),
                    'gold_585': round(am['gold_585'] / 10, 2),
                    'silver': round(am['silver_999'] / 1000, 2),
                    'platinum': round(am['platinum_999'] / 10, 2) if am.get('platinum_999') else None,
                }
            if pm:
                row['pm'] = {
                    'gold_999': round(pm['gold_999'] / 10, 2),
                    'gold_995': round(pm['gold_995'] / 10, 2),
                    'gold_916': round(pm['gold_916'] / 10, 2),
                    'gold_750': round(pm['gold_750'] / 10, 2),
                    'gold_585': round(pm['gold_585'] / 10, 2),
                    'silver': round(pm['silver_999'] / 1000, 2),
                    'platinum': round(pm['platinum_999'] / 10, 2) if pm.get('platinum_999') else None,
                }
            am_pm_data.append(row)

        # --- Current rates for AM/PM header table ---
        current_am = None
        current_pm = None
        # The first table with AM/PM single row is the "today" summary
        am_pm_table = soup.find('table')
        if am_pm_table:
            rows = am_pm_table.find_all('tr')
            for row in rows:
                cells = [c.get_text(strip=True) for c in row.find_all(['th', 'td'])]
                if len(cells) >= 3:
                    if 'AM' in cells[0].upper():
                        current_am = cells[1] if len(cells) > 1 else None
                        current_pm = cells[2] if len(cells) > 2 else None

        # Previous day rates for accurate change calculation (use PM table, row index 1 = yesterday)
        prev_day = {}
        prev_source = history_pm if len(history_pm) >= 2 else (history_am if len(history_am) >= 2 else [])
        if len(prev_source) >= 2:
            prev = prev_source[1]  # index 0 = latest, index 1 = previous day
            prev_day = {
                'gold_999': round(prev['gold_999'] / 10, 2),
                'gold_995': round(prev['gold_995'] / 10, 2),
                'gold_916': round(prev['gold_916'] / 10, 2),
                'gold_750': round(prev['gold_750'] / 10, 2),
                'gold_585': round(prev['gold_585'] / 10, 2),
                'silver': round(prev['silver_999'] / 1000, 2),
                'platinum': round(prev.get('platinum_999', 0) / 10, 2) if prev.get('platinum_999') else None,
            }

        result = {
            'success': True,
            'source': 'IBJA (ibjarates.com)',
            'last_updated': datetime.now().strftime('%d %b %Y, %I:%M %p'),
            'gold': {
                '24K': {
                    'price_per_gram': gold_999,
                    'price_per_10g': round(gold_999 * 10, 2) if gold_999 else None,
                    'purity': '999',
                },
                '22K': {
                    'price_per_gram': gold_916,
                    'price_per_10g': round(gold_916 * 10, 2) if gold_916 else None,
                    'purity': '916',
                },
                '18K': {
                    'price_per_gram': gold_750,
                    'price_per_10g': round(gold_750 * 10, 2) if gold_750 else None,
                    'purity': '750',
                },
                '995': {
                    'price_per_gram': gold_995,
                    'price_per_10g': round(gold_995 * 10, 2) if gold_995 else None,
                    'purity': '995',
                },
                '585': {
                    'price_per_gram': gold_585,
                    'price_per_10g': round(gold_585 * 10, 2) if gold_585 else None,
                    'purity': '585',
                },
            },
            'silver': {
                'price_per_gram': silver_per_gram,
                'price_per_kg': silver_per_kg,
            },
            'platinum': {
                'price_per_10g': platinum_per_10g,
                'price_per_gram': round(platinum_per_10g / 10, 2) if platinum_per_10g else None,
            },
            'gold_history': gold_history_day,
            'silver_history': silver_history_day,
            'am_pm_data': am_pm_data,
            'prev_day': prev_day,
            'chart_data_points': len(chart_gold),
        }

        _cache['data'] = result
        _cache['timestamp'] = now
        return result

    except Exception as e:
        logger.error(f'IBJA scrape failed: {e}')
        if _cache['data']:
            return _cache['data']
        return {
            'success': False,
            'error': str(e),
            'source': 'IBJA (ibjarates.com)',
            'last_updated': datetime.now().strftime('%d %b %Y, %I:%M %p'),
        }
