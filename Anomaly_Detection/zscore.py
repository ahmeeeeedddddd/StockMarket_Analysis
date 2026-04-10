import statistics


VOL_WINDOW = 30
VOL_Z_THRESHOLD = 3.0

JUMP_WINDOW = 20
JUMP_STD_THRESHOLD = 3.0


def check_volume_spike(volumes: list, volume: float) -> dict | None:
    
    window = list(volumes)[-VOL_WINDOW:]
    if len(window) < VOL_WINDOW:
        return None

    mean = statistics.mean(window)
    std = statistics.pstdev(window)
    if std == 0:
        return None

    z = (volume - mean) / std
    if abs(z) < VOL_Z_THRESHOLD:
        return None

    return {
        "type": "VOLUME_SPIKE",
        "z_score": round(z, 3),
        "current_volume": volume,
        "rolling_mean_volume": round(mean, 2),
        "rolling_std_volume": round(std, 2),
        "threshold": VOL_Z_THRESHOLD,
        "severity": _severity_z(abs(z)),
    }


def check_price_jump(prices: list, price: float) -> dict | None:
    
    window = list(prices)[-JUMP_WINDOW:]
    if len(window) < JUMP_WINDOW:
        return None

    prior = window[:-1]
    if len(prior) < 2:
        return None

    mean = statistics.mean(prior)
    std = statistics.pstdev(prior)
    if std == 0:
        return None

    deviation_sigmas = abs(price - mean) / std
    if deviation_sigmas < JUMP_STD_THRESHOLD:
        return None

    return {
        "type": "PRICE_JUMP",
        "price": price,
        "prior_mean": round(mean, 4),
        "prior_std": round(std, 4),
        "deviation_sigmas": round(deviation_sigmas, 3),
        "threshold_sigmas": JUMP_STD_THRESHOLD,
        "severity": _severity_z(deviation_sigmas),
    }


def _severity_z(z: float) -> str:
    if z > 5:
        return "CRITICAL"
    if z > 4:
        return "HIGH"
    if z > 3:
        return "MEDIUM"
    return "LOW"