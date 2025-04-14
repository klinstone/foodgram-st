from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение позволяет редактировать объект только его владельцу (автору).
    Для чтения доступ разрешен всем.
    """

    def has_object_permission(self, request, view, obj):
        """Проверяет наличие прав на уровне объекта."""
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )
