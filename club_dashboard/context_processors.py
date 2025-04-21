def club_notifications(request):
    context = {
        'pending_orders_count': 0,
    }

    if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
        user_profile = request.user.userprofile
        if hasattr(user_profile, 'director_profile') and user_profile.director_profile:
            club = user_profile.director_profile.club

            from students.models import Order
            pending_orders_count = Order.objects.filter(
                club=club,
                status='pending',
                payment_method='cash_on_delivery'
            ).count()

            context['pending_orders_count'] = pending_orders_count

    return context