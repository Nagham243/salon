from django.contrib import admin
from .models import CoachAppointmentsModel, StudentAppointmentPresenceModel
# Register your models here.

admin.site.register(CoachAppointmentsModel)
admin.site.register(StudentAppointmentPresenceModel)