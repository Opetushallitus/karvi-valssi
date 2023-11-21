from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from kyselyt import views


router_v1 = routers.DefaultRouter()
router_v1.register(r"kyselykerta", views.KyselykertaViewSet)
router_v1.register(r"vastaa", views.VastaaViewSet, basename="vastaa")
router_v1.register(r"tempvastaus", views.TempVastausViewSet, basename="tempvastaus")


urlpatterns = [
    path(settings.BASE_URL, include([
        path("admin/", admin.site.urls),
        path("api/v1/", include(router_v1.urls)),
        path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
        path("api/v1/scale/", views.ScaleViewSet.as_view()),
        path("api/v1/malfunction-message/get-active/", views.MalfunctionMessageViewSet.as_view()),
        path("health/", views.HealthViewSet.as_view()),
        path("health-db/", views.HealthDbViewSet.as_view()),
    ]))
]
