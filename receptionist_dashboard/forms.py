from django import forms
from accounts.models import StudentProfile, CoachProfile
from .models import SalonBooking
from students.models import ServicesModel
from datetime import datetime

class SalonBookingForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=StudentProfile.objects.all(),
        label="اسم العميل",
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'})
    )
    employee = forms.ModelChoiceField(
        queryset=CoachProfile.objects.all(),
        label="اسم الموظف",
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'})
    )
    employee_name = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    def __init__(self, *args, **kwargs):
        super(SalonBookingForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get('employee')

        if employee and hasattr(employee, 'full_name'):
            cleaned_data['employee_name'] = employee.full_name

        return cleaned_data

class ServiceSelectionForm(forms.Form):
    service = forms.ModelChoiceField(
        queryset=ServicesModel.objects.all(),
        label="نوع الخدمة",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'onchange': 'updateServiceDuration(this)'
        })
    )
    duration = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        service = cleaned_data.get('service')

        if service:
            cleaned_data['duration'] = service.duration

        return cleaned_data