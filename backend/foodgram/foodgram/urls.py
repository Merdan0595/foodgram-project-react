from django.contrib import admin
from django.urls import path, include

from api.views import error_404_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]

handler404 = error_404_view
