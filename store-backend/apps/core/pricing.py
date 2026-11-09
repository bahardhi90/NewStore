"""The ONE place where prices are calculated. Money is always int (Toman)."""

ROUNDING_STEP = 1_000


def calc_final_price(base_price: int, discount_percent: int) -> int:
    """base * (100 - discount) / 100, rounded down to the nearest 1,000 Toman.

    Without a discount the base price is returned unchanged.
    """
    base_price = int(base_price)
    discount_percent = int(discount_percent or 0)
    if discount_percent <= 0:
        return base_price
    raw = base_price * (100 - discount_percent) // 100
    return (raw // ROUNDING_STEP) * ROUNDING_STEP


def toman_to_rial(amount_toman: int) -> int:
    return int(amount_toman) * 10
