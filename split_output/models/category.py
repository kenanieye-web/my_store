import django.db.models.signals
from django.utils.text import slugify


class Category(django.db.models.Model):
    name = django.db.models.CharField(max_length=200, verbose_name="اسم التصنيف")
    slug = django.db.models.SlugField(unique=True, null=True, blank=True, verbose_name="الرابط (Slug)")
    parent = django.db.models.ForeignKey(
        'self',
        on_delete=django.db.models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="التصنيف الرئيسي"
    )

    class Meta:
        verbose_name = "تصنيف"
        verbose_name_plural = "التصنيفات"

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} -> {self.name}"
        return self.name

    def is_main_category(self):
        """التحقق مما إذا كان التصنيف رئيسياً"""
        return self.parent is None

    def save(self, *args, **kwargs):
        """توليد الـ Slug تلقائياً في حال عدم إدخاله"""
        if not self.slug and self.name:
            self.slug = slugify(self.name, allow_unicode=True) # type: ignore
        super().save(*args, **kwargs)
