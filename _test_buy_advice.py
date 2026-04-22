"""Test the updated prediction with buy timing advice, MCX/COMEX, and crisis data."""
from app.ibja_rates import fetch_ibja_rates
from app.gold_predictor import predict_gold_price
from app.mcx_comex import fetch_market_data

ibja = fetch_ibja_rates()
market = fetch_market_data()
result = predict_gold_price(ibja, market)

if result.get('success'):
    print('=== BUY TIMING ADVICE ===')
    adv = result.get('buy_advice', {})
    print(f'Best Time: {adv.get("best_time")}')
    print(f'  Reason: {adv.get("best_time_reason")}')
    print(f'Direction: {adv.get("price_direction")}')
    print(f'Risk: {adv.get("risk_level")}')
    print()
    print(f'CHIT: {adv.get("chit_action")}')
    print(f'  {adv.get("chit_reason")}')
    print()
    print(f'INVEST: {adv.get("invest_action")}')
    print(f'  {adv.get("invest_reason")}')
    print()
    print(f'Savings Tip: {adv.get("savings_tip")}')
    if adv.get('premium_note'):
        print(f'Premium: {adv.get("premium_note")}')

    print('\n=== PRICE FORECAST ===')
    for k, v in result['predictions'].items():
        print(f'{k}: {v["current"]} -> {v["predicted"]} ({v["change"]:+.2f})')

    print('\n=== MCX/COMEX ===')
    mc = result.get('mcx_comex', {})
    if mc.get('comex_oz_usd'):
        print(f'COMEX: ${mc["comex_oz_usd"]}/oz (change: ${mc.get("comex_change_usd", 0)}, {mc.get("comex_change_pct", 0)}%)')
        print(f'  = Rs {mc["comex_inr_gram"]}/gram (@ USD/INR {mc["usd_inr"]})')
    if mc.get('silver_oz_usd'):
        print(f'Silver: ${mc["silver_oz_usd"]}/oz')
    if mc.get('mcx_price'):
        print(f'MCX proxy: Rs {mc["mcx_price"]}/gram (source: {mc.get("mcx_source")})')
    if mc.get('india_premium'):
        print(f'India Premium: Rs {mc["india_premium"]}/gram ({mc["india_premium_pct"]}%)')

    print('\n=== CRISIS ALERT ===')
    ca = result.get('crisis_alert')
    if ca:
        print(f'Level: {ca["level"]}')
        print(f'Message: {ca["message"]}')
    else:
        print('No crisis alert (normal volatility)')

    print(f'\n=== CRISIS SAMPLES ({len(result.get("crisis_samples", []))}) ===')
    for cs in result.get('crisis_samples', [])[:3]:
        print(f'  {cs["event"]} ({cs["date"]}): ${cs["gold_usd"]}/oz, Rs {cs["gold_inr_gram"]}/g, {cs["change_1w"]}')

    print('\n=== AM/PM PATTERN ===')
    print(f'AM->PM avg: {result.get("am_avg_change")}')
    print(f'PM->AM overnight: {result.get("pm_to_next_am")}')
else:
    print('Failed:', result.get('error'))
