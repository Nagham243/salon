from django.db import models
from django.contrib.auth.models import User
from .fields import citys
from django.utils import timezone
from django.utils.timezone import now
from datetime import timedelta


AccountTypeChoices = (
    ('1', 'admin'),
    ('2', 'director'),
    ('3', 'student'),
    ('4', 'coach'),
    ('5', 'receptionist'),
)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image_base64 = models.TextField(blank=True, null=True)
    account_type = models.CharField(max_length=250, choices=AccountTypeChoices)
    creation_date = models.DateTimeField(auto_now_add=True)
    
    # ✅ Allow multiple directors per club
    director_profile = models.ForeignKey('DirectorProfile', on_delete=models.SET_NULL, null=True, blank=True)
    student_profile = models.ForeignKey('StudentProfile', on_delete=models.SET_NULL, null=True, blank=True)
    Coach_profile = models.ForeignKey('CoachProfile', on_delete=models.SET_NULL, null=True, blank=True)
    receptionist_profile = models.ForeignKey('ReceptionistProfile', on_delete=models.SET_NULL, null=True, blank=True)

    is_active = models.BooleanField(default=False)
    last_active_datetime = models.DateTimeField(null=True, blank=True)
    is_in_chat = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.get_account_type_display()}"


class ClubsModel(models.Model):
    name = models.CharField(max_length=250, unique=True, verbose_name="اسم الأكاديمية")
    club_profile_image_base64 = models.TextField(blank=True, null=True)
    desc = models.CharField(max_length=255, null=True, verbose_name="وصف قصير")
    about = models.TextField(max_length=255, null=True, verbose_name="نبذة")
    city = models.CharField(max_length=255, choices=citys, null=True, verbose_name="المدينة")
    district = models.CharField(max_length=250, null=True, verbose_name="الحي")
    street = models.CharField(max_length=250, null=True, verbose_name="الشارع")
    creation_date = models.DateTimeField(auto_now_add=True)
    chat_enabled = models.BooleanField(default=True, verbose_name="دردشة مفعلة")

    def __str__(self):
        return str(self.name)


class DirectorProfile(models.Model):
    full_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    about = models.TextField(null=True, blank=True)
    
    # ✅ Ensure multiple directors per club
    club = models.ForeignKey('ClubsModel', on_delete=models.CASCADE, related_name="directors")

    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.club.name}"


class StudentProfile(models.Model):
    full_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    birthday = models.DateField()
    has_subscription = models.BooleanField(default=False)
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    about = models.TextField(null=True)
    club = models.ForeignKey('ClubsModel', on_delete=models.SET_NULL, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.full_name)

    def age(self):
        return (timezone.now().date() - self.birthday).days // 365

    def save(self, *args, **kwargs):
        if not self.pk:
            self.subscription_start_date = timezone.now()
            self.subscription_end_date = timezone.now() + timedelta(days=30)
            self.has_subscription = True

        super(StudentProfile, self).save(*args, **kwargs)

    def get_subscription_status(self):
        if self.subscription_end_date:
            end_date = self.subscription_end_date.date()
            days_left = (end_date - timezone.now().date()).days
            
            if days_left > 6:
                return "active"
            elif 0 <= days_left <= 6:
                return "expiring_soon"
            else:
                return "expired"
        
        return "expired"


class CoachProfile(models.Model):
    full_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    # stadium = models.CharField(max_length=50)
    major = models.CharField(max_length=50, null=True)
    about = models.TextField(null=True)
    club = models.ForeignKey('ClubsModel', on_delete=models.SET_NULL, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.full_name)

class ReceptionistProfile(models.Model):
    full_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    email = models.EmailField()
    club = models.ForeignKey('ClubsModel', on_delete=models.SET_NULL, null=True)
    about = models.TextField(null=True, blank=True)
    hire_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Receptionist: {self.full_name}"

class OTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"OTP for {self.user.username}: {self.otp_code}"