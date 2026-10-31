from common.exceptions import BusinessRuleError


def line_unit_price(product, variant=None, plan=None):
    """The plan's own product uses the plan price; anything else uses the
    product's sales price. A variant adds its extra price to either."""
    base = plan.price if plan and plan.product_id == product.id else product.sales_price
    extra = variant.extra_price if variant else 0
    return base + extra


def ensure_available(plan, on):
    if not plan.is_available(on):
        raise BusinessRuleError(f"{plan.name} isn't available on {on}.", "plan_unavailable")


def ensure_min_quantity(plan, lines):
    for line in lines:
        if line["product"].id == plan.product_id and line["quantity"] < plan.min_quantity:
            raise BusinessRuleError(f"{plan.name} needs a quantity of at least {plan.min_quantity}.", "below_min_quantity")
