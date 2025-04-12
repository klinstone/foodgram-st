# backend/api/permissions.py
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение позволяет редактировать объект только его владельцу (автору).
    Для чтения доступ разрешен всем.
    """
    def has_permission(self, request, view):
        # Разрешаем GET, HEAD, OPTIONS запросы всем
        if request.method in permissions.SAFE_METHODS:
            return True
        # Для остальных методов требуем аутентификацию
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Разрешаем GET, HEAD, OPTIONS запросы всем
        if request.method in permissions.SAFE_METHODS:
            return True
        # Требуем, чтобы пользователь был автором объекта
        # (Предполагаем, что у объекта есть поле 'author')
        return obj.author == request.user

class IsAdminOrReadOnly(permissions.BasePermission):
     """
     Разрешение позволяет редактировать объект только админам/суперюзерам.
     Для чтения доступ разрешен всем.
     """
     def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

     def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
             return True
        # Разрешение на запись только для админа или суперпользователя
        return request.user.is_staff or request.user.is_superuser