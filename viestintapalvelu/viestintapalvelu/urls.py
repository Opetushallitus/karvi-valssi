from django.conf import settings
from django.contrib import admin
from django.urls import path, include

from kyselyt import views


urlpatterns = [
    path(settings.BASE_URL, include([
        path('admin/', admin.site.urls),
        path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
        path('api/v1/viestit/', views.MessageListViewSet.as_view()),
        path('api/v1/token/', views.AccessTokenView.as_view()),
        path('api/v1/pdfsend/', views.PdfUploadViewSet.as_view()),
        path('api/v1/laheta/', views.SendViewSet.as_view()),
        path('health/', views.HealthViewSet.as_view()),
        path('health-db/', views.HealthDbViewSet.as_view()),
    ]))
]
