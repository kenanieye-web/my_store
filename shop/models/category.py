from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name="اسم التصنيف")
    slug = models.SlugField(unique=True, null=True, blank=True, allow_unicode=True,
                            verbose_name="الرابط (Slug)")
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='children', verbose_name="التصنيف الرئيسي"
    )
    image = models.ImageField(upload_to='categories/', null=True, blank=True,
                              verbose_name="صورة التصنيف")

    class Meta:
        verbose_name = "تصنيف"
        verbose_name_plural = "التصنيفات"

    def __str__(self):
        return self.full_path()

    def full_path(self, sep=' › '):
        """المسار الكامل: الكترونيات › الأجهزة المنزلية › كاويات"""
        parts, node, seen = [], self, set()
        while node is not None and node.pk not in seen:
            seen.add(node.pk)
            parts.append(node.name)
            node = node.parent
        return sep.join(reversed(parts))

    def is_main_category(self):
        return self.parent_id is None

    def descendant_ids(self):
        """معرّفات كل التصنيفات التابعة (أبناء وأحفاد) بأي عمق"""
        ids, current = [], [self.pk]
        while current:
            current = list(Category.objects.filter(parent_id__in=current)
                           .values_list('pk', flat=True))
            ids.extend(current)
        return ids

    def self_and_descendant_ids(self):
        return [self.pk] + self.descendant_ids()

    @classmethod
    def tree(cls):
        """قائمة مرتبة شجرياً: [(التصنيف, المستوى, المسار الكامل), ...]"""
        children = {}
        for c in cls.objects.all().order_by('name'):
            children.setdefault(c.parent_id, []).append(c)
        out = []

        def walk(parent_id, level, prefix):
            for c in children.get(parent_id, []):
                path = prefix + c.name
                out.append((c, level, path))
                walk(c.pk, level + 1, path + ' › ')

        walk(None, 0, '')
        return out

    def clean(self):
        if self.pk and self.parent_id:
            if self.parent_id == self.pk or self.parent_id in self.descendant_ids():
                raise ValidationError("لا يمكن جعل التصنيف أباً لنفسه أو لأحد فروعه.")

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            base = slugify(self.name, allow_unicode=True) or 'category'
            slug, i = base, 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f'{base}-{i}'
            self.slug = slug
        super().save(*args, **kwargs)