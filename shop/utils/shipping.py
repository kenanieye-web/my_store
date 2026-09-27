from decimal import Decimal, ROUND_HALF_UP


def calculate_shipping_cost(items, shipping_method):
    """
    items: [(product, quantity), ...]
    shipping_method: كائن ShippingMethod
    """
    total_cbm = Decimal("0")
    for product, qty in items:
        total_cbm += product.get_cbm() * Decimal(qty)

    volume_cost = total_cbm * shipping_method.price_per_cbm
    final_cost = max(volume_cost, shipping_method.min_charge) + shipping_method.cost
    final_cost = final_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "total_cbm": total_cbm.quantize(Decimal("0.000001")),
        "cost": final_cost,
        "delivery_days": shipping_method.estimated_days,
        "method_name": shipping_method.name,
    }