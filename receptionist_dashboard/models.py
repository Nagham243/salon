from django.db import models
from club_dashboard.models import SalonAppointment
from accounts.models import StudentProfile, UserProfile
from students.models import ServicesModel

class SalonBooking(models.Model):
    appointment = models.OneToOneField(
        'club_dashboard.SalonAppointment',
        on_delete=models.CASCADE,
        related_name='booking'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='salon_bookings'
    )
    employee = models.CharField(max_length=255)  # Storing as string per the form's save method
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        service_names = ", ".join([bs.service.title for bs in self.services.all()])
        return f"{self.student.full_name} - {service_names} - {self.appointment.day}"

    class Meta:
        ordering = ['-created_at']

class BookingService(models.Model):
    """Model to handle multiple services per booking"""
    booking = models.ForeignKey(
        SalonBooking,
        on_delete=models.CASCADE,
        related_name='services'
    )
    service = models.ForeignKey(
        ServicesModel,
        on_delete=models.CASCADE,
        related_name='booking_services'
    )

    def __str__(self):
        return f"{self.booking.student.full_name} - {self.service.title}"

    class Meta:
        unique_together = ['booking', 'service']