import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RATES_FILE = os.path.join(BASE_DIR, "data", "rates_2026.json")

with open(RATES_FILE, "r") as f:
    RATE_DATA = json.load(f)


def get_all_markets():
    return {code: m["name"] for code, m in RATE_DATA["markets"].items()}


def get_all_bsps():
    return RATE_DATA["bsp_providers"]


def apply_tiered_pricing(volume, base_rate, tiers):
    if volume <= 0:
        return 0.0
    total_cost = 0.0
    remaining = volume
    for tier in tiers:
        tier_min = tier["min"]
        tier_max = tier["max"]
        discount = tier["discount"]
        effective_rate = base_rate * (1 - discount)
        if tier_max is None:
            tier_volume = remaining
        else:
            tier_capacity = tier_max - tier_min + 1
            tier_volume = min(remaining, tier_capacity)
        total_cost += tier_volume * effective_rate
        remaining -= tier_volume
        if remaining <= 0:
            break
    return round(total_cost, 6)


def calculate_bsp_fee(meta_cost, total_messages, bsp_key):
    bsp = RATE_DATA["bsp_providers"].get(bsp_key, RATE_DATA["bsp_providers"]["none"])
    model = bsp["model"]
    per_message_fee = bsp["per_message_fee"]
    markup_percent = bsp["markup_percent"]
    platform_fee = bsp["platform_fee"]
    if model == "flat_per_message":
        message_markup = total_messages * per_message_fee
    elif model == "percent_markup":
        message_markup = meta_cost * markup_percent
    else:
        message_markup = 0.0
    return round(message_markup, 4), round(platform_fee, 2)


def calculate_costs(
    country_code, bsp_key, custom_platform_fee,
    marketing_vol, utility_vol, auth_vol, service_vol,
    csw_percent, auth_international, fep_percent,
    audience_size=0, avg_order_value=0.0,
    abandoned_carts=0, conversion_rate=0.50,
):
    market = RATE_DATA["markets"].get(country_code)
    if not market:
        raise ValueError(f"Unknown country: {country_code}")

    bsp_data = RATE_DATA["bsp_providers"].get(bsp_key, RATE_DATA["bsp_providers"]["none"])
    util_tiers = RATE_DATA["utility_tiers"]
    auth_tiers = RATE_DATA["auth_tiers"]
    auth_intl_countries = RATE_DATA["auth_international_countries"]

    # Marketing — FEP deduction
    fep_ratio = max(0.0, min(1.0, fep_percent / 100.0))
    effective_marketing_vol = max(0, int(marketing_vol * (1 - fep_ratio)))
    meta_marketing_cost = effective_marketing_vol * market["marketing"]

    # Utility — CSW deduction + tiered pricing
    csw_ratio = max(0.0, min(1.0, csw_percent / 100.0))
    effective_utility_vol = max(0, int(utility_vol * (1 - csw_ratio)))
    meta_utility_cost = apply_tiered_pricing(effective_utility_vol, market["utility"], util_tiers)

    # Authentication — intl rate check + tiered pricing
    if auth_international and country_code in auth_intl_countries:
        auth_rate = market["auth_intl"] or market["auth"]
        auth_intl_applied = True
    else:
        auth_rate = market["auth"]
        auth_intl_applied = False
    meta_auth_cost = apply_tiered_pricing(auth_vol, auth_rate, auth_tiers)

    # Totals
    total_billed = effective_marketing_vol + effective_utility_vol + auth_vol
    meta_total = meta_marketing_cost + meta_utility_cost + meta_auth_cost
    bsp_markup, bsp_platform = calculate_bsp_fee(meta_total, total_billed, bsp_key)
    platform_fee = custom_platform_fee if custom_platform_fee > 0 else bsp_platform
    grand_total = meta_total + bsp_markup + platform_fee
    cost_per_msg = grand_total / total_billed if total_billed > 0 else 0.0

    # ROI
    roi_data = {}
    if audience_size > 0 and avg_order_value > 0:
        gross = audience_size * 0.95 * conversion_rate * avg_order_value
        roi_data = {
            "gross_revenue": round(gross, 2),
            "net_revenue": round(gross - grand_total, 2),
            "roi_percent": round((gross - grand_total) / grand_total * 100, 1) if grand_total > 0 else 0,
            "revenue_per_dollar": round(gross / grand_total, 2) if grand_total > 0 else 0,
        }

    # Cart recovery
    cart_data = {}
    if abandoned_carts > 0 and avg_order_value > 0:
        wa = abandoned_carts * 0.35 * avg_order_value
        em = abandoned_carts * 0.10 * avg_order_value
        cart_data = {
            "wa_revenue": round(wa, 2),
            "email_revenue": round(em, 2),
            "delta": round(wa - em, 2),
        }

    # Tips
    tips = generate_tips(
        country_code, market, bsp_key, bsp_data,
        marketing_vol, utility_vol, auth_vol,
        csw_ratio, fep_ratio, auth_intl_applied,
        meta_total, grand_total, bsp_markup,
        auth_rate, auth_intl_countries,
    )

    # Country comparison
    comparison = build_comparison(effective_marketing_vol, effective_utility_vol, auth_vol, util_tiers, auth_tiers)

    return {
        "country_code": country_code,
        "country_name": market["name"],
        "bsp_name": bsp_data["name"],
        "rates_applied": {
            "marketing": round(market["marketing"], 4),
            "utility": round(market["utility"], 4),
            "auth": round(auth_rate, 4),
            "auth_intl_applied": auth_intl_applied,
        },
        "volumes": {
            "marketing_input": marketing_vol,
            "marketing_effective": effective_marketing_vol,
            "utility_input": utility_vol,
            "utility_effective": effective_utility_vol,
            "auth": auth_vol,
            "service": service_vol,
            "total_billed": total_billed,
        },
        "costs": {
            "meta_marketing": round(meta_marketing_cost, 2),
            "meta_utility": round(meta_utility_cost, 2),
            "meta_auth": round(meta_auth_cost, 2),
            "meta_total": round(meta_total, 2),
            "bsp_markup": round(bsp_markup, 2),
            "platform_fee": round(platform_fee, 2),
            "grand_total": round(grand_total, 2),
            "cost_per_message": round(cost_per_msg, 6),
        },
        "savings": {
            "fep_saving": round(marketing_vol * market["marketing"] * fep_ratio, 2),
            "csw_saving": round(utility_vol * market["utility"] * csw_ratio, 2),
        },
        "tips": tips,
        "roi": roi_data,
        "cart_recovery": cart_data,
        "comparison": comparison,
    }


def generate_tips(
    country_code, market, bsp_key, bsp_data,
    marketing_vol, utility_vol, auth_vol,
    csw_ratio, fep_ratio, auth_intl_applied,
    meta_total, grand_total, bsp_markup,
    auth_rate, auth_intl_countries,
):
    tips = []

    if bsp_key not in ("none", "chatmaxima") and bsp_markup > 10:
        tips.append({
            "type": "warning",
            "title": "BSP markup is eating your budget",
            "body": f"{bsp_data['name']} adds ${bsp_markup:.2f}/month on top of Meta fees. "
                    f"Switching to a flat-fee provider like ChatMaxima ($19/month, zero markup) "
                    f"could save you ${bsp_markup - 19:.2f}/month (${(bsp_markup-19)*12:.0f}/year)."
        })

    if marketing_vol > 0 and fep_ratio < 0.30:
        saving = round(marketing_vol * market["marketing"] * 0.30, 2)
        tips.append({
            "type": "success",
            "title": "Unlock 72-hour free entry point windows",
            "body": f"Click-to-WhatsApp ads on Facebook/Instagram open a 72-hr free window "
                    f"for ALL message types including marketing. Moving 30% of your traffic "
                    f"through CTWA ads could save ~${saving:.2f}/month."
        })

    if utility_vol > 0 and csw_ratio < 0.40:
        saving = round(utility_vol * 0.40 * market["utility"], 2)
        tips.append({
            "type": "success",
            "title": "Use the 24-hour customer service window",
            "body": f"Utility templates sent inside an active customer service window are "
                    f"completely FREE. Routing ~40% of your {utility_vol:,} utility messages "
                    f"through inbound-triggered flows could save ~${saving:.2f}/month."
        })

    if auth_intl_applied and auth_vol > 0:
        domestic = market["auth"]
        premium_pct = round((auth_rate - domestic) / domestic * 100, 0)
        tips.append({
            "type": "danger",
            "title": "Auth-International rate trap detected!",
            "body": f"You are paying ${auth_rate:.4f} (international) vs ${domestic:.4f} "
                    f"(domestic) — a {premium_pct:.0f}% premium. Register a local WABA "
                    f"via a regional BSP in {market['name']} to eliminate this surcharge."
        })

    if country_code in ("DE", "FR") and marketing_vol > 500:
        india_cost = marketing_vol * RATE_DATA["markets"]["IN"]["marketing"]
        current_cost = marketing_vol * market["marketing"]
        tips.append({
            "type": "info",
            "title": "Geography massively affects your cost",
            "body": f"Your {marketing_vol:,} marketing messages cost ${current_cost:.2f} "
                    f"in {market['name']}. The same campaign to Indian users costs "
                    f"${india_cost:.2f} — {round(current_cost/india_cost, 1)}× cheaper."
        })

    if utility_vol > 80000:
        tips.append({
            "type": "info",
            "title": "Volume discounts are active",
            "body": f"Your {utility_vol:,} utility messages qualify for Meta's tiered "
                    f"discounts. Tier 2 (80K+) = 5% off, Tier 3 (750K+) = 10% off, "
                    f"up to 25% off at 6M+ messages/month."
        })

    if not tips:
        tips.append({
            "type": "info",
            "title": "Optimise your message mix",
            "body": "Keep support replies inside the 24-hr service window (always free), "
                    "classify transactional messages as Utility instead of Marketing, "
                    "and use Click-to-WhatsApp ads to unlock free 72-hr windows."
        })

    return tips


def build_comparison(marketing_vol, utility_vol, auth_vol, util_tiers, auth_tiers):
    codes = ["IN", "CO", "TR", "US", "MX", "BR", "ZA", "GB", "ES", "IT", "DE", "FR"]
    results = []
    for code in codes:
        m = RATE_DATA["markets"].get(code)
        if not m:
            continue
        total = (
            marketing_vol * m["marketing"] +
            apply_tiered_pricing(utility_vol, m["utility"], util_tiers) +
            apply_tiered_pricing(auth_vol, m["auth"], auth_tiers)
        )
        results.append({
            "code": code,
            "name": m["name"],
            "total": round(total, 2),
        })
    return sorted(results, key=lambda x: x["total"])