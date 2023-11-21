from django.contrib import admin
from django.urls import path, include
from django.conf import settings

from raportointi import views

from rest_framework import routers


router_v1 = routers.DefaultRouter()
router_v1.register(r"data-collection", views.DataCollectionViewset, basename="data-collection")
router_v1.register(r"reporting-base", views.ReportingBaseViewset, basename="reporting-base")
router_v1.register(r"reporting-template", views.ReportingTemplateViewset, basename="reporting-template")
router_v1.register(r"closed-surveys", views.ClosedSurveysViewset, basename="closed-surveys")
router_v1.register(r"view-kysymysryhma-report", views.ViewReportViewset, basename="view-report")
router_v1.register(r"download-kysymysryhma-report", views.ReportPdfViewset, basename="download-report")
router_v1.register(r"summary", views.SummaryViewset, basename="summary")
router_v1.register(r"result", views.ResultViewset, basename="result")
router_v1.register(r"available-kyselykertas", views.AvailableKyselykierrosListViewset,
                   basename="available-kyselykertas")
router_v1.register(r"answers-export", views.AnswersExportViewset, basename="answers-export")

urlpatterns = [
    path(settings.BASE_URL, include([
        path("admin/", admin.site.urls),
        path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
        path("api/v1/", include(router_v1.urls)),
        path("api/v1/token/", views.AccessTokenView.as_view()),
        path("api/v1/token/refresh/", views.RefreshTokenView.as_view()),
        path("accounts/login", views.CasLoginView.as_view(), name="cas_ng_login"),
        path("accounts/logout", views.CasLogoutView.as_view(), name="cas_ng_logout"),
        path("health/", views.HealthViewSet.as_view()),
        path("health-db/", views.HealthDbViewSet.as_view()),
    ]))
]
