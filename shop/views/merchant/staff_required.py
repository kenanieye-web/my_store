from django.contrib.auth.decorators import user_passes_test


def staff_required(view_func):
    """ديكور مخصص للتحقق من أن المستخدم من طاقم الإدارة (التاجر)"""
    def check_user(user):
        return user.is_authenticated and user.is_staff
    
    decorated_view = user_passes_test(
        check_user,
        login_url='login',
        redirect_field_name=None
    )(view_func)
    return decorated_view
