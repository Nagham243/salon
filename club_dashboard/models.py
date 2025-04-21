from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import ClubsModel, UserProfile
from django.utils.timezone import now  # ✅ Import existing ClubsModel
from accounts.models import StudentProfile, CoachProfile  # ✅ Import the correct models



try:
    from students.models import ProductsModel  # ✅ Import ProductsModel safely
except ImportError:
    ProductsModel = None  # ✅ Prevents ImportError in circular dependencies


# ✅ Model for tracking product stockx`
class ProductsStockModel(models.Model):
    product = models.ForeignKey(
        ProductsModel,
        on_delete=models.CASCADE,
        related_name="stock_entries",
        verbose_name="المنتج"
    )
    quantity = models.PositiveIntegerField(verbose_name="الكمية المتاحة")
    creation_date = models.DateTimeField(default=timezone.now, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")  # ✅ Added tracking for updates

    def __str__(self):
        return f"{self.product.name} - Stock: {self.quantity}"

class ProductImg(models.Model):
    product = models.ForeignKey('students.ProductsModel', on_delete=models.CASCADE, related_name='product_images')
    img = models.ImageField(upload_to='product_images/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'

    def __str__(self):
        return f"Image for {self.product.name}"


# ✅ Model for club-wide notifications
class Notification(models.Model):
    club = models.ForeignKey(
        ClubsModel,  # ✅ Correct reference to ClubsModel from accounts
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="النادي"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,  # ✅ Prevents issues when a user is deleted
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name="المستخدم"
    )
    message = models.TextField(verbose_name="الرسالة")
    is_read = models.BooleanField(default=False, verbose_name="تم القراءة")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")  # ✅ Added for tracking notification updates

    def __str__(self):
        return f"Notification for {self.user.username if self.user else 'Unknown'}: {self.message[:50]}..."
        
        
class Review(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="student_reviews")
    coach = models.ForeignKey(CoachProfile, on_delete=models.CASCADE, related_name="coach_reviews")
    rating = models.IntegerField(choices=[(i, f"{i}⭐") for i in range(1, 6)], default=5)
    comment = models.TextField(null=True, blank=True)  # ✅ Allows NULL values to prevent migration errors
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.student.full_name} for {self.coach.full_name} ({self.rating}/5)"


class SalonAppointment(models.Model):
    DAY_CHOICES = [
        ('السبت', 'السبت'),
        ('الأحد', 'الأحد'),
        ('الإثنين', 'الإثنين'),
        ('الثلاثاء', 'الثلاثاء'),
        ('الأربعاء', 'الأربعاء'),
        ('الخميس', 'الخميس'),
        ('الجمعة', 'الجمعة'),
    ]
    club = models.ForeignKey(
        ClubsModel,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name="النادي"
    )
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        status = "متاح" if self.available else "محجوز"
        time_display = f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}" if self.start_time and self.end_time else "N/A"
        return f"{self.day} - {time_display} ({status})- {self.club.name}"



class ProductShipment(models.Model):
    product = models.ForeignKey(
        'students.ProductsModel',
        on_delete=models.CASCADE,
        related_name='shipments',
        verbose_name="المنتج"
    )
    quantity = models.PositiveIntegerField(verbose_name="الكمية")
    manufacturing_date = models.DateField(null=True, blank=True, verbose_name="تاريخ التصنيع")
    expiration_date = models.DateField(null=True, blank=True, verbose_name="تاريخ انتهاء الصلاحية")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")

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

    @property
    def remaining_quantity(self):
        return self.quantity

    def __str__(self):
        return f"شحنة {self.product.title} - {self.quantity} وحدة - تاريخ الإنتهاء: {self.expiration_date or 'غير محدد'}"

    class Meta:
        ordering = ['expiration_date', 'created_at']
        verbose_name = "شحنة منتج"
        verbose_name_plural = "شحنات المنتجات"
