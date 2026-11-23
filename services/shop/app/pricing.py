def total_stable(amount: float, promo: dict | None) -> float:
    percent = promo["percent"] if promo else 0
    return round(amount * (1 - percent / 100), 2)


def total_with_required_promo(amount: float, promo: dict | None) -> float:
    percent = promo["percent"]
    return round(amount * (1 - percent / 100), 2)


def calculator(version: str):
    return total_with_required_promo if version == "2.4.0" else total_stable
