import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .calculators import calculate_costs, get_all_markets, get_all_bsps
from .models import LeadCapture


def index(request):
    markets = get_all_markets()
    bsps = get_all_bsps()
    context = {
        "markets": json.dumps(markets),
        "bsps": json.dumps({k: v["name"] for k, v in bsps.items()}),
    }
    return render(request, "calculator/index.html", context)


@csrf_exempt
@require_POST
def api_calculate(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        result = calculate_costs(
            country_code=data.get("country_code", "US"),
            bsp_key=data.get("bsp_key", "wati"),
            custom_platform_fee=float(data.get("custom_platform_fee", 0)),
            marketing_vol=int(data.get("marketing_vol", 0)),
            utility_vol=int(data.get("utility_vol", 0)),
            auth_vol=int(data.get("auth_vol", 0)),
            service_vol=int(data.get("service_vol", 0)),
            csw_percent=float(data.get("csw_percent", 0)),
            auth_international=bool(data.get("auth_international", False)),
            fep_percent=float(data.get("fep_percent", 0)),
            audience_size=int(data.get("audience_size", 0)),
            avg_order_value=float(data.get("avg_order_value", 0)),
            abandoned_carts=int(data.get("abandoned_carts", 0)),
            conversion_rate=float(data.get("conversion_rate", 0.5)),
        )
        return JsonResponse({"success": True, "data": result})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_POST
def api_capture_lead(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    ip = x_forwarded.split(",")[0] if x_forwarded else request.META.get("REMOTE_ADDR")

    lead = LeadCapture.objects.create(
        name=data.get("name", ""),
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        company=data.get("company", ""),
        business_size=data.get("business_size", ""),
        industry=data.get("industry", ""),
        country_code=data.get("country_code", ""),
        country_name=data.get("country_name", ""),
        bsp_key=data.get("bsp_key", ""),
        marketing_vol=int(data.get("marketing_vol", 0)),
        utility_vol=int(data.get("utility_vol", 0)),
        auth_vol=int(data.get("auth_vol", 0)),
        service_vol=int(data.get("service_vol", 0)),
        grand_total=float(data.get("grand_total", 0)),
        meta_total=float(data.get("meta_total", 0)),
        ip_address=ip,
    )
    return JsonResponse({"success": True, "lead_id": lead.id})