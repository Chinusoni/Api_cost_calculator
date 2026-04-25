from django.db import models
from django.utils import timezone


class LeadCapture(models.Model):

    BUSINESS_SIZE_CHOICES = [
        ("solo",       "Solo / Freelancer"),
        ("small",      "Small (1–10 employees)"),
        ("medium",     "Medium (11–100 employees)"),
        ("large",      "Large (101–500 employees)"),
        ("enterprise", "Enterprise (500+)"),
    ]

    INDUSTRY_CHOICES = [
        ("ecommerce",   "E-commerce / Retail"),
        ("saas",        "SaaS / Technology"),
        ("fintech",     "Fintech / Banking"),
        ("healthcare",  "Healthcare"),
        ("logistics",   "Logistics / Delivery"),
        ("education",   "Education"),
        ("agency",      "Marketing Agency"),
        ("other",       "Other"),
    ]

    name          = models.CharField(max_length=200)
    email         = models.EmailField()
    phone         = models.CharField(max_length=30, blank=True)
    company       = models.CharField(max_length=200, blank=True)
    business_size = models.CharField(max_length=20, choices=BUSINESS_SIZE_CHOICES, blank=True)
    industry      = models.CharField(max_length=30, choices=INDUSTRY_CHOICES, blank=True)

    country_code  = models.CharField(max_length=5, blank=True)
    country_name  = models.CharField(max_length=100, blank=True)
    bsp_key       = models.CharField(max_length=50, blank=True)
    marketing_vol = models.IntegerField(default=0)
    utility_vol   = models.IntegerField(default=0)
    auth_vol      = models.IntegerField(default=0)
    service_vol   = models.IntegerField(default=0)
    grand_total   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    meta_total    = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at    = models.DateTimeField(default=timezone.now)
    ip_address    = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Lead"
        verbose_name_plural = "Leads"

    def __str__(self):
        return f"{self.name} — {self.email}"