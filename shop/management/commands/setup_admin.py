from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "يتأكد من وجود حساب مشرف ثابت دائماً، وينشئه تلقائياً لو كانت قاعدة البيانات فاضية"

    def handle(self, *args, **options):
        User = get_user_model()

        admin_email = "kenan.ie.ye@gmail.com"
        admin_username = "kenan"
        admin_password = "kenan123456"

        user, created = User.objects.get_or_create(
            email=admin_email,
            defaults={
                "username": admin_username,
                "is_staff": True,
                "is_superuser": True,
            }
        )

        if created:
            user.set_password(admin_password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"تم إنشاء حساب المشرف: {admin_email}"))
        else:
            changed = False
            if not user.is_staff:
                user.is_staff = True
                changed = True
            if not user.is_superuser:
                user.is_superuser = True
                changed = True
            if changed:
                user.save()
            self.stdout.write(self.style.SUCCESS(f"حساب المشرف {admin_email} موجود بالفعل وصلاحياته سليمة"))