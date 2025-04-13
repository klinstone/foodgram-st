from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение позволяет редактировать объект только его владельцу (автору).
    Для чтения доступ разрешен всем.
    """

    def has_permission(self, request, view):
        """Проверяет наличие прав на уровне ViewSet."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Проверяет наличие прав на уровне объекта."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение позволяет редактировать объект только админам/суперюзерам.
    Для чтения доступ разрешен всем.
    """

    def has_permission(self, request, view):
        """Проверяет наличие прав на уровне ViewSet."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Проверяет наличие прав на уровне объекта."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff or request.user.is_superuser
