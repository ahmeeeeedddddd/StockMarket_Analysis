import statistics


BB_WINDOW = 20
BB_STD_MULTIPLIER = 2.0


def check_bollinger_breach(prices: list, price: float) -> dict | None:
    
    window = list(prices)[-BB_WINDOW:]
    if len(window) < BB_WINDOW:
        return None

    mean = statistics.mean(window)
    std = statistics.pstdev(window)

    upper = mean + BB_STD_MULTIPLIER * std
    lower = mean - BB_STD_MULTIPLIER * std

    if price > upper:
        direction = "above upper band"
        severity = _severity(price, upper, std)
    elif price < lower:
        direction = "below lower band"
        severity = _severity(lower, price, std)
    else:
        return None

    return {
        "type": "BOLLINGER_BREACH",
        "direction": direction,
        "severity": severity,
        "price": price,
        "upper_band": round(upper, 4),
        "lower_band": round(lower, 4),
        "middle_band": round(mean, 4),
        "std": round(std, 4),
    }


def _severity(outer: float, inner: float, std: float) -> str:
    if std == 0:
        return "HIGH"
    excess = (outer - inner) / std
    if excess > 2:
        return "CRITICAL"
    if excess > 1:
        return "HIGH"
    return "MEDIUM"