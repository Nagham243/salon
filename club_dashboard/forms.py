from django import forms
from accounts.models import StudentProfile, CoachProfile, DirectorProfile,ReceptionistProfile
from students.models import Blog, ServicesModel, ProductsClassificationModel, ServicesClassificationModel, ProductsModel
from .models import ProductShipment


class StudentProfileForm(forms.ModelForm):

    class Meta:
        model = StudentProfile
        fields = ['full_name', 'phone', 'birthday']

        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder':'اسم الكامل', 'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
            'phone': forms.TextInput(attrs={'placeholder':'رقم الهاتف', 'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
            'birthday': forms.DateInput(attrs={'type':'date', 'placeholder':'تاريخ الميلاد', 'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
        }

class CoachProfileForm(forms.ModelForm):

    class Meta:
        model = CoachProfile
        fields = ['full_name', 'phone']

        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder':'اسم الكامل', 'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
            'phone': forms.TextInput(attrs={'placeholder':'رقم الهاتف', 'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
            # 'stadium': forms.DateInput(attrs={'placeholder':'الملعب', 'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
        }

class ArticleModelForm(forms.ModelForm):

    class Meta:
        model = Blog
        fields = ['title', 'desc', 'img', 'body']
        
        widgets = {
            'title': forms.TextInput(attrs={'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
            'desc': forms.TextInput(attrs={'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
            'img': forms.FileInput(attrs={'accept':"image/*", 'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
            'body': forms.Textarea(attrs={'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
        }


class ServicesModelForm(forms.ModelForm):
    class Meta:
        model = ServicesModel
        fields = ['title', 'desc', 'price', 'is_enabled']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
            'desc': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500', 'step': '0.01'}),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 mr-2'}),
        }

class ServicesClassificationModelForm(forms.ModelForm):

    class Meta:
        model = ServicesClassificationModel
        fields = ['title']

        widgets = {
            'title':forms.TextInput(attrs={'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'})
        }




class ProductsModelForm(forms.ModelForm):

    class Meta:
        model = ProductsModel
        fields = ['title','desc', 'price', 'stock', 'classification', 'manufacturing_date', 'expiration_date', 'is_enabled']

        widgets = {
        'title': forms.TextInput(attrs={'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
        'desc': forms.Textarea(attrs={'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
        'price':forms.NumberInput(attrs={'step': 0.00, 'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
        'stock':forms.NumberInput(attrs={'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
        'classification':forms.SelectMultiple(attrs={'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
        'manufacturing_date': forms.DateInput(attrs={'type': 'date', 'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
        'expiration_date': forms.DateInput(attrs={'type': 'date', 'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
        'is_enabled':forms.CheckboxInput(),
        }

class ProductsClassificationModelForm(forms.ModelForm):

    class Meta:
        model = ProductsClassificationModel
        fields = ['title']

        widgets = {
            'title':forms.TextInput(attrs={'class':'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'})
        }

class DirectorProfileForm(forms.ModelForm):
    class Meta:
        model = DirectorProfile
        fields = ['full_name', 'phone', 'about']  # No 'club' field

        widgets = {
            'full_name': forms.TextInput(attrs={
                'placeholder': 'اسم الكامل',
                'class': 'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'رقم الهاتف',
                'class': 'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'
            }),
            'about': forms.Textarea(attrs={
                'placeholder': 'نبذة عن المدير',
                'class': 'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'rows': 3
            }),
        }

class ReceptionistProfileForm(forms.ModelForm):
    class Meta:
        model = ReceptionistProfile
        fields = ['full_name', 'phone', 'email', 'about']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'placeholder': 'اسم الكامل',
                'class': 'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'رقم الهاتف',
                'class': 'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'البريد الالكتروني',
                'class': 'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'
            }),
            'about': forms.Textarea(attrs={
                'placeholder': 'نبذة عن الاستقبال',
                'class': 'w-full px-3 py-2 border border-indigo-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'rows': 3
            }),
        }

class ProductShipmentForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=ProductsModel.objects.none(),
        label="المنتج",
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'})
    )

    class Meta:
        model = ProductShipment
        fields = ['product', 'quantity', 'manufacturing_date', 'expiration_date', 'notes']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'min': 1
            }),
            'manufacturing_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'type': 'date'
            }),
            'expiration_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        club = kwargs.pop('club', None)
        super(ProductShipmentForm, self).__init__(*args, **kwargs)

        if club:
            self.fields['product'].queryset = ProductsModel.objects.filter(club=club)
