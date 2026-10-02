from django import template

from shop.models import PricingSettings

register = template.Library()


@register.simple_tag(takes_context=True)
def user_price(context, product):
    """
    سعر المنتج حسب مستوى الزبون الحالي (تجزئة للزائر).

    الاستخدام في القالب:
        {% load pricing_tags %}
        {% user_price product as p %}
        ${{ p|floatformat:2 }}
    """
    request = context.get('request')
    user = getattr(request, 'user', None)
    # إعدادات التسعير تُقرأ مرة واحدة لكل طلب صفحة
    pricing = getattr(request, '_pricing_settings', None)
    if pricing is None:
        pricing = PricingSettings.get_solo()
        if request is not None:
            request._pricing_settings = pricing
    return product.get_price_for_user(user, pricing)