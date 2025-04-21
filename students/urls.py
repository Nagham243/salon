from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import add_review,edit_review

urlpatterns = [
    path('', views.index, name='studentIndex'),
    # path('login/', auth_views.LoginView.as_view(), name='login'),
    # Products
    path('viewProducts', views.viewProducts, name='StudentViewProducts'),
    path('viewProducts/<int:id>', views.viewProductsSpecific, name='viewProductsSpecific'),

    # Services (Updated to avoid conflicts with club dashboard)
    path('studentViewServices', views.viewServices, name='studentViewServices'),
    path('studentViewServicesSpecific/<int:id>', views.viewServicesSpecific, name='studentViewServicesSpecific'),

    # Blog (Updated to avoid conflicts with club dashboard)
    path('articles/', views.viewArticles, name='clientviewArticles'),
    path('articles/<int:id>/', views.viewArticle, name='viewArticle'),
    path('clientSalonAppointments', views.salon_appointments, name='studentViewArticles'),
    path('salon/select-day/', views.select_appointment_day, name='client_select_appointment_day'),
    path('salon/book/<str:day>/', views.book_appointment_details, name='client_book_appointment_details'),
    path('select-appointment-time/<str:day>/', views.select_appointment_time, name='client_select_appointment_time'),
    path('verify-and-book-appointment/<str:day>/', views.verify_and_book_appointment, name='client_verify_and_book_appointment'),
    path('salon/book/<str:day>/<str:time_slot>/', views.book_appointment, name='client_book_appointment'),
    path('salon/appointment/<int:appointment_id>/', views.appointment_details, name='client_appointment_details'),
    path('salon/cancel/<int:appointment_id>/', views.cancel_appointment, name='client_cancel_appointment'),
    path('salon/service-duration/<int:service_id>/', views.get_service_duration, name='get_service_duration'),
    path('studentViewServicesSpecific/<int:id>', views.viewServicesSpecific, name='viewServicesSpecific'),

    # Order Service
    path('OrderService/<int:service_id>', views.OrderService, name='OrderService'),

    # Reviews
    path('reviews/', views.view_reviews, name='view_reviews'),
    path('add_review/', views.add_review, name='add_review'),  # Add review page
    path('reviews/edit/<int:review_id>/', views.edit_review, name='edit_review'),  # ✅ Edit Review
    path('cart/', views.cart, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/count/', views.get_cart_count, name='get_cart_count'),
    path('checkout/', views.checkout, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('service/cart/add/', views.add_service_to_cart, name='add_service_to_cart'),
    path('service/cart/update/', views.update_service_cart, name='update_service_cart'),
    path('profile/', views.view_student_profile, name='student_profile'),
    path('profile/edit/', views.edit_student_profile, name='edit_student_profile'),
    path('orders/<int:order_id>/', views.order_details, name='order_details'),
    path('student/orders/', views.student_orders, name='student_orders'),
]
