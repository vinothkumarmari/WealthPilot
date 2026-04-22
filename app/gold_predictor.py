"""
Gold Price Predictor for WealthPilot
Analyzes IBJA, MCX & COMEX data to predict gold prices 12 hours ahead.
Provides actionable buy timing advice for gold chit payments and investments.

Methods: Linear Regression, WMA, EMA, RSI, Volatility, AM/PM pattern, MCX-COMEX spread.
Disclaimer: Statistical estimate only — not financial advice.
"""
import math
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def _linear_regression(prices):
    """Simple linear regression. Returns (slope, intercept, r_squared)."""
    n = len(prices)
    if n < 3:
        return 0, prices[-1] if prices else 0, 0

    x_vals = list(range(n))
    x_mean = sum(x_vals) / n
    y_mean = sum(prices) / n

    ss_xy = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, prices))
    ss_xx = sum((x - x_mean) ** 2 for x in x_vals)
    ss_yy = sum((y - y_mean) ** 2 for y in prices)

    if ss_xx == 0:
        return 0, y_mean, 0

    slope = ss_xy / ss_xx
    intercept = y_mean - slope * x_mean

    if ss_yy == 0:
        r_squared = 1.0
    else:
        r_squared = (ss_xy ** 2) / (ss_xx * ss_yy)

    return slope, intercept, r_squared


def _weighted_moving_avg(prices, window=7):
    """Weighted moving average giving more weight to recent prices."""
    if not prices:
        return 0
    subset = prices[-window:]
    weights = list(range(1, len(subset) + 1))
    return sum(p * w for p, w in zip(subset, weights)) / sum(weights)


def _ema(prices, span=10):
    """Exponential moving average."""
    if not prices:
        return 0
    alpha = 2 / (span + 1)
    ema_val = prices[0]
    for p in prices[1:]:
        ema_val = alpha * p + (1 - alpha) * ema_val
    return ema_val


def _rsi(prices, period=14):
    """Relative Strength Index (0-100)."""
    if len(prices) < period + 1:
        return 50  # neutral

    gains = []
    losses = []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _volatility(prices, window=14):
    """Calculate standard deviation of daily returns."""
    if len(prices) < window + 1:
        return 0
    returns = [(prices[i] - prices[i - 1]) / prices[i - 1]
               for i in range(1, len(prices)) if prices[i - 1] != 0]
    if not returns:
        return 0
    subset = returns[-window:]
    mean_r = sum(subset) / len(subset)
    variance = sum((r - mean_r) ** 2 for r in subset) / len(subset)
    return math.sqrt(variance)


def _support_resistance(prices, window=20):
    """Find support and resistance levels from recent prices."""
    if len(prices) < window:
        window = len(prices)
    recent = prices[-window:]
    support = min(recent)
    resistance = max(recent)
    return support, resistance


def predict_gold_price(ibja_data, market_data=None):
    """
    Predict gold price 12 hours ahead using IBJA + MCX/COMEX data.
    Provides actionable buy/wait timing for gold chit and investment.

    Args:
        ibja_data: dict from fetch_ibja_rates()
        market_data: dict from mcx_comex.fetch_market_data() (optional)

    Returns:
        dict with predictions, buy timing advice, MCX/COMEX analysis
    """
    if not ibja_data or not ibja_data.get('success'):
        return {'success': False, 'error': 'No IBJA data available'}

    gold_history = ibja_data.get('gold_history', [])
    silver_history = ibja_data.get('silver_history', [])
    am_pm_data = ibja_data.get('am_pm_data', [])

    if len(gold_history) < 5:
        return {'success': False, 'error': 'Insufficient historical data for prediction'}

    now = datetime.now()
    predictions = {}

    # --- Analyze AM/PM intra-day pattern (key for timing) ---
    am_avg_change = 0  # avg AM→PM change
    pm_to_next_am = 0  # avg PM→next AM change
    am_pm_pattern = []
    if am_pm_data and len(am_pm_data) >= 2:
        am_diffs = []
        overnight_diffs = []
        for i, row in enumerate(am_pm_data[:7]):
            am = row.get('am', {})
            pm = row.get('pm', {})
            if am.get('gold_999') and pm.get('gold_999'):
                intraday = pm['gold_999'] - am['gold_999']
                am_diffs.append(intraday)
                am_pm_pattern.append({
                    'date': row['date'],
                    'am_price': am['gold_999'],
                    'pm_price': pm['gold_999'],
                    'intraday_change': round(intraday, 2),
                })
            # Overnight: this PM → next day AM
            if i + 1 < len(am_pm_data):
                next_row = am_pm_data[i + 1]
                next_am = next_row.get('am', {})
                if pm.get('gold_999') and next_am.get('gold_999'):
                    overnight = next_am['gold_999'] - pm['gold_999']
                    overnight_diffs.append(overnight)
        if am_diffs:
            am_avg_change = sum(am_diffs) / len(am_diffs)
        if overnight_diffs:
            pm_to_next_am = sum(overnight_diffs) / len(overnight_diffs)

    # --- Gold predictions for 24K ---
    for karat in ['24K', '22K', '18K']:
        prices = [h[karat] for h in gold_history if h.get(karat)]
        if len(prices) < 5:
            continue

        current = prices[-1]

        # Regression
        slope, intercept, r_sq = _linear_regression(prices)
        lr_prediction = intercept + slope * (len(prices) - 1 + 0.5)

        short_prices = prices[-14:]
        s_slope, s_intercept, s_r_sq = _linear_regression(short_prices)
        short_prediction = s_intercept + s_slope * (len(short_prices) - 1 + 0.5)

        # Momentum
        wma_7 = _weighted_moving_avg(prices, 7)
        wma_3 = _weighted_moving_avg(prices, 3)
        momentum = wma_3 - wma_7

        # EMA
        ema_5 = _ema(prices, 5)
        ema_20 = _ema(prices, 20)

        # RSI & Volatility
        rsi = _rsi(prices)
        vol = _volatility(prices)
        daily_vol_rupees = current * vol if vol else 0
        support, resistance = _support_resistance(prices)

        # AM/PM bias for this karat
        karat_am_bias = 0
        if am_pm_data:
            key = 'gold_999' if karat == '24K' else ('gold_916' if karat == '22K' else 'gold_750')
            diffs = []
            for row in am_pm_data[:7]:
                am = row.get('am', {})
                pm = row.get('pm', {})
                if am.get(key) and pm.get(key):
                    diffs.append(pm[key] - am[key])
            if diffs:
                karat_am_bias = sum(diffs) / len(diffs)

        # Ensemble prediction
        w_lr = 0.15 if r_sq > 0.5 else 0.05
        predicted = (
            w_lr * lr_prediction +
            0.35 * short_prediction +
            0.30 * (current + momentum * 0.5) +
            0.20 * (current + karat_am_bias)
        )
        total_w = w_lr + 0.35 + 0.30 + 0.20
        predicted /= total_w

        # Mean reversion
        mean_dev = (predicted - wma_7) / wma_7 * 100 if wma_7 else 0
        if abs(mean_dev) > 2:
            predicted = predicted * 0.8 + wma_7 * 0.2

        predicted = round(predicted, 2)
        change = round(predicted - current, 2)
        change_pct = round((change / current * 100), 2) if current else 0

        # Range bands
        half_day_vol = daily_vol_rupees * 0.7
        if half_day_vol < 1:
            half_day_vol = current * 0.003

        predictions[karat] = {
            'current': current,
            'predicted': predicted,
            'change': change,
            'change_pct': change_pct,
            'range_low': round(predicted - half_day_vol, 2),
            'range_high': round(predicted + half_day_vol, 2),
            'rsi': round(rsi, 1),
            'volatility_pct': round(vol * 100, 2),
            'support': round(support, 2),
            'resistance': round(resistance, 2),
            'ema_5': round(ema_5, 2),
            'ema_20': round(ema_20, 2),
            'wma_7': round(wma_7, 2),
            'trend_slope': round(s_slope, 4),
            'r_squared': round(s_r_sq, 3),
            'momentum': round(momentum, 2),
        }

    # --- Silver prediction ---
    silver_prices = [h['price'] for h in silver_history if h.get('price')]
    if len(silver_prices) >= 5:
        s_current = silver_prices[-1]
        s_slope, s_intercept, s_r_sq = _linear_regression(silver_prices[-14:])
        s_wma = _weighted_moving_avg(silver_prices, 7)
        s_momentum = _weighted_moving_avg(silver_prices, 3) - s_wma
        s_rsi = _rsi(silver_prices)
        s_vol = _volatility(silver_prices)

        s_predicted = 0.4 * (s_intercept + s_slope * (min(14, len(silver_prices)) - 0.5)) + \
                      0.35 * (s_current + s_momentum * 0.5) + \
                      0.25 * s_current
        s_predicted = round(s_predicted, 2)
        s_change = round(s_predicted - s_current, 2)
        s_half_vol = s_current * s_vol * 0.7 if s_vol else s_current * 0.005

        predictions['Silver'] = {
            'current': s_current,
            'predicted': s_predicted,
            'change': s_change,
            'change_pct': round((s_change / s_current * 100), 2) if s_current else 0,
            'range_low': round(s_predicted - s_half_vol, 2),
            'range_high': round(s_predicted + s_half_vol, 2),
            'rsi': round(s_rsi, 1),
            'volatility_pct': round(s_vol * 100, 2),
        }

    # --- MCX / COMEX analysis ---
    mcx_comex = {}
    if market_data:
        mcx = market_data.get('mcx', {})
        comex = market_data.get('comex', {})

        if mcx.get('success') and mcx.get('gold_per_gram'):
            mcx_comex['mcx_price'] = mcx['gold_per_gram']
            mcx_comex['mcx_source'] = mcx.get('source', 'MCX')

        if comex.get('success') and comex.get('gold_oz_usd'):
            mcx_comex['comex_oz_usd'] = comex['gold_oz_usd']
            mcx_comex['comex_inr_gram'] = comex['gold_inr_gram']
            mcx_comex['usd_inr'] = comex['usd_inr']
            mcx_comex['comex_source'] = comex.get('source', 'COMEX')
            mcx_comex['comex_change_usd'] = comex.get('gold_change_usd', 0)
            mcx_comex['comex_change_pct'] = comex.get('gold_change_pct', 0)
            mcx_comex['silver_oz_usd'] = comex.get('silver_oz_usd', 0)

        # India premium = IBJA price - COMEX converted price
        ibja_24k = predictions.get('24K', {}).get('current', 0)
        comex_inr = mcx_comex.get('comex_inr_gram', 0)
        if ibja_24k and comex_inr:
            premium = ibja_24k - comex_inr
            premium_pct = (premium / comex_inr * 100) if comex_inr else 0
            mcx_comex['india_premium'] = round(premium, 2)
            mcx_comex['india_premium_pct'] = round(premium_pct, 2)

    # --- BUY TIMING ADVICE ---
    buy_advice = _generate_buy_advice(predictions, am_pm_pattern, am_avg_change, pm_to_next_am, now, mcx_comex)

    # --- CRISIS / HIGH VOLATILITY DETECTION ---
    crisis_alert = None
    p24 = predictions.get('24K', {})
    if p24:
        vol_pct = p24.get('volatility_pct', 0)
        daily_change = abs(p24.get('change_pct', 0))
        # Check COMEX 1-day swing
        comex_swing = abs(mcx_comex.get('comex_change_pct', 0))
        # Crisis-like conditions: high volatility + large price swings
        if vol_pct > 2.0 or daily_change > 1.5 or comex_swing > 2.0:
            crisis_alert = {
                'level': 'HIGH' if (vol_pct > 3 or daily_change > 3 or comex_swing > 4) else 'ELEVATED',
                'volatility': vol_pct,
                'daily_swing': daily_change,
                'comex_swing': comex_swing,
                'message': 'Unusual market volatility detected. '
                           'During crises (wars, pandemics, banking collapses), gold prices can swing 3-8% in a single day. '
                           'See historical crisis data below for context.',
                'advice': 'Avoid large gold purchases during high volatility. '
                          'If paying gold chit, pay the minimum. For investments, wait 2-3 days for stability.'
                          if vol_pct > 2.5 else
                          'Moderate volatility. Proceed with caution for large purchases. '
                          'Gold chit payments are fine at current levels.',
            }

    # Crisis samples from market_data
    crisis_samples = market_data.get('crisis_samples', []) if market_data else []

    target_time = now + timedelta(hours=12)

    return {
        'success': True,
        'predictions': predictions,
        'buy_advice': buy_advice,
        'am_pm_pattern': am_pm_pattern,
        'am_avg_change': round(am_avg_change, 2),
        'pm_to_next_am': round(pm_to_next_am, 2),
        'mcx_comex': mcx_comex,
        'crisis_alert': crisis_alert,
        'crisis_samples': crisis_samples,
        'data_points': len(gold_history),
        'prediction_time': now.strftime('%d %b %Y, %I:%M %p'),
        'target_time': target_time.strftime('%d %b %Y, %I:%M %p'),
        'target_hours': 12,
        'disclaimer': 'Statistical estimate based on IBJA, MCX & COMEX trends. Not financial advice. During crises (wars, pandemics), gold can swing 3-8% in a day — our model detects abnormal volatility and adjusts advice accordingly.',
    }


def _generate_buy_advice(predictions, am_pm_pattern, am_avg_change, pm_to_next_am, now, mcx_comex):
    """
    Generate actionable buy/wait advice for gold chit payment and investment.
    Analyzes: time-of-day pattern, predicted direction, volatility, premium.
    """
    p24 = predictions.get('24K', {})
    if not p24:
        return {}

    current = p24['current']
    predicted = p24['predicted']
    change = p24['change']
    change_pct = p24['change_pct']
    rsi = p24.get('rsi', 50)
    vol = p24.get('volatility_pct', 0)
    support = p24.get('support', 0)
    wma = p24.get('wma_7', current)

    hour = now.hour
    is_market_hours = 9 <= hour < 23  # MCX trading hours
    is_before_midnight = hour >= 20
    is_early_morning = hour < 9

    advice = {
        'chit_action': '',      # "Pay now" / "Wait till morning" etc
        'chit_reason': '',
        'invest_action': '',    # "Buy today" / "Wait for dip" etc
        'invest_reason': '',
        'best_time': '',        # "Before 11:59 PM today" / "Tomorrow before 9 AM"
        'best_time_reason': '',
        'price_direction': '',  # concise: "Prices expected to rise ₹X by morning"
        'risk_level': '',       # "Low" / "Moderate" / "High"
        'savings_tip': '',
    }

    # --- Determine price direction ---
    if change > 0:
        advice['price_direction'] = f'Prices expected to rise ~₹{abs(change):.0f}/gram (~{abs(change_pct):.2f}%) in next 12 hours'
    elif change < 0:
        advice['price_direction'] = f'Prices expected to drop ~₹{abs(change):.0f}/gram (~{abs(change_pct):.2f}%) in next 12 hours'
    else:
        advice['price_direction'] = 'Prices expected to remain stable in next 12 hours'

    # --- Risk level ---
    if vol > 1.5:
        advice['risk_level'] = 'High'
    elif vol > 0.8:
        advice['risk_level'] = 'Moderate'
    else:
        advice['risk_level'] = 'Low'

    # --- AM/PM pattern insight ---
    # Historically, AM prices are usually lower than PM (gold tends to rise during trading)
    am_usually_lower = am_avg_change > 0  # PM > AM means AM is cheaper
    overnight_drops = pm_to_next_am < 0   # PM to next AM usually drops

    # --- CHIT PAYMENT advice ---
    # Gold chit: user pays monthly, gets gold at day's rate. We advise which day/time to pay.
    if change > 0:
        # Price going up → pay sooner to lock lower rate
        if is_before_midnight:
            advice['chit_action'] = 'Pay your gold chit NOW'
            advice['chit_reason'] = f'Price is expected to rise by ₹{abs(change):.0f}/gram by tomorrow. Paying before 11:59 PM locks today\'s lower rate.'
        elif is_early_morning:
            advice['chit_action'] = 'Pay your gold chit NOW (before 9 AM)'
            advice['chit_reason'] = f'Morning prices are usually ₹{abs(am_avg_change):.0f}/gram lower than evening. Pay before market opens for best rate.'
        else:
            advice['chit_action'] = 'Pay your gold chit TODAY'
            advice['chit_reason'] = f'Price is trending up. Delaying will likely cost ₹{abs(change):.0f}/gram more.'
    elif change < 0:
        # Price going down → wait for lower rate
        if is_before_midnight:
            advice['chit_action'] = 'Wait till tomorrow morning'
            advice['chit_reason'] = f'Price is expected to drop ₹{abs(change):.0f}/gram by morning. Pay tomorrow before 9 AM for a better rate.'
        else:
            advice['chit_action'] = 'Wait for a better rate'
            advice['chit_reason'] = f'Prices are trending down. You may save ₹{abs(change):.0f}/gram by waiting.'
    else:
        advice['chit_action'] = 'Pay anytime today'
        advice['chit_reason'] = 'Prices are stable. No significant advantage in timing.'

    # --- INVESTMENT advice ---
    near_support = (current - support) / current * 100 < 2 if support else False
    near_resistance = (p24.get('resistance', 0) - current) / current * 100 < 1 if p24.get('resistance') else False
    oversold = rsi < 35
    overbought = rsi > 70

    if oversold or near_support:
        advice['invest_action'] = 'Good time to BUY gold'
        reasons = []
        if oversold:
            reasons.append(f'RSI at {rsi:.0f} indicates oversold conditions — likely to bounce up')
        if near_support:
            reasons.append(f'Price near support level (₹{support:,.0f}) — historically bounces from here')
        advice['invest_reason'] = '. '.join(reasons) + '.'
    elif overbought or near_resistance:
        advice['invest_action'] = 'WAIT before buying more gold'
        reasons = []
        if overbought:
            reasons.append(f'RSI at {rsi:.0f} indicates overbought — a correction is likely')
        if near_resistance:
            reasons.append(f'Price near resistance (₹{p24.get("resistance", 0):,.0f}) — may face selling pressure')
        advice['invest_reason'] = '. '.join(reasons) + '.'
    elif change < 0 and abs(change_pct) > 0.3:
        advice['invest_action'] = 'Consider BUYING on the dip'
        advice['invest_reason'] = f'Prices expected to drop ₹{abs(change):.0f}/gram. A dip is a buying opportunity if you\'re investing for the long term.'
    elif change > 0 and abs(change_pct) > 0.3:
        advice['invest_action'] = 'Buy NOW or wait for next dip'
        advice['invest_reason'] = f'Prices rising. If you need gold soon, buy now. Otherwise wait for a pullback day.'
    else:
        advice['invest_action'] = 'Steady — SIP/chit as usual'
        advice['invest_reason'] = 'No strong signal. Continue regular gold SIP or chit as planned.'

    # --- Best time to act ---
    if am_usually_lower and overnight_drops:
        advice['best_time'] = 'Tomorrow before 9:00 AM'
        advice['best_time_reason'] = f'AM prices are historically ₹{abs(am_avg_change):.0f}/gram cheaper than PM. Overnight prices tend to drop ₹{abs(pm_to_next_am):.0f}/gram.'
    elif am_usually_lower:
        advice['best_time'] = 'Any morning before 10:00 AM'
        advice['best_time_reason'] = f'AM prices average ₹{abs(am_avg_change):.0f}/gram lower than PM closing.'
    elif change > 0:
        advice['best_time'] = 'Before 11:59 PM today'
        advice['best_time_reason'] = 'Prices are rising — buying sooner locks a lower rate.'
    else:
        advice['best_time'] = 'Tomorrow morning'
        advice['best_time_reason'] = 'Prices are expected to be lower by morning.'

    # --- Savings tip ---
    price_10g = current * 10
    if change > 0:
        savings_per_10g = abs(change) * 10
        advice['savings_tip'] = f'Buying NOW vs tomorrow could save ~₹{savings_per_10g:,.0f} per 10 grams'
    elif change < 0:
        savings_per_10g = abs(change) * 10
        advice['savings_tip'] = f'Waiting could save ~₹{savings_per_10g:,.0f} per 10 grams'
    else:
        advice['savings_tip'] = 'Minimal price movement expected — timing won\'t matter much today'

    # --- India premium insight ---
    if mcx_comex.get('india_premium'):
        prem = mcx_comex['india_premium']
        if prem > 200:
            advice['premium_note'] = f'India premium is high (₹{prem:,.0f}/gram over international price). Consider Gold ETF/SGB for lower premium.'
        elif prem < 50:
            advice['premium_note'] = f'India premium is low (₹{prem:,.0f}/gram). Good time for physical gold purchase.'
        else:
            advice['premium_note'] = f'India premium is normal at ₹{prem:,.0f}/gram over international price.'

    return advice
