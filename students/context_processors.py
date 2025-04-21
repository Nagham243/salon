from django.db.models import Sum
from .models import CartItem, ServiceCartItem

def cart_items_count(request):
    if request.user.is_authenticated:
        product_count = CartItem.objects.filter(user=request.user).aggregate(
            total=Sum('quantity'))['total'] or 0
        service_count = ServiceCartItem.objects.filter(user=request.user).aggregate(
            total=Sum('quantity'))['total'] or 0
        total_count = product_count + service_count
        return {'cart_count': total_count}
    return {'cart_count': 0}

