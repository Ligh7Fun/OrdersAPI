from rest_framework.permissions import BasePermission


class IsShopOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == 'shop' and request.user == obj.creator
