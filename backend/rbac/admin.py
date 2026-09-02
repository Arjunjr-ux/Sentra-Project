from django.contrib import admin

from .models import Permission, Role, RolePermission, UserRole


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 0
    autocomplete_fields = ["permission"]


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["codename", "description"]
    search_fields = ["codename", "description"]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name", "is_system", "description", "created_at"]
    list_filter = ["is_system"]
    search_fields = ["name"]
    inlines = [RolePermissionInline]


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "assigned_by", "assigned_at"]
    search_fields = ["user__email", "role__name"]
    autocomplete_fields = ["user", "role", "assigned_by"]
