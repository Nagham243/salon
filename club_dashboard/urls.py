from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views  # ✅ Import views properly
from .views import mark_notifications_read  # ✅ Import the view
from .views import viewClubNotifications  # ✅ Import the view function
from students.views import salon_appointments



# ✅ Import necessary views once
from .views import (
    viewDirectors, addDirector, editDirector, deleteDirector,
    viewAdmins, addAdmin, editAdmin, deleteAdmin
)

urlpatterns = [
    path('', views.club_dashboard_index, name="club_dashboard_index"),

    # Students Management
    path('viewStudents', views.viewStudents, name="viewStudents"),
    path('addStudent', views.addStudent, name="addStudent"),
    path('editStudent/<int:id>', views.editStudent, name="editStudent"),
    path('deleteStudent/<int:id>', views.deleteStudent, name="deleteStudent"),

    # Coaches Management
    path('viewCoachs', views.viewCoachs, name="viewCoachs"),
    path('addCoach', views.addCoach, name="addCoach"),    
    path('editCoach/<int:id>', views.editCoach, name="editCoach"),    
    path('deleteCoach/<int:id>', views.deleteCoach, name="deleteCoach"),

    path('viewReceptionists', views.viewReceptionists, name="viewReceptionists"),
    path('addReceptionist', views.addReceptionist, name="addReceptionist"),
    path('editReceptionist/<int:id>', views.editReceptionist, name="editReceptionist"),
    path('deleteReceptionist/<int:id>', views.deleteReceptionist, name="deleteReceptionist"),
    # Products Management
    path('addProduct', views.addProduct, name="addProduct"),
    path('editProduct/<int:id>', views.editProduct, name="editProduct"),
    path('DeleteProduct/<int:id>', views.DeleteProduct, name="DeleteProduct"),
    path('viewProducts', views.viewProducts, name="viewProducts"),

    path('addProductClassification', views.addProductClassification, name="addProductClassification"),
    path('editProductClassification/<int:id>', views.editProductClassification, name="editProductClassification"),
    path('viewProductsClassification', views.viewProductsClassification, name="viewProductsClassification"),
    path('DeleteProductsClassification/<int:id>', views.DeleteProductsClassification, name="DeleteProductsClassification"),

    # Services Management
    path('addServices', views.addServices, name="addServices"),
    path('editServices/<int:id>', views.editServices, name="editServices"),
    path('DeleteServices/<int:id>', views.DeleteServices, name="DeleteServices"),
    path('viewServices', views.viewServices, name="viewServices"),

    path('addServicesClassification', views.addServicesClassification, name="addServicesClassification"),
    path('editServicesClassification/<int:id>', views.editServicesClassification, name="editServicesClassification"),
    path('DeleteServicesClassification/<int:id>', views.DeleteServicesClassification, name="DeleteServicesClassification"),
    path('viewServicesClassification', views.viewServicesClassification, name="viewServicesClassification"),

    # Blog Management
    path('articles/', views.viewArticles, name="viewArticles"),
    path('articles/add/', views.addArticle, name="addArticle"),
    path('articles/edit/<int:id>/', views.editArticle, name="editArticle"),
    path('articles/delete/<int:id>/', views.DeleteArticle, name="DeleteArticle"),
    path('salon-appointments/', views.salon_appointments, name='club_salon_appointments'),
    path('salon/appointment/<int:appointment_id>/', views.appointment_details, name='director_appointment_details'),
    path('salon/cancel/<int:appointment_id>/', views.cancel_appointment, name='director_cancel_appointment'),
    path('viewDirectors/', viewDirectors, name="viewDirectors"),  # ✅ This now matches your working URL
    path('viewDirectors/add/', addDirector, name="addDirector"),
    path('viewDirectors/edit/<int:id>/', editDirector, name="editDirector"),
    path('viewDirectors/delete/<int:id>/', deleteDirector, name="deleteDirector"),
    path('mark-notifications-read/', mark_notifications_read, name='mark_notifications_read'),
    path('notifications/', viewClubNotifications, name='viewClubNotifications'),  # ✅ Ensure correct name
    path('reviews/', views.reviews_list, name='reviews_list'),

    # ✅ Correct URL
    path('club/orders/', views.club_orders, name='club_orders'),
    path('club/orders/<int:order_id>/update/', views.update_order_status, name='update_order_status'),
    path('club/orders/<int:order_id>/details/', views.order_details_api, name='order_details_api'),
    path('products/shipments/add/', views.add_shipment, name='add_shipment'),
    path('products/<int:product_id>/shipments/', views.view_product_shipments, name='view_product_shipments'),
    path('products/<int:product_id>/details/', views.product_details, name='product_details'),
    path('financial-dashboard/', views.club_financial_dashboard, name='club_financial_dashboard'),
]

# ✅ Ensure media files work in debug mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
