from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.functions import Lower

from common.permissions import ADMIN, CUSTOMER, STAFF


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra):
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.update(is_staff=True, is_superuser=True, role=ADMIN)
        return self.create_user(email, password, **extra)


class User(AbstractUser):
    """Login identity. It exists in the first commit because a custom user
    model must be in place before any migration runs."""

    ROLES = [(ADMIN, "Admin"), (STAFF, "Staff"), (CUSTOMER, "Customer")]

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLES, default=CUSTOMER, db_index=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        constraints = [models.UniqueConstraint(Lower("email"), name="unique_lower_email")]
