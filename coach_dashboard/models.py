from django.db import models
from accounts.models import CoachProfile, StudentProfile
from students.models import ServicesModel
from django.utils import timezone

# Create your models here.

class CoachAppointmentsModel(models.Model):
    coach = models.ForeignKey(CoachProfile, on_delete=models.CASCADE)
    service = models.ForeignKey(ServicesModel, on_delete=models.CASCADE, null=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.coach.full_name)
    
    def has_ended(self):
        if self.end_datetime > timezone.now():
            return False
        return True
        
class StudentAppointmentPresenceModel(models.Model):
    appointment = models.ForeignKey(CoachAppointmentsModel, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)

    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.student.full_name)

