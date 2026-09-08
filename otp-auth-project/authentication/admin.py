

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User


class CustomUserCreationForm(UserCreationForm):
   
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("mobile_number", "country_code", "name", "email")


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    # Columns shown in the user list page.
    list_display = (
        "name",
        "email",
        "mobile_number",
        "country_code",
        "is_mobile_verified",
        "is_email_verified",
        "is_active",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "is_mobile_verified",
        "is_email_verified",
        "is_active",
        "is_staff",
    )

    search_fields = ("name", "email", "mobile_number")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "last_login")

    # Fields shown on the "view/edit user" detail page.
    fieldsets = (
        (None, {"fields": ("mobile_number", "country_code", "password")}),
        ("Personal info", {"fields": ("name", "email")}),
        (
            "Verification status",
            {"fields": ("is_mobile_verified", "is_email_verified")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    # Fields shown on the "add new user" page in the admin.
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "mobile_number",
                    "country_code",
                    "name",
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )
