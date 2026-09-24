from django.contrib.auth.models import AbstractUser
import django.db


class CustomUser(AbstractUser):
    email = django.db.models.EmailField(unique=True, verbose_name="البريد الإلكتروني")


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email