import sys
import base64
from io import BytesIO
from django import forms
from .models import StudentProfile, ClubsModel


class StudentProfileForm(forms.ModelForm):
    """Form for creating/updating a student profile."""

    class Meta:
        model = StudentProfile
        fields = ['full_name', 'phone', 'birthday', 'club']

        widgets = {
            'full_name': forms.TextInput(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500", 'placeholder': 'الاسم كامل'}),
            'phone': forms.TextInput(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500", 'placeholder': 'رقم الهاتف'}),
            'birthday': forms.DateInput(format=('%d-%m-%Y'), attrs={'type': 'date', 'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"}),
            'club': forms.Select(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"}),
        }


class DirectorSignupForm(forms.Form):
    """Form for Director signup, including club registration with Base64 image conversion."""

    # User fields
    username = forms.CharField(label="اسم المستخدم", widget=forms.TextInput(attrs={'class': "input-style"}))
    email = forms.EmailField(label="البريد الالكتروني", widget=forms.EmailInput(attrs={'class': "input-style"}))
    password = forms.CharField(label="كلمة المرور", widget=forms.PasswordInput(attrs={'class': "input-style"}))
    phone = forms.CharField(label="رقم الهاتف", widget=forms.TextInput(attrs={'class': "input-style"}))

    # Club fields
    club_name = forms.CharField(label="اسم النادي", widget=forms.TextInput(attrs={'class': "input-style"}))
    city = forms.ChoiceField(label="المدينة", choices=[], widget=forms.Select(attrs={'class': "input-style"}))
    street = forms.CharField(label="الشارع", widget=forms.TextInput(attrs={'class': "input-style"}))
    district = forms.CharField(label="الحي", required=False, widget=forms.TextInput(attrs={'class': "input-style"}))
    about = forms.CharField(label="عن النادي", required=False, widget=forms.Textarea(attrs={'class': "input-style", 'rows': 3}))
    desc = forms.CharField(label="وصف قصير", required=False, widget=forms.Textarea(attrs={'class': "input-style", 'rows': 2}))
    club_profile_image_base64 = forms.FileField(label="شعار النادي", required=False, widget=forms.FileInput(attrs={'class': "input-style"}))

    def __init__(self, *args, **kwargs):
        """Initialize form and handle city choices dynamically."""
        super().__init__(*args, **kwargs)

        # Import city choices dynamically to avoid circular import issues
        from .fields import citys

        # Ensure `citys` is a valid tuple and has data
        if not isinstance(citys, tuple) or not citys:
            citys = (('', 'اختر المدينة'),)  # Safe fallback as a tuple

        # Convert tuple to list before assigning (Django requires lists for choices)
        self.fields['city'].choices = list(citys)

    def clean_club_profile_image_base64(self):
        """Convert uploaded image file to Base64 string before saving."""
        image_file = self.cleaned_data.get("club_profile_image_base64")

        if image_file:
            try:
                # Read image binary data
                image_data = image_file.read()

                # Debugging: Print first 50 bytes of the image
                print(f"DEBUG: First 50 bytes of image = {image_data[:50]}")

                # Encode to Base64
                base64_encoded = base64.b64encode(image_data).decode("utf-8")
                print(f"DEBUG: Base64 length = {len(base64_encoded)}")

                return base64_encoded

            except Exception as e:
                print(f"ERROR: Failed to convert image to Base64: {e}")
                raise forms.ValidationError(f"خطأ في معالجة الصورة: {e}")

        return None  # No image uploaded


class EditClubProfileForm(forms.ModelForm):
    """Form for editing club profile with Base64 image handling."""

    club_profile_image_base64 = forms.FileField(label="شعار النادي", required=False, widget=forms.FileInput(attrs={'class': "input-style"}))

    class Meta:
        model = ClubsModel
        fields = ['name', 'desc', 'about', 'club_profile_image_base64']

    def save(self, commit=True):
        club = super().save(commit=False)

        # Handle image upload and Base64 conversion
        if self.cleaned_data.get('club_profile_image_base64'):
            image = self.cleaned_data['club_profile_image_base64']
            image_data = image.read()
            base64_encoded = base64.b64encode(image_data).decode('utf-8')
            club.club_profile_image_base64 = base64_encoded

        if commit:
            club.save()
        return club

class ReceptionistSignupForm(forms.Form):
    """Form for Receptionist signup."""

    # User fields
    username = forms.CharField(label="اسم المستخدم", widget=forms.TextInput(attrs={'class': "input-style"}))
    email = forms.EmailField(label="البريد الالكتروني", widget=forms.EmailInput(attrs={'class': "input-style"}))
    password = forms.CharField(label="كلمة المرور", widget=forms.PasswordInput(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500",'placeholder': 'أدخل كلمة المرور'}))

    # Receptionist fields
    full_name = forms.CharField(label="الاسم الكامل", widget=forms.TextInput(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500",'placeholder': 'الاسم كامل'}))
    phone = forms.CharField(label="رقم الهاتف", widget=forms.TextInput(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500",'placeholder': 'رقم الهاتف'}))
    club = forms.ModelChoiceField(
        queryset=ClubsModel.objects.all(),
        label="النادي",
        widget=forms.Select(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"})
    )
    about = forms.CharField(
        label="معلومات إضافية",
        required=False,
        widget=forms.Textarea(attrs={'class': "w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500", 'rows': 3, 'placeholder': 'معلومات إضافية'})
    )

