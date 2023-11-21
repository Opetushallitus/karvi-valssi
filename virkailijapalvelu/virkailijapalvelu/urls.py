from django.contrib import admin
from django.urls import path, include
from django.conf import settings

from rest_framework import routers

from kyselyt import views


router_v1 = routers.DefaultRouter()
router_v1.register(r"tyontekija", views.TyontekijaViewSet, basename="tyontekija")
router_v1.register(r"kyselysend", views.KyselySendViewSet, basename="kyselysend")
router_v1.register(r"indikaattori", views.IndikaattoriViewSet, basename="indikaattori")
router_v1.register(r"kyselykerta", views.KyselykertaViewSet, basename="kyselykerta")
router_v1.register(r"kysymysryhma", views.KysymysryhmaViewSet, basename="kysymysryhma")
router_v1.register(r"scale", views.ScaleViewSet, basename="scale")
router_v1.register(r"malfunction-message", views.MalfunctionMessageViewSet, basename="malfunction-message")


urlpatterns = [
    path(settings.BASE_URL, include([
        path("", views.RootView.as_view(), name='root-view'),
        path("admin/", admin.site.urls),
        path("api/v1/", include(router_v1.urls)),
        path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
        path("api/v1/token/", views.AccessTokenView.as_view()),
        path("api/v1/token/refresh/", views.RefreshTokenView.as_view()),
        path("accounts/login", views.CasLoginView.as_view(), name="cas_ng_login"),
        path("accounts/logout", views.CasLogoutView.as_view(), name="cas_ng_logout"),
        path("health/", views.HealthViewSet.as_view()),
        path("health-db/", views.HealthDbViewSet.as_view()),
    ]))
]
