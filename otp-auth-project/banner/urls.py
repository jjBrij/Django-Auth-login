from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("banners", views.BannerViewSet, basename="banner")
router.register("notifications", views.NotificationViewSet, basename="notification")

urlpatterns = router.urls