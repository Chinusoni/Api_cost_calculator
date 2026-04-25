from django.contrib import admin
from .models import LeadCapture


@admin.register(LeadCapture)
class LeadCaptureAdmin(admin.ModelAdmin):
    list_display  = ["name", "email", "company", "country_name", "grand_total", "created_at"]
    list_filter   = ["industry", "business_size", "country_code", "created_at"]
    search_fields = ["name", "email", "company"]
    ordering      = ["-created_at"]