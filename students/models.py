from django.db import models
from accounts.models import ClubsModel
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import UserProfile


# Create your models here.


#Products
class ProductsClassificationModel(models.Model):
    club = models.ForeignKey(ClubsModel, on_delete=models.CASCADE, null=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    title = models.CharField(max_length=254, null=True)
    creation_date = models.DateTimeField(null=True, verbose_name="تاريخ الانشاء")

class ProductsModel(models.Model):
    club = models.ForeignKey(ClubsModel, on_delete=models.CASCADE)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=254, null=True)
    desc = models.TextField(null=True)
    price = models.DecimalField(max_digits = 6, decimal_places = 2)
    stock = models.IntegerField(default=1, null=True)
    classification = models.ManyToManyField('ProductsClassificationModel', blank=True)
    is_enabled = models.BooleanField(default=True)
    creation_date = models.DateTimeField(null=True, verbose_name="تاريخ الانشاء")
    manufacturing_date = models.DateField(null=True, blank=True, verbose_name="تاريخ التصنيع")
    expiration_date = models.DateField(null=True, blank=True, verbose_name="تاريخ انتهاء الصلاحية")

    @property
    def is_expiring_soon(self):
        if not self.expiration_date:
            return False

        import datetime
        one_month_later = datetime.date.today() + datetime.timedelta(days=30)
        return self.expiration_date <= one_month_later and self.expiration_date > datetime.date.today()

    @property
    def is_expired(self):
        if not self.expiration_date:
            return False

        import datetime
        return self.expiration_date < datetime.date.today()

class ProductsImage(models.Model):
    product = models.ForeignKey('ProductsModel', on_delete=models.CASCADE)
    img = models.ImageField(upload_to="Products/imgs/%Y/%m/%d", blank=True, null=True)
    img_base64 = models.TextField(blank=True, null=True)
    creation_date = models.DateTimeField(null=True, verbose_name="تاريخ الانشاء")

class ProductsRate(models.Model):
    product = models.ForeignKey('ProductsModel', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    msg = models.TextField()
    rate = models.IntegerField()
    creation_date = models.DateTimeField(null=True, verbose_name="تاريخ الانشاء")





#Services
class ServicesClassificationModel(models.Model):
    club = models.ForeignKey(ClubsModel, on_delete=models.CASCADE, null=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    title = models.CharField(max_length=254, null=True)
    creation_date = models.DateTimeField(null=True, verbose_name="تاريخ الانشاء")

    def __str__(self):
        return self.title


class ServicesModel(models.Model):
    club = models.ForeignKey(ClubsModel, on_delete=models.CASCADE)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=254, null=True)
    desc = models.TextField(null=True)
    subscription_days = models.IntegerField(default=30, null=True, blank=True)
    age_from = models.IntegerField(default=0, null=True, blank=True)
    age_to = models.IntegerField(default=100, null=True, blank=True)

    price = models.DecimalField(max_digits=6, decimal_places=2)
    classification = models.ManyToManyField('ServicesClassificationModel', blank=True)
    is_enabled = models.BooleanField(default=True)
    creation_date = models.DateTimeField(null=True, verbose_name="تاريخ الانشاء")

    duration = models.IntegerField(help_text="Duration in minutes", default=0)
    discounted_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='services/', null=True, blank=True)

    def __str__(self):
        return self.title

class ServicesImage(models.Model):
    product = models.ForeignKey('ServicesModel', on_delete=models.CASCADE)
    img = models.ImageField(upload_to="Services/imgs/%Y/%m/%d", blank=True, null=True)
    img_base64 = models.TextField(blank=True, null=True)
    creation_date = models.DateTimeField(null=True, verbose_name="تاريخ الانشاء")

class ServicesRate(models.Model):
    
    product = models.ForeignKey('ServicesModel', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    msg = models.TextField()
    rate = models.IntegerField()
    creation_date = models.DateTimeField(null=True, verbose_name="تاريخ الانشاء")



#Blog
class BlogClassificationModel(models.Model):
    club = models.ForeignKey(ClubsModel, on_delete=models.CASCADE, null=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    title = models.CharField(max_length=254, null=True)
    creation_date = models.DateTimeField(null=True, verbose_name="تاريخ الانشاء")

class Blog(models.Model):
    club = models.ForeignKey(ClubsModel, on_delete=models.CASCADE, null=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    title = models.CharField(max_length=254, null=True)
    desc = models.CharField(max_length=254, null=True)
    img = models.ImageField(upload_to="blog/imgs/%Y/%m/%d", blank=True, null=True)
    body = models.TextField()

    creation_date = models.DateTimeField(null=True, verbose_name="تاريخ الانشاء")



class ServiceOrderModel(models.Model):
    service = models.ForeignKey(ServicesModel, on_delete=models.SET_NULL, null=True)
    student = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits = 6, decimal_places = 2)
    is_complited = models.BooleanField(default=False)
    end_datetime = models.DateTimeField()
    creation_date = models.DateTimeField(null=True, verbose_name="تاريخ الانشاء")

    def has_subscription(self):
        if self.end_datetime > timezone.now():
            return True
        return False


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductsModel, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.title} ({self.quantity})"

    @property
    def total_price(self):
        return self.quantity * self.product.price

class ServiceCartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.ForeignKey(ServicesModel, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.service.title} ({self.quantity})"

    @property
    def total_price(self):
        return self.quantity * self.service.price

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('confirmed', 'تم التأكيد'),
        ('cancelled', 'تم الإلغاء'),
        ('completed', 'مكتمل'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('credit_card', 'بطاقة ائتمان'),
        ('cash_on_delivery', 'الدفع عند الاستلام'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    club = models.ForeignKey(ClubsModel, on_delete=models.CASCADE, related_name='orders', null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(ProductsModel, on_delete=models.SET_NULL, null=True, blank=True)
    service = models.ForeignKey(ServicesModel, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        if self.product:
            return f"{self.product.title} ({self.quantity})"
        elif self.service:
            return f"{self.service.title} ({self.quantity})"
        return f"Order Item #{self.id}"
