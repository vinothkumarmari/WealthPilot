"""
Gold Price Predictor for WealthPilot
Uses IBJA historical data (~80 days) to predict gold prices 12 hours ahead.

Methods used:
1. Linear Regression (trend)
2. Weighted Moving Average (recent momentum)
3. Volatility analysis (confidence bands)
4. AM/PM intra-day pattern analysis
5. Mean reversion signal

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


def predict_gold_price(ibja_data):
    """
    Predict gold price 12 hours ahead using IBJA historical data.

    Args:
        ibja_data: dict from fetch_ibja_rates()

    Returns:
        dict with predictions for 24K, 22K, 18K gold and silver
    """
    if not ibja_data or not ibja_data.get('success'):
        return {'success': False, 'error': 'No IBJA data available'}

    gold_history = ibja_data.get('gold_history', [])
    silver_history = ibja_data.get('silver_history', [])
    am_pm_data = ibja_data.get('am_pm_data', [])

    if len(gold_history) < 5:
        return {'success': False, 'error': 'Insufficient historical data for prediction'}

    predictions = {}

    # --- Gold predictions for each purity ---
    for karat in ['24K', '22K', '18K']:
        prices = [h[karat] for h in gold_history if h.get(karat)]
        if len(prices) < 5:
            continue

        current = prices[-1]

        # 1. Linear regression trend (full history)
        slope, intercept, r_sq = _linear_regression(prices)
        # 12 hours = 0.5 day
        lr_prediction = intercept + slope * (len(prices) - 1 + 0.5)

        # 2. Short-term regression (last 14 days)
        short_prices = prices[-14:]
        s_slope, s_intercept, s_r_sq = _linear_regression(short_prices)
        short_prediction = s_intercept + s_slope * (len(short_prices) - 1 + 0.5)

        # 3. Weighted moving average momentum
        wma_7 = _weighted_moving_avg(prices, 7)
        wma_3 = _weighted_moving_avg(prices, 3)
        momentum = wma_3 - wma_7  # positive = upward momentum

        # 4. EMA signals
        ema_5 = _ema(prices, 5)
        ema_20 = _ema(prices, 20)
        ema_signal = 'bullish' if ema_5 > ema_20 else 'bearish'

        # 5. RSI
        rsi = _rsi(prices)

        # 6. Volatility
        vol = _volatility(prices)
        daily_vol_rupees = current * vol if vol else 0

        # 7. Support & Resistance
        support, resistance = _support_resistance(prices)

        # 8. AM/PM intra-day pattern
        am_pm_bias = 0
        if am_pm_data:
            diffs = []
            for row in am_pm_data[:7]:  # last 7 days
                am = row.get('am', {})
                pm = row.get('pm', {})
                key = 'gold_999' if karat == '24K' else ('gold_916' if karat == '22K' else 'gold_750')
                if am.get(key) and pm.get(key):
                    diffs.append(pm[key] - am[key])
            if diffs:
                am_pm_bias = sum(diffs) / len(diffs)

        # --- Combine predictions (weighted ensemble) ---
        # Long-term trend: 15%, Short-term trend: 35%, Momentum: 30%, AM/PM: 20%
        if r_sq > 0.5:
            w_lr = 0.15
        else:
            w_lr = 0.05  # low r² = don't trust long-term trend

        predicted = (
            w_lr * lr_prediction +
            0.35 * short_prediction +
            0.30 * (current + momentum * 0.5) +
            0.20 * (current + am_pm_bias)
        )

        # Normalize weights
        total_w = w_lr + 0.35 + 0.30 + 0.20
        predicted /= total_w

        # Mean reversion: if too far from WMA, pull back
        mean_dev = (predicted - wma_7) / wma_7 * 100 if wma_7 else 0
        if abs(mean_dev) > 2:
            predicted = predicted * 0.8 + wma_7 * 0.2

        predicted = round(predicted, 2)
        change = round(predicted - current, 2)
        change_pct = round((change / current * 100), 2) if current else 0

        # Confidence bands
        half_day_vol = daily_vol_rupees * 0.7  # ~70% of daily vol for 12hrs
        if half_day_vol < 1:
            half_day_vol = current * 0.003  # minimum 0.3% band

        # Direction assessment
        signals = {
            'trend': 1 if s_slope > 0 else -1,
            'momentum': 1 if momentum > 0 else -1,
            'ema': 1 if ema_signal == 'bullish' else -1,
            'rsi': -1 if rsi > 70 else (1 if rsi < 30 else 0),
        }
        bullish_count = sum(1 for v in signals.values() if v > 0)
        bearish_count = sum(1 for v in signals.values() if v < 0)

        if bullish_count >= 3:
            direction = 'Likely Up'
            confidence = 'High' if bullish_count == 4 else 'Moderate'
        elif bearish_count >= 3:
            direction = 'Likely Down'
            confidence = 'High' if bearish_count == 4 else 'Moderate'
        else:
            direction = 'Sideways'
            confidence = 'Low'

        predictions[karat] = {
            'current': current,
            'predicted': predicted,
            'change': change,
            'change_pct': change_pct,
            'direction': direction,
            'confidence': confidence,
            'range_low': round(predicted - half_day_vol, 2),
            'range_high': round(predicted + half_day_vol, 2),
            'rsi': round(rsi, 1),
            'ema_signal': ema_signal,
            'support': round(support, 2),
            'resistance': round(resistance, 2),
            'volatility_pct': round(vol * 100, 2),
            'trend_slope': round(s_slope, 4),
            'r_squared': round(s_r_sq, 3),
            'signals': signals,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
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
            'direction': 'Likely Up' if s_change > 0 else ('Likely Down' if s_change < 0 else 'Sideways'),
            'confidence': 'Moderate',
            'range_low': round(s_predicted - s_half_vol, 2),
            'range_high': round(s_predicted + s_half_vol, 2),
            'rsi': round(s_rsi, 1),
            'volatility_pct': round(s_vol * 100, 2),
        }

    # Prediction metadata
    now = datetime.now()
    target_time = now + timedelta(hours=12)

    return {
        'success': True,
        'predictions': predictions,
        'data_points': len(gold_history),
        'prediction_time': now.strftime('%d %b %Y, %I:%M %p'),
        'target_time': target_time.strftime('%d %b %Y, %I:%M %p'),
        'target_hours': 12,
        'disclaimer': 'Statistical estimate based on historical trends. Not financial advice. Actual prices may vary due to global events, market sentiment, and economic factors.',
    }
