from django.contrib import admin
from .models import OnboardingSlide

@admin.register(OnboardingSlide)
class OnboardingSlideAdmin(admin.ModelAdmin):
    list_display = ("title", "emoji", "order", "is_active")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"slug": ("title",)}