from rest_framework import serializers
from .models import Banner, Notification


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ["id", "title", "slug", "subtitle", "image",
                  "cta_text", "order", "is_active", "created_at"]
        read_only_fields = ["slug"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "title", "slug", "body", "is_read", "created_at"]
        read_only_fields = ["slug"]