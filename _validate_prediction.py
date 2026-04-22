"""Quick validation of gold prediction vs live IBJA data."""
from app.ibja_rates import fetch_ibja_rates
from app.gold_predictor import predict_gold_price

data = fetch_ibja_rates()
if not data.get('success'):
    print('IBJA fetch failed:', data.get('error'))
    exit()

print('=== LIVE IBJA PRICES ===')
print(f'Source: {data["source"]}')
print(f'Updated: {data["last_updated"]}')
for k in ['24K', '22K', '18K']:
    g = data['gold'][k]
    print(f'  {k}: Rs {g["price_per_gram"]}/gram (Rs {g["price_per_10g"]}/10g)')
print(f'  Silver: Rs {data["silver"]["price_per_gram"]}/gram')

gh = data.get('gold_history', [])
print(f'\nHistory: {len(gh)} data points')
print('Last 7 days (24K per gram):')
for h in gh[-7:]:
    print(f'  {h["date"]}: Rs {h["24K"]}')

# Daily changes
if len(gh) >= 2:
    print('\nDaily changes (24K):')
    for i in range(-5, 0):
        if abs(i) < len(gh):
            prev = gh[i-1]['24K']
            curr = gh[i]['24K']
            chg = curr - prev
            pct = (chg/prev*100) if prev else 0
            print(f'  {gh[i]["date"]}: {prev} -> {curr} ({chg:+.2f}, {pct:+.2f}%)')

# AM/PM pattern
am_pm = data.get('am_pm_data', [])
if am_pm:
    print(f'\nAM/PM data: {len(am_pm)} days')
    for row in am_pm[:3]:
        am = row.get('am', {})
        pm = row.get('pm', {})
        if am.get('gold_999') and pm.get('gold_999'):
            diff = pm['gold_999'] - am['gold_999']
            print(f'  {row["date"]}: AM={am["gold_999"]} PM={pm["gold_999"]} diff={diff:+.2f}')

# Prediction
result = predict_gold_price(data)
print('\n=== PREDICTIONS (12 hours ahead) ===')
if result.get('success'):
    print(f'From: {result["prediction_time"]}')
    print(f'To:   {result["target_time"]}')
    for k, v in result['predictions'].items():
        print(f'\n{k}:')
        print(f'  Current:   Rs {v["current"]}')
        print(f'  Predicted: Rs {v["predicted"]}')
        print(f'  Change:    Rs {v["change"]} ({v["change_pct"]}%)')
        print(f'  Range:     Rs {v["range_low"]} - {v["range_high"]}')
        print(f'  Direction: {v["direction"]} (Confidence: {v.get("confidence", "N/A")})')
        if 'rsi' in v:
            print(f'  RSI: {v["rsi"]}, Volatility: {v["volatility_pct"]}%')
        if 'support' in v:
            print(f'  Support: {v["support"]}, Resistance: {v["resistance"]}')
else:
    print('Prediction failed:', result.get('error'))
