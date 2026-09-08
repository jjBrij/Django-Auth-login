

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, mobile_number, country_code, name, email=None, **extra_fields):
        if not mobile_number:
            raise ValueError("Mobile number is required.")
        if not name:
            raise ValueError("Name is required.")
        email = self.normalize_email(email) if email else None
        user = self.model(
            mobile_number=mobile_number,
            country_code=country_code,
            name=name,
            email=email,
            **extra_fields,
        )
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile_number, country_code, name, password, email=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_mobile_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        email = self.normalize_email(email) if email else None

        user = self.model(
            mobile_number=mobile_number,
            country_code=country_code,
            name=name,
            email=email,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=150)
    country_code = models.CharField(max_length=5, default="+91")
    mobile_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Stored in full E.164 format, e.g. +919876543210",
    )
    email = models.EmailField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )
    is_mobile_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # required for Django admin access
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = UserManager()
    USERNAME_FIELD = "mobile_number"
    REQUIRED_FIELDS = ["name", "country_code"]
    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["mobile_number"]),
            models.Index(fields=["email"]),
        ]
    def __str__(self):
        return f"{self.name} ({self.mobile_number})"
