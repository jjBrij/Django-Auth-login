from rest_framework import serializers
from .models import OnboardingSlide

class OnboardingSlideSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingSlide
        fields = ["id", "title", "slug", "subtitle", "emoji", "image",
                  "description", "order", "is_active"]
        read_only_fields = ["slug"]