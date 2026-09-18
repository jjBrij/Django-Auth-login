from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import OnboardingSlide
from .serializers import OnboardingSlideSerializer

class OnboardingSlideViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OnboardingSlide.objects.filter(is_active=True)
    serializer_class = OnboardingSlideSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"