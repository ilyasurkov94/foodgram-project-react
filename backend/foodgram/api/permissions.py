from rest_framework import permissions, status


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            if request.user.is_admin:
                return True
            elif request.user.is_blocked:
                return False
        return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            if request.user.is_admin:
                return True
            elif request.user.is_blocked:
                return False
        return False


class IsAdminAuthorOrReadPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            if request.user.is_admin:
                return True
            elif request.user.is_blocked:
                return False
        return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            if request.user.is_admin or obj.author == request.user:
                return True
            elif request.user.is_blocked:
                return False
        return False



# class IsAdminAuthorOrReadPermission(permissions.BasePermission):
#     def has_permission(self, request, view):
#         if request.user.is_authenticated:  # Если юзер авторизован
#             if request.user.is_blocked:  # Проверка заблокированного юзера
#                 return False
#             elif request.user.is_admin:  # Если юзер админ
#                 return True
#         elif request.method in permissions.SAFE_METHODS:  # Если safe methods
#             return True
#         raise ValueError(
#             "Ошибка доступа!", 'token', status.HTTP_403_FORBIDDEN)

#     def has_object_permission(self, request, view, obj):
#         if request.user.is_authenticated:  # Если юзер авторизован
#             if request.user.is_blocked:  # Проверка заблокированного юзера
#                 return False
#             elif (request.user.is_admin
#                   or obj.author == request.user):  # Если юзер админ
#                 return True
#         elif request.method in permissions.SAFE_METHODS:  # Если safe methods
#             return True
#         raise ValueError("Ошибка доступа!", status.HTTP_403_FORBIDDEN)
