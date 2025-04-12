from django.contrib import admin
from django.urls import path, include
from django.conf import settings
# Для раздачи медиа в режиме разработки
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Подключаем URL из нашего приложения api
    path('api/', include('api.urls')),
    # Подключаем URL для аутентификации от Djoser
    path('api/auth/', include('djoser.urls')),
    # Предоставляет эндпоинт для получения/удаления токена
    path('api/auth/', include('djoser.urls.authtoken')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
