from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from shop.models.product import Product
from shop.models.review import Review

@login_required
def add_review(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        rating = request.POST.get('rating', 5)
        comment = request.POST.get('comment', '')
        
        # حفظ التقييم في قاعدة البيانات
        Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            comment=comment
        )
    return redirect('product_detail', pk=product_id)
