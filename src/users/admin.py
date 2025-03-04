from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CmmsUserChangeForm, CmmsUserCreationForm
from .models import AuditEntry, CmmsUser


class CmmsUserAdmin(UserAdmin):
    add_form = CmmsUserCreationForm
    form = CmmsUserChangeForm
    model = CmmsUser
    list_display = ("email", "first_name", "last_name", "is_manager")
    fieldsets = (
        (None, {"fields": ("email", "first_name", "last_name", "password", "groups")}),
        (
            "Permissions",
            {"fields": ("is_manager", "is_staff", "is_superuser", "is_active")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "is_manager",
                    "is_staff",
                    "is_superuser",
                    "is_active",
                    "groups",
                ),
            },
        ),
    )
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email", "first_name", "last_name")


class AuditEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "action", "email", "ip", "description")
    list_filter = (
        "date",
        "action",
    )
    search_fields = ("date", "email", "action", "ip", "description")


admin.site.register(CmmsUser, CmmsUserAdmin)
admin.site.register(AuditEntry, AuditEntryAdmin)
