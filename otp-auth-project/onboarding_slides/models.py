import uuid
from django.db import models
from django.utils.text import slugify


class OnboardingSlide(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    subtitle = models.CharField(max_length=150, blank=True)
    emoji = models.CharField(max_length=10, blank=True)
    image = models.ImageField(upload_to="onboarding/", blank=True, null=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:110]
            self.slug = f"{base}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title