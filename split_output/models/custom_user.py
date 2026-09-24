import django.db.models.signals
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    email =django.db.models.EmailField(unique=True,verbose_name="البريد الالكتروني")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    class Meta:
        verbose_name="مستخدم"
        verbose_name_plural="المستخدمون"

    def __str__(self):
             return self.username
