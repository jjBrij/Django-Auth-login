import uuid
from django.db import models
from django.utils.text import slugify


class Banner(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    subtitle = models.CharField(max_length=150, blank=True)
    image = models.ImageField(upload_to="banners/", blank=True, null=True)
    cta_text = models.CharField(max_length=50, default="Register Now")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]

    def save(self, *args, **kwargs):
        # auto-create slug only when it's empty (admin can override manually)
        if not self.slug:
            base = slugify(self.title)[:110]
            self.slug = f"{base}-{uuid.uuid4().hex[:8]}"   # e.g. free-doubt-resolution-3fa2b1c9
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Notification(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    body = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:160]
            self.slug = f"{base}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title