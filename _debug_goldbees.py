"""Get GOLDBEES history to validate MCX proxy."""
import requests
from datetime import datetime

r = requests.get(
    'https://query1.finance.yahoo.com/v8/finance/chart/GOLDBEES.NS?interval=1d&range=1mo',
    timeout=10, headers={'User-Agent': 'Mozilla/5.0'}
)
data = r.json()
result = data['chart']['result'][0]
closes = result['indicators']['quote'][0]['close']
ts = result['timestamp']
print(f'GOLDBEES data points: {len(closes)}')
for t, c in zip(ts[-10:], closes[-10:]):
    if c:
        dt = datetime.fromtimestamp(t).strftime('%Y-%m-%d')
        # GOLDBEES NAV is ~1/100th of gold per gram price
        mcx_approx = round(c * 100, 2)
        print(f'  {dt}: GOLDBEES={c:.2f} INR => MCX approx ~{mcx_approx}/10g')
