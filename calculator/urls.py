from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/calculate/", views.api_calculate, name="api_calculate"),
    path("api/capture-lead/", views.api_capture_lead, name="api_capture_lead"),
]