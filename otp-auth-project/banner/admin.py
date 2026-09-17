from django.contrib import admin
from .models import Banner, Notification

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "order", "is_active")
    prepopulated_fields = {"slug": ("title",)}   # auto-fills as you type title
    list_editable = ("order", "is_active")

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_read", "created_at")
    prepopulated_fields = {"slug": ("title",)}