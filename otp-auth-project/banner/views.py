from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Banner, Notification
from .serializers import BannerSerializer, NotificationSerializer

class BannerViewSet(viewsets.ModelViewSet):
    queryset = Banner.objects.filter(is_active=True)
    serializer_class = BannerSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"          # detail lookups by slug instead of id


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.all().order_by("-created_at")
    serializer_class = NotificationSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"