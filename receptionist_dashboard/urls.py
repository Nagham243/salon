from django.urls import path
from receptionist_dashboard import views

urlpatterns = [
    path('', views.index, name='receptionistIndex'),
    path('salon/appointments/', views.salon_appointments, name='receptionist_salon_appointments'),
    path('salon/select-day/', views.select_appointment_day, name='select_appointment_day'),
    path('salon/book/<str:day>/', views.book_appointment_details, name='book_appointment_details'),
    path('select-appointment-time/<str:day>/', views.select_appointment_time, name='select_appointment_time'),
    path('verify-and-book-appointment/<str:day>/', views.verify_and_book_appointment, name='verify_and_book_appointment'),
    path('salon/book/<str:day>/<str:time_slot>/', views.book_appointment, name='book_appointment'),
    path('salon/appointment/<int:appointment_id>/', views.appointment_details, name='appointment_details'),
    path('salon/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('salon/service-duration/<int:service_id>/', views.get_service_duration, name='get_service_duration'),
    path('viewStudents', views.viewStudentss, name="viewStudentss"),
    path('addStudent', views.addStudent, name="addStudentFromReceptionist"),
    path('editStudent/<int:id>/', views.editStudentt, name='editStudentt'),
    path('deleteStudent/<int:id>/', views.deleteStudentt, name='deleteStudentt'),
]