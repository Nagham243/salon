from django.shortcuts import render, redirect,get_object_or_404
from accounts.models import UserProfile, StudentProfile, CoachProfile ,ReceptionistProfile
from django.contrib.auth.models import User
from .forms import StudentProfileForm, CoachProfileForm, ArticleModelForm, ServicesModelForm, ServicesClassificationModelForm, ProductsModelForm, ProductsClassificationModelForm,ReceptionistProfileForm,ProductShipmentForm
from accounts.forms import ReceptionistSignupForm
from students.models import Blog, ServicesModel, ServicesClassificationModel, ProductsModel, ProductsClassificationModel, ProductsImage, ServicesImage,Order,OrderItem,ServiceOrderModel
from django.utils import timezone
# Create your views here.
from django.contrib import messages  # ✅ Fix missing import
from .forms import DirectorProfileForm  # ✅ Fix missing import
from accounts.models import DirectorProfile  # ✅ Add this import
from .models import Notification  # Import the Notification model
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile
from club_dashboard.models import Notification  # ✅ Import Notification Model
from .utils import send_notification  # ✅ Import notification function
from django.contrib.auth.decorators import login_required  # ✅ Fix missing import
from django.db.models import Avg
from club_dashboard.models import Review  # ✅ Import Review model from students app
from .models import SalonAppointment,ProductShipment
from django.shortcuts import render
from django.db.models import Sum, F, FloatField, Case, When, IntegerField, Value
from django.db.models.functions import Cast
from .models import ProductsModel ,ProductImg
from django.utils import timezone
from django.contrib import messages
from .forms import ProductsModelForm
from django.core.paginator import Paginator
import base64
import time
import decimal
from django.core.files.base import ContentFile
from django.utils import timezone
from .forms import ServicesModelForm
from datetime import datetime, timedelta
from django.db import models , transaction
from receptionist_dashboard.models import BookingService
from django.template.loader import render_to_string
import json

# Helper function to get user's club
def get_user_club(user):
    user_profile = user.userprofile
    club = None
    if user_profile.account_type == '3':  # Student
        club = user_profile.student_profile.club if hasattr(user_profile, 'student_profile') else None
    elif user_profile.account_type == '4':  # Coach
        club = user_profile.Coach_profile.club if hasattr(user_profile, 'Coach_profile') else None
    elif user_profile.account_type == '2':  # Director
        club = user_profile.director_profile.club if hasattr(user_profile, 'director_profile') else None
    elif user_profile.account_type == '5':  # Receptionist
        club = user_profile.receptionist_profile.club if hasattr(user_profile, 'receptionist_profile') else None
    return club

@login_required
def club_dashboard_index(request):
    user = request.user

    # ✅ Ensure the user has a valid director profile
    if not hasattr(user, 'userprofile') or not user.userprofile.director_profile:
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    # ✅ Get the correct club for the director
    club = user.userprofile.director_profile.club
    club_name = club.name

    # ✅ Get directors linked through UserProfile
    directors = UserProfile.objects.filter(account_type='2', director_profile__club=club)
    director_count = directors.count()

    # ✅ Fetch students and coaches from this club
    students = StudentProfile.objects.filter(club=club)
    student_count = students.count()

    coaches = CoachProfile.objects.filter(club=club)
    coach_count = coaches.count()

    # ✅ Notifications
    notifications = Notification.objects.filter(club=club, is_read=False).order_by('-created_at')
    unread_count = notifications.count()
    notifications.update(is_read=True)

    # ✅ Subscriptions
    active_count, expiring_soon_count, expired_count = 0, 0, 0
    for student in students:
        status = student.get_subscription_status()
        if status == "active":
            active_count += 1
        elif status == "expiring_soon":
            expiring_soon_count += 1
        else:
            expired_count += 1

    total_students = max(1, active_count + expiring_soon_count + expired_count)

    def calc_percent(v, total):
        return round((v / total) * 100, 2) if total > 0 else 0

    active_percentage = calc_percent(active_count, total_students)
    expiring_soon_percentage = calc_percent(expiring_soon_count, total_students)
    expired_percentage = calc_percent(expired_count, total_students)

    # ✅ Top Rated Coaches
    top_rated_coaches = (
        CoachProfile.objects.filter(club=club)
        .annotate(avg_rating=Avg('coach_reviews__rating'))
        .filter(avg_rating__isnull=False)
        .order_by('-avg_rating')[:5]
    )

    # ✅ Top Reviews
    top_reviews = (
        Review.objects.filter(coach__club=club)
        .order_by('-rating', '-created_at')[:5]
    )



    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date:
        start_date = (timezone.now() - timezone.timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')

    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
    except ValueError:
        start_date_obj = timezone.now() - timezone.timedelta(days=30)
        end_date_obj = timezone.now()

    orders = Order.objects.filter(
        club=club,
        created_at__gte=start_date_obj,
        created_at__lte=end_date_obj
    ).order_by('-created_at')

    total_revenue = int(orders.filter(status__in=['confirmed', 'completed']).aggregate(Sum('total_price'))['total_price__sum'] or 0)


    return render(request, 'club_dashboard/index.html', {
        'clubName': club_name,
        'students': students,
        'coaches': coaches,
        'directors': directors,
        'director_count': director_count,
        'coach_count': coach_count,
        'student_count': student_count,
        'active_count': active_count,
        'expiring_soon_count': expiring_soon_count,
        'expired_count': expired_count,
        'active_percentage': active_percentage,
        'expiring_soon_percentage': expiring_soon_percentage,
        'expired_percentage': expired_percentage,
        'notifications': notifications,
        'unread_count': unread_count,
        'top_rated_coaches': top_rated_coaches,
        'top_reviews': top_reviews,
        'total_revenue': total_revenue,
    })



def viewStudents(request):
    """Displays all students in the club."""
    user = request.user

    if not hasattr(user.userprofile, 'director_profile') or not user.userprofile.director_profile:
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    club = user.userprofile.director_profile.club

    students = UserProfile.objects.filter(
        account_type='3', 
        student_profile__club=club
    ).select_related('user', 'student_profile')

    # ✅ Enrich each student with subscription status
    for student in students:
        profile = student.student_profile
        if profile and hasattr(profile, 'get_subscription_status'):
            student.subscription_status = profile.get_subscription_status()
        else:
            student.subscription_status = "unknown"

    return render(request, 'club_dashboard/students/viewStudents.html', {'students': students})


def addStudent(request):
    """Adds a new student to the club."""
    user = request.user

    # ✅ Ensure user is a director
    if not hasattr(user.userprofile, 'director_profile') or not user.userprofile.director_profile:
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    club = user.userprofile.director_profile.club
    form = StudentProfileForm()

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # ✅ Prevent duplicate username and email
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('addStudent')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already in use.")
            return redirect('addStudent')

        form = StudentProfileForm(request.POST)
        if form.is_valid():
            # ✅ Create new user
            student = User.objects.create(username=username, email=email)
            if password:
                student.set_password(password)
            student.save()

            # ✅ Create and link Student Profile
            student_profile = form.save(commit=False)
            student_profile.user = student  # 🔥 FIXED: Set user reference
            student_profile.club = club
            student_profile.save()

            # ✅ Create UserProfile entry
            UserProfile.objects.create(user=student, account_type='3', student_profile=student_profile)

            # ✅ Send notification
            send_notification(user, club, f"📢 New student {username} has joined {club.name}.")

            messages.success(request, "Student added successfully.")
            return redirect('viewStudents')

    return render(request, 'club_dashboard/students/addStudent.html', {'form': form})


@login_required
def editStudent(request, id):
    """Edits an existing student's details."""
    user = request.user

    # ✅ Ensure user is a director
    if not hasattr(user.userprofile, 'director_profile') or not user.userprofile.director_profile:
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    club = user.userprofile.director_profile.club  
    student_profile = get_object_or_404(StudentProfile, id=id)
    student = get_object_or_404(User, userprofile__student_profile=student_profile)

    form = StudentProfileForm(instance=student_profile)

    if request.method == 'POST':
        new_username = request.POST.get('username')
        new_email = request.POST.get('email')
        password = request.POST.get('password')

        form = StudentProfileForm(request.POST, instance=student_profile)
        if form.is_valid():
            # ✅ Update student details
            student.username = new_username
            student.email = new_email
            if password:
                student.set_password(password)
            student.save()

            student_profile = form.save(commit=False)
            student_profile.user = student  # 🔥 FIXED: Ensure user link remains
            student_profile.save()

            # ✅ Send notification
            send_notification(user, club, f"📝 Student {student.username}'s profile has been updated.")

            messages.success(request, "Student profile updated successfully.")
            return redirect('viewStudents')

    return render(request, 'club_dashboard/students/editStudent.html', {
        'form': form,
        'student': student
    })



@login_required
def deleteStudent(request, id):
    """Deletes a student from the club."""
    user = request.user

    # ✅ Ensure user is a director
    if not hasattr(user.userprofile, 'director_profile') or not user.userprofile.director_profile:
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    club = user.userprofile.director_profile.club  
    student_profile = get_object_or_404(StudentProfile, id=id)
    student = get_object_or_404(User, userprofile__student_profile=student_profile)

    student_name = student.username

    # ✅ Delete student profile and user account
    student_profile.delete()
    student.delete()

    # ✅ Send notification
    send_notification(user, club, f"🗑️ Student {student_name} has been removed from the club.")

    messages.success(request, "Student has been deleted successfully.")
    return redirect('viewStudents')


def viewCoachs(request):
    """Displays a list of coaches belonging to the club."""
    user = request.user
    coach_userprofile = UserProfile.objects.filter(
        account_type='4',
        Coach_profile__club=user.userprofile.director_profile.club
    )
    return render(request, 'club_dashboard/coachs/viewCoachs.html', {'coach_userprofile': coach_userprofile})

@login_required
def addCoach(request):
    """Adds a new coach to the club."""
    user = request.user

    # ✅ Ensure user is a director
    if not hasattr(user.userprofile, 'director_profile') or not user.userprofile.director_profile:
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    club = user.userprofile.director_profile.club
    form = CoachProfileForm()

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # ✅ Prevent duplicate username and email
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('addCoach')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already in use.")
            return redirect('addCoach')

        form = CoachProfileForm(request.POST)
        if form.is_valid():
            # ✅ Create new user
            coach = User.objects.create(username=username, email=email)
            if password:
                coach.set_password(password)
            coach.save()

            # ✅ Create coach profile & associate with club
            coach_profile = form.save(commit=False)
            coach_profile.club = club
            coach_profile.save()

            # ✅ Create UserProfile entry
            UserProfile.objects.create(user=coach, account_type='4', Coach_profile=coach_profile)

            # ✅ Send notification
            send_notification(user, club, f"📢 A new coach {username} has joined {club.name}.")

            messages.success(request, "Employee added successfully.")
            return redirect('viewCoachs')

    return render(request, 'club_dashboard/coachs/addCoach.html', {'form': form})

@login_required
def editCoach(request, id):
    """Edits an existing coach's details."""
    user = request.user

    # ✅ Ensure user is a director
    if not hasattr(user.userprofile, 'director_profile') or not user.userprofile.director_profile:
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    club = user.userprofile.director_profile.club  
    coach_profile = get_object_or_404(CoachProfile, id=id)
    coach = get_object_or_404(User, userprofile__Coach_profile=coach_profile)

    form = CoachProfileForm(instance=coach_profile)

    if request.method == 'POST':
        new_username = request.POST.get('username')
        new_email = request.POST.get('email')
        password = request.POST.get('password')

        form = CoachProfileForm(request.POST, instance=coach_profile)
        if form.is_valid():
            # ✅ Check if username or email was changed
            username_changed = new_username != coach.username
            email_changed = new_email != coach.email

            # ✅ Update coach details
            coach.username = new_username
            coach.email = new_email
            if password:
                coach.set_password(password)
            coach.save()

            form.save()

            # ✅ Send notification if changes were made
            notification_message = f"📝 Coach {coach.username}'s profile was updated."
            if username_changed or email_changed:
                notification_message += " (Username/Email updated.)"

            send_notification(user, club, notification_message)

            messages.success(request, "Coach profile updated successfully.")
            return redirect('viewCoachs')

    return render(request, 'club_dashboard/coachs/editCoach.html', {
        'form': form,
        'coach': coach,
    })

@login_required
def deleteCoach(request, id):
    """Deletes a coach from the club."""
    user = request.user

    # ✅ Ensure user is a director
    if not hasattr(user.userprofile, 'director_profile') or not user.userprofile.director_profile:
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    club = user.userprofile.director_profile.club  
    coach_profile = get_object_or_404(CoachProfile, id=id)
    coach = get_object_or_404(User, userprofile__Coach_profile=coach_profile)

    coach_name = coach.username

    # ✅ Delete coach profile and user account
    coach_profile.delete()
    coach.delete()

    # ✅ Send notification
    send_notification(user, club, f"🗑️ Employee {coach_name} has been removed from the salon.")

    messages.success(request, "Employee has been deleted successfully.")
    return redirect('viewCoachs')



    
def viewAdmins(request):
    user = request.user
    admin_userprofile = UserProfile.objects.filter(account_type='3', Admin_profile__club=user.userprofile.director_profile.club)
    return render(request, 'club_dashboard/admins/viewAdmins.html', {'admin_userprofile': admin_userprofile})
def addAdmin(request):
    user = request.user
    club = user.userprofile.director_profile.club

    form = AdminProfileForm()
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        form = AdminProfileForm(request.POST)
        if form.is_valid():
            admin = User.objects.create(username=username, email=email)
            if password:
                admin.set_password(password)
            admin.save()

            admin_profile = form.save()
            admin_profile.club = club
            admin_profile.save()

            userprofile = UserProfile.objects.create(user=admin, account_type='3', Admin_profile=admin_profile)
            userprofile.save()

            return redirect('viewAdmins')

    return render(request, 'club_dashboard/admins/addAdmin.html', {'form': form})

def editAdmin(request, id):
    admin_profile = AdminProfile.objects.get(id=id)
    form = AdminProfileForm(instance=admin_profile)
    admin = User.objects.get(userprofile__Admin_profile=admin_profile)
    username = admin.username
    email = admin.email

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        form = AdminProfileForm(request.POST, instance=admin_profile)
        if form.is_valid():
            admin.username = username
            admin.email = email
            if password:
                admin.set_password(password)
            admin.save()

            admin_profile = form.save()

            return redirect('viewAdmins')

    return render(request, 'club_dashboard/admins/editAdmin.html', {'admin': admin, 'form': form, 'email': email, 'username': username})

def deleteAdmin(request, id):
    admin_profile = AdminProfile.objects.get(id=id)
    admin = User.objects.get(userprofile__Admin_profile=admin_profile)

    admin_profile.delete()
    admin.delete()

    return redirect('viewAdmins')




def addProduct(request):
    user = request.user
    club = user.userprofile.director_profile.club
    form = ProductsModelForm()

    if request.method == 'POST':
        form = ProductsModelForm(data=request.POST)
        if form.is_valid():
            ser = form.save(commit=False)
            ser.club = club
            ser.creator = user
            ser.creation_date = timezone.now()
            ser.save()

            profile_imgs = request.POST.getlist('profile_imgs')
            for img_data in profile_imgs:
                format, imgstr = img_data.split(';base64,') if ';base64,' in img_data else ('', img_data)
                ext = format.split('/')[-1] if '/' in format else 'png'

                from django.core.files.base import ContentFile
                import base64, uuid

                data = ContentFile(base64.b64decode(imgstr), name=f'{uuid.uuid4()}.{ext}')

                ProductImg.objects.create(
                    product=ser,
                    img=data
                )

            messages.success(request, 'تم إضافة المنتج بنجاح!')
            return redirect('viewProducts')

    return render(request, 'club_dashboard/products/ProductsStock/addProductStock.html', {'form': form})

def editProduct(request, id):
    product = ProductsModel.objects.get(id=id)
    profile_img_objs = ProductImg.objects.filter(product=product)
    form = ProductsModelForm(instance=product)

    if request.method == 'POST':
        form = ProductsModelForm(data=request.POST, instance=product)
        if form.is_valid():
            profile_imgs = request.POST.getlist('profile_imgs')
            images_changed = request.POST.get('images_changed', 'false') == 'true'

            updated_product = form.save(commit=False)
            updated_product.updated_at = timezone.now()
            updated_product.save()
            form.save_m2m()

            if images_changed:
                ProductImg.objects.filter(product=product).delete()

                for img_data in profile_imgs:
                    if img_data.startswith('data:image'):
                        format, imgstr = img_data.split(';base64,')
                        ext = format.split('/')[-1]

                        import uuid
                        filename = f"{uuid.uuid4()}.{ext}"

                        from django.core.files.base import ContentFile
                        import base64
                        data = ContentFile(base64.b64decode(imgstr))

                        img_obj = ProductImg(product=product)
                        img_obj.img.save(filename, data, save=False)
                        img_obj.save()

            messages.success(request, 'تم تعديل المنتج بنجاح')
            return redirect('viewProducts')

    context = {
        'form': form,
        'profile_imgs': profile_img_objs
    }
    return render(request, 'club_dashboard/products/ProductsStock/editProductStock.html', context)

def viewProducts(request):
    user = request.user
    club = user.userprofile.director_profile.club
    products = ProductsModel.objects.filter(club=club)
    total_products = products.count()

    total_value = 0
    low_stock_count = 0
    out_of_stock_count = 0
    expiring_soon_count = 0
    expired_count = 0
    low_stock_threshold = 10

    for product in products:
        product_value = product.price * product.stock
        total_value += product_value

        if 0 < product.stock <= low_stock_threshold:
            low_stock_count += 1

        if product.stock == 0:
            out_of_stock_count += 1

        if product.is_expiring_soon:
            expiring_soon_count += 1

        if product.is_expired:
            expired_count += 1

    paginator = Paginator(products, 6)
    page_number = request.GET.get('page', 1)
    paginated_products = paginator.get_page(page_number)

    context = {
        'products': paginated_products,
        'total_products': total_products,
        'total_value': total_value,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'expiring_soon_count': expiring_soon_count,
        'expired_count': expired_count,
        'low_stock_threshold': low_stock_threshold,
    }

    return render(request, 'club_dashboard/products/ProductsStock/viewProductsStock.html', context)


def DeleteProduct(request, id):
    art = get_object_or_404(ProductsModel, id=id)
    art.delete()
    messages.success(request, 'تم حذف المنتج بنجاح!')
    return redirect('viewProducts')

def addProductClassification(request):
    user = request.user
    club = user.userprofile.director_profile.club
    form = ProductsClassificationModelForm()
    if request.method == 'POST':
        form = ProductsClassificationModelForm(data=request.POST)
        if form.is_valid():
            cla = form.save(commit=False)
            cla.club = club
            cla.creator = user
            cla.creation_date = timezone.now()
            cla.save()

    return render(request, 'club_dashboard/products/Classification/addClassification.html', {'form':form})

def editProductClassification(request, id):
    cla = ProductsClassificationModel.objects.get(id=id)
    form = ProductsClassificationModelForm(instance=cla)
    if request.method == 'POST':
        form = ProductsClassificationModelForm(data=request.POST, instance=cla)
        if form.is_valid():
            form.save()
    return render(request, 'club_dashboard/products/Classification/editClassification.html', {'form':form})

def viewProductsClassification(request):
    classifications = ProductsClassificationModel.objects.all()

    return render(request, 'club_dashboard/products/Classification/viewClassification.html', {'classifications':classifications})

def DeleteProductsClassification(request, id):
    art = ProductsClassificationModel.objects.get(id=id)
    art.delete()
    return redirect('viewProductsClassification')


#Services
def addServices(request):
    user = request.user
    club = user.userprofile.director_profile.club
    form = ServicesModelForm()

    if request.method == 'POST':
        form = ServicesModelForm(data=request.POST)
        if form.is_valid():
            ser = form.save(commit=False)
            ser.club = club
            ser.creator = user
            ser.creation_date = timezone.now()

            # Set default values for required fields you don't want to use
            ser.age_from = 0  # Default value
            ser.age_to = 100  # Default value
            ser.subscription_days = 30  # Default value

            # Handle the duration field from the form
            duration = request.POST.get('duration')
            if duration:
                ser.duration = int(duration)
            else:
                ser.duration = 0  # Default value

            # Handle the discounted_price field from the form
            discounted_price = request.POST.get('discounted_price')
            if discounted_price and discounted_price.strip():
                ser.discounted_price = decimal.Decimal(discounted_price)

            ser.save()

            # Handle direct image upload
            image_data = request.POST.get('service_image_data')
            if image_data and image_data.startswith('data:image'):
                # Get the format and the actual base64 data
                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]

                # Generate filename and save path
                filename = f"service_{ser.id}_{int(time.time())}.{ext}"
                temp_file = ContentFile(base64.b64decode(imgstr), name=filename)

                # Save to the model's ImageField
                ser.image.save(filename, temp_file, save=True)

            # Redirect to the service list after successful addition
            return redirect('viewServices')
        else:
            print(form.errors)  # Add this to debug form validation errors

    return render(request, 'club_dashboard/services/addServices.html', {'form': form})



def editServices(request, id):
    ser = ServicesModel.objects.get(id=id)
    form = ServicesModelForm(instance=ser)

    if request.method == 'POST':
        form = ServicesModelForm(data=request.POST, instance=ser)
        if form.is_valid():
            ser = form.save(commit=False)
            ser.creation_date = timezone.now()

            duration = request.POST.get('duration')
            ser.duration = int(duration) if duration else 0

            discounted_price = request.POST.get('discounted_price')
            if discounted_price and discounted_price.strip():
                ser.discounted_price = decimal.Decimal(discounted_price)
            else:
                ser.discounted_price = None

            # Check if the current image should be removed
            remove_current_image = request.POST.get('remove_current_image')
            if remove_current_image == 'true' and ser.image:
                # Delete the old image file
                ser.image.delete(save=False)

            # Process new image upload if available
            image_data = request.POST.get('service_image_data')
            if image_data and image_data.startswith('data:image'):
                # Get the format and the actual base64 data
                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]

                # Generate filename and save path
                filename = f"service_{ser.id}_{int(time.time())}.{ext}"
                temp_file = ContentFile(base64.b64decode(imgstr), name=filename)

                # If there's an existing image, delete it first
                if ser.image:
                    ser.image.delete(save=False)

                # Save to the model's ImageField
                ser.image.save(filename, temp_file, save=False)

            ser.save()
            return redirect('viewServices')
        else:
            print(form.errors)

    return render(request, 'club_dashboard/services/editServices.html', {'form': form})


def viewServices(request):
    services = ServicesModel.objects.filter(club=request.user.userprofile.director_profile.club)

    if services:
        avg_price = sum(service.discounted_price or service.price for service in services) / len(services)
        avg_price = round(avg_price, 1)

        avg_duration = sum(service.duration for service in services) / len(services)
        avg_duration_hours = int(avg_duration // 60)
        avg_duration_minutes = int(avg_duration % 60)
    else:
        avg_price = 0
        avg_duration_hours = 0
        avg_duration_minutes = 0

    context = {
        'services': services,
        'avg_price': avg_price,
        'avg_duration_hours': avg_duration_hours,
        'avg_duration_minutes': avg_duration_minutes,
    }

    return render(request, 'club_dashboard/services/viewServices.html', context)

def DeleteServices(request, id):
    art = ServicesModel.objects.get(id=id)
    art.delete()
    return redirect('viewServices')

def addServicesClassification(request):
    user = request.user
    club = user.userprofile.director_profile.club
    form = ServicesClassificationModelForm()
    if request.method == 'POST':
        form = ServicesClassificationModelForm(data=request.POST)
        if form.is_valid():
            cla = form.save(commit=False)
            cla.club = club
            cla.creator = user
            cla.creation_date = timezone.now()
            cla.save()


    return render(request, 'club_dashboard/services/Classification/addClassification.html', {'form':form})

def editServicesClassification(request, id):
    cla = ServicesClassificationModel.objects.get(id=id)
    form = ServicesClassificationModelForm(instance=cla)
    if request.method == 'POST':
        form = ServicesClassificationModelForm(data=request.POST, instance=cla)
        if form.is_valid():
            form.save()

    return render(request, 'club_dashboard/services/Classification/editClassification.html', {'form':form})

def viewServicesClassification(request):
    classifications = ServicesClassificationModel.objects.all()
    return render(request, 'club_dashboard/services/Classification/viewClassification.html', {'classifications':classifications})

def DeleteServicesClassification(request, id):
    art = ServicesClassificationModel.objects.get(id=id)
    art.delete()
    return redirect('viewServicesClassification')

#Blog
def addArticle(request):
    user = request.user
    club = user.userprofile.director_profile.club
    form = ArticleModelForm()
    if request.method == 'POST':
        form = ArticleModelForm(data=request.POST,files=request.FILES)
        if form.is_valid():

            art = form.save(commit=False)
            art.club = club
            art.creator = user
            art.creation_date = timezone.now()
            art.save()
            return redirect('viewArticles')

    return render(request, 'club_dashboard/blog/addArticle.html', {'form':form})

def editArticle(request, id):
    user = request.user
    club = user.userprofile.director_profile.club
    art = Blog.objects.get(id=id)
    form = ArticleModelForm(instance=art)
    try:
        art = Blog.objects.get(id=id, club=club)
        form = ArticleModelForm(instance=art)

        if request.method == 'POST':
            form = ArticleModelForm(data=request.POST, files=request.FILES, instance=art)
            if form.is_valid():
                form.save()
                return redirect('viewArticles')

        return render(request, 'club_dashboard/blog/editArticle.html', {'form': form})

    except Blog.DoesNotExist:
        return redirect('viewArticles')

def viewArticles(request):
    user = request.user
    club = user.userprofile.director_profile.club
    arts = Blog.objects.filter(club=club)  # Only show articles from this club

    # Get statistics for the dashboard
    total_articles = arts.count()
    current_month = timezone.now().month
    current_year = timezone.now().year
    new_articles_this_month = arts.filter(
        creation_date__month=current_month,
        creation_date__year=current_year
    ).count()

    # Get most popular articles (assuming you have a views or likes field)
    # If not, you can add this feature later
    popular_articles = arts.order_by('-id')[:3]

    context = {
        'arts': arts,
        'total_articles': total_articles,
        'new_articles_this_month': new_articles_this_month,
        'popular_articles': popular_articles.count()
    }
    return render(request, 'club_dashboard/blog/viewArticless.html', context)

def DeleteArticle(request, id):
    user = request.user
    club = user.userprofile.director_profile.club
    try:
        art = Blog.objects.get(id=id, club=club)
        art.delete()
    except Blog.DoesNotExist:
        pass

    return redirect('viewArticles')
    
def viewDirectors(request):
    user = request.user

    # ✅ Ensure the user has a profile
    user_profile = get_object_or_404(UserProfile, user=user)

    # ✅ Ensure user is a director and has a club
    if not user_profile.director_profile or not user_profile.director_profile.club:
        messages.error(request, "Unauthorized access.")
        return redirect('club_dashboard_index')

    # ✅ Get all directors from the same club
    club = user_profile.director_profile.club
    directors = UserProfile.objects.filter(account_type='2', director_profile__club=club).select_related('director_profile', 'user')

    return render(request, 'club_dashboard/directors/viewDirectors.html', {'directors': directors})   
    
def addDirector(request):
    user = request.user

    # ✅ Ensure the user is a director before proceeding
    if not hasattr(user.userprofile, 'director_profile') or not user.userprofile.director_profile:
        messages.error(request, "Unauthorized access.")
        return redirect('club_dashboard_index')  # 🔹 Fix: Redirect to the club dashboard if unauthorized

    club = user.userprofile.director_profile.club  # Get the current director’s club
    form = DirectorProfileForm()

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # ✅ Ensure username and email are unique
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('addDirector')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already in use.")
            return redirect('addDirector')

        form = DirectorProfileForm(request.POST)
        if form.is_valid():
            # ✅ Create user
            director_user = User.objects.create(username=username, email=email)
            if password:
                director_user.set_password(password)
            director_user.save()

            # ✅ Create director profile and assign the club
            director_profile = form.save(commit=False)
            director_profile.club = club  
            director_profile.save()

            # ✅ Create user profile
            UserProfile.objects.create(user=director_user, account_type='2', director_profile=director_profile)

            messages.success(request, "Director added successfully.")
            return redirect('viewDirectors')  # 🔹 Fix: Redirect to the correct club dashboard page

    return render(request, 'club_dashboard/directors/addDirector.html', {'form': form})


def editDirector(request, id):
    # Get the DirectorProfile object
    director_profile = get_object_or_404(DirectorProfile, id=id)
    # Get the associated User object
    director = get_object_or_404(User, userprofile__director_profile=director_profile)

    form = DirectorProfileForm(instance=director_profile)
    username = director.username
    email = director.email

    if request.method == 'POST':
        username = request.POST.get('username')  # Allow username editing
        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        about = request.POST.get('about')
        password = request.POST.get('password')

        form = DirectorProfileForm(request.POST, instance=director_profile)
        
        if form.is_valid():
            # Ensure the username is unique (excluding the current user)
            if User.objects.exclude(id=director.id).filter(username=username).exists():
                messages.error(request, "Username already exists.")
                return redirect('editDirector', id=id)

            # Ensure the email is unique (excluding the current user)
            if User.objects.exclude(id=director.id).filter(email=email).exists():
                messages.error(request, "Email is already in use.")
                return redirect('editDirector', id=id)

            # Update the User fields
            director.username = username
            director.email = email
            if password:
                director.set_password(password)  # Change password if provided
            director.save()

            # Update the DirectorProfile fields
            director_profile.full_name = full_name
            director_profile.phone = phone
            director_profile.about = about
            director_profile.save()

            messages.success(request, "Director updated successfully.")
            return redirect('viewDirectors')

    return render(request, 'club_dashboard/directors/editDirector.html', {
        'director': director,
        'form': form,
        'email': email,
        'username': username
    })
    
def deleteDirector(request, id):
    director_profile = get_object_or_404(DirectorProfile, id=id)
    director = get_object_or_404(User, userprofile__director_profile=director_profile)

    user = request.user

    # ✅ Ensure only directors from the same club can delete
    if not hasattr(user.userprofile, 'director_profile') or not user.userprofile.director_profile:
        messages.error(request, "Unauthorized access.")
        return redirect('viewDirectors')

    if user.userprofile.director_profile.club != director_profile.club:
        messages.error(request, "You cannot delete a director from another club.")
        return redirect('viewDirectors')

    director_profile.delete()
    director.delete()

    messages.success(request, "Director deleted successfully.")
    return redirect('viewDirectors')

def viewClubNotifications(request):
    """Displays all club notifications and marks them as read."""
    user = request.user

    # ✅ Ensure the user has a valid director profile
    if not hasattr(user.userprofile, 'director_profile') or not user.userprofile.director_profile:
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    club = user.userprofile.director_profile.club

    # ✅ Fetch all notifications for the club
    notifications = Notification.objects.filter(club=club).order_by('-created_at')

    # ✅ Ensure only unread notifications are marked as read
    unread_count = notifications.filter(is_read=False).update(is_read=True)

    return render(request, 'club_dashboard/notifications/viewClubNotifications.html', {
        'notifications': notifications,
        'unread_count': unread_count  # ✅ Pass unread count for better UI
    })


def mark_notifications_read(request):
    """Marks all unread notifications as read for the club."""
    user = request.user

    # ✅ Ensure the user has a valid director profile
    if not hasattr(user.userprofile, 'director_profile') or not user.userprofile.director_profile:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized access'}, status=403)

    club = user.userprofile.director_profile.club

    # ✅ Mark only unread notifications as read
    updated_count = Notification.objects.filter(club=club, is_read=False).update(is_read=True)

    return JsonResponse({'status': 'success', 'message': f'Marked {updated_count} notifications as read'})


def salon_appointments(request):
    days = ['السبت', 'الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة']

    # Generate time slots in 12-hour format
    time_slots = []
    for period in ['AM', 'PM']:
        for hour in range(1, 13):  # Use 1-12 range for 12-hour format
            for minute in [0, 30]:
                time_str = f'{hour:02d}:{minute:02d} {period}'
                current_time = datetime.strptime(time_str, '%I:%M %p').time()
                time_slots.append(current_time)

    schedule = {}

    club = get_user_club(request.user)
    if not club:
        messages.error(request, "No club assigned to your profile. Please contact an administrator.")
        return render(request, 'student/blog/viewArticles.html', {
            'schedule': {},
            'days': days,
            'time_slots': [slot.strftime('%I:%M %p') for slot in time_slots]
        })

    for day in days:
        schedule[day] = []
        appointments = SalonAppointment.objects.filter(day=day,club=club).order_by('start_time')

        displayed_appointments = set()

        for slot in time_slots:
            slot_info = {
                'time': slot.strftime('%I:%M %p'),
                'available': True,
                'id': None,
                'booking': None,
                'is_start': False,
                'height': 1
            }

            for appointment in appointments:
                if appointment.start_time and appointment.end_time:
                    if appointment.start_time <= slot < appointment.end_time:
                        slot_info['available'] = False
                        slot_info['id'] = appointment.id

                        if slot == appointment.start_time and appointment.id not in displayed_appointments:
                            displayed_appointments.add(appointment.id)
                            slot_info['is_start'] = True

                            try:
                                booking = appointment.booking
                                start_datetime = datetime.combine(datetime.today(), appointment.start_time)
                                end_datetime = datetime.combine(datetime.today(), appointment.end_time)
                                duration_minutes = (end_datetime - start_datetime).seconds / 60
                                half_hour_blocks = max(1, round(duration_minutes / 30))

                                services = BookingService.objects.filter(booking=booking)
                                service_names = ", ".join([s.service.title for s in services])

                                slot_info['height'] = half_hour_blocks
                                slot_info['booking'] = {
                                    'student_name': booking.student.full_name,
                                    'service': service_names,
                                    'duration': duration_minutes,
                                    'start': appointment.start_time.strftime('%I:%M %p'),
                                    'end': appointment.end_time.strftime('%I:%M %p')
                                }
                            except:
                                slot_info['booking'] = None

                        break

            schedule[day].append(slot_info)

    return render(request, 'club_dashboard/salon_appointments.html', {
        'schedule': schedule,
        'days': days,
        'time_slots': [slot.strftime('%I:%M %p') for slot in time_slots]
    })

@login_required
def appointment_details(request, appointment_id):
    club = get_user_club(request.user)

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم.")
        return redirect('index')

    appointment = get_object_or_404(SalonAppointment, id=appointment_id)
    if appointment.club != club:
        messages.error(request, "ليس لديك صلاحية لعرض هذا الموعد.")
        return redirect('club_salon_appointments')

    try:
        booking = appointment.booking
        # Explicitly fetch booking services
        booking_services = BookingService.objects.filter(booking=booking).select_related('service')

        if not booking_services.exists():
            messages.warning(request, "لا توجد خدمات مرتبطة بهذا الحجز")

        context = {
            'appointment': appointment,
            'booking': booking,
            'student': booking.student,
            'employee': booking.employee,
            'booking_services': booking_services,
            'total_price': sum(bs.service.price for bs in booking_services),
            'total_duration': sum(bs.service.duration for bs in booking_services)
        }
    except Exception as e:
        messages.error(request, f"لم يتم العثور على معلومات الحجز: {str(e)}")
        return redirect('salon_appointments')

    return render(request, 'club_dashboard/appointment_details.html', context)

def reviews_list(request):
    """
    Fetch all reviews for the club associated with the logged-in user.
    """
    # Assuming the logged-in user is a director or admin
    user = request.user

    try:
        # Get the club associated with the logged-in user
        club = user.userprofile.director_profile.club

        # Fetch all reviews for coaches in this club
        reviews = Review.objects.filter(coach__club=club).select_related(
            'student', 'coach'
        ).order_by('-created_at')
        # Calculate average rating for the club
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

        return render(request, 'club_dashboard/reviews_list.html', {
            'reviews': reviews,
            'avg_rating': avg_rating,
            'total_reviews': reviews.count()
        })

    except AttributeError:
        messages.error(request, "لا يمكن العثور على النادي الخاص بك.")
        return redirect('club_dashboard')


def viewReceptionists(request):
    """Displays a list of coaches belonging to the club."""
    user = request.user
    receptionist_userprofile = UserProfile.objects.filter(
        account_type='5',
        receptionist_profile__club=user.userprofile.director_profile.club
    )
    return render(request, 'club_dashboard/receptionists/viewReceptionists.html', {'receptionist_userprofile': receptionist_userprofile})

@login_required
def addReceptionist(request):
    user = request.user

    if not hasattr(user.userprofile, 'director_profile') or not user.userprofile.director_profile:
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    club = user.userprofile.director_profile.club

    # Initialize the correct form
    form = ReceptionistSignupForm(initial={'club': club})

    if request.method == 'POST':
        form = ReceptionistSignupForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
                return redirect('addReceptionist')

            if User.objects.filter(email=email).exists():
                messages.error(request, "Email is already in use.")
                return redirect('addReceptionist')

            receptionist = User.objects.create(username=username, email=email)
            if password:
                receptionist.set_password(password)
            receptionist.save()

            receptionist_profile = ReceptionistProfile.objects.create(
                full_name=form.cleaned_data['full_name'],
                phone=form.cleaned_data['phone'],
                email=email,
                club=form.cleaned_data['club'],  # Get club from form
                about=form.cleaned_data.get('about', "")
            )

            UserProfile.objects.create(user=receptionist, account_type='5', receptionist_profile=receptionist_profile)

            send_notification(user, club, f"📢 A new receptionist {username} has joined {club.name}.")

            messages.success(request, "Receptionist added successfully.")
            return redirect('viewReceptionists')

    return render(request, 'club_dashboard/receptionists/addReceptionist.html', {'form': form})


@login_required
def editReceptionist(request, id):
    """Edits an existing receptionist's details."""
    user = request.user

    if not hasattr(user.userprofile, 'director_profile') or not user.userprofile.director_profile:
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    club = user.userprofile.director_profile.club
    receptionist_profile = get_object_or_404(ReceptionistProfile, id=id)
    receptionist = get_object_or_404(User, userprofile__receptionist_profile=receptionist_profile)

    form = ReceptionistProfileForm(instance=receptionist_profile)

    if request.method == 'POST':
        new_username = request.POST.get('username')
        new_email = request.POST.get('email')
        password = request.POST.get('password')

        form = ReceptionistProfileForm(request.POST, instance=receptionist_profile)
        if form.is_valid():
            username_changed = new_username != receptionist.username
            email_changed = new_email != receptionist.email

            receptionist.username = new_username
            receptionist.email = new_email
            if password:
                receptionist.set_password(password)
            receptionist.save()

            form.save()

            notification_message = f"📝 Receptionist {receptionist.username}'s profile was updated."
            if username_changed or email_changed:
                notification_message += " (Username/Email updated.)"

            send_notification(user, club, notification_message)

            messages.success(request, "Receptionist profile updated successfully.")
            return redirect('viewReceptionists')

    return render(request, 'club_dashboard/receptionists/editReceptionist.html', {
        'form': form,
        'receptionist': receptionist,
    })


@login_required
def deleteReceptionist(request, id):
    """Deletes a receptionist from the club."""
    user = request.user

    if not hasattr(user.userprofile, 'director_profile') or not user.userprofile.director_profile:
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    club = user.userprofile.director_profile.club
    receptionist_profile = get_object_or_404(ReceptionistProfile, id=id)
    receptionist = get_object_or_404(User, userprofile__receptionist_profile=receptionist_profile)

    receptionist_name = receptionist.username

    receptionist_profile.delete()
    receptionist.delete()

    send_notification(user, club, f"🗑️ Receptionist {receptionist_name} has been removed from the club.")

    messages.success(request, "Receptionist has been deleted successfully.")
    return redirect('viewReceptionists')

@login_required
def cancel_appointment(request, appointment_id):
    club = get_user_club(request.user)

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم.")
        return redirect('index')

    appointment = get_object_or_404(SalonAppointment, id=appointment_id)
    if appointment.club != club:
        messages.error(request, "ليس لديك صلاحية لإلغاء هذا الموعد.")
        return redirect('club_salon_appointments')

    try:
        booking = appointment.booking
        BookingService.objects.filter(booking=booking).delete()
        booking.delete()
        appointment.delete()

        messages.success(request, "تم إلغاء الحجز بنجاح")
    except:
        messages.error(request, "لم يتم العثور على حجز لهذا الموعد")

    return redirect('club_salon_appointments')

@login_required
def club_orders(request):
    user = request.user

    if not hasattr(user.userprofile, 'director_profile') or not user.userprofile.director_profile:
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    club = user.userprofile.director_profile.club

    orders = Order.objects.filter(club=club).order_by('-created_at')

    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        orders = orders.filter(status=status_filter)

    context = {
        'orders': orders,
        'status_filter': status_filter or 'all'
    }

    return render(request, 'club_dashboard/orders/club_orders.html', context)

@login_required
def update_order_status(request, order_id):
    user = request.user

    if not hasattr(user.userprofile, 'director_profile') or not user.userprofile.director_profile:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized access'}, status=403)

    club = user.userprofile.director_profile.club

    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id, club=club)
            new_status = request.POST.get('status')

            if new_status not in dict(Order.STATUS_CHOICES):
                return JsonResponse({'status': 'error', 'message': 'Invalid status'}, status=400)

            old_status = order.status
            order.status = new_status
            order.save()

            if new_status == 'confirmed' and old_status == 'pending' and order.payment_method == 'cash_on_delivery':
                order_items = OrderItem.objects.filter(order=order)

                for item in order_items:
                    if item.product:
                        product = item.product
                        product.stock -= item.quantity
                        product.save()

                    if item.service:
                        ServiceOrderModel.objects.create(
                            service=item.service,
                            student=order.user,
                            price=item.service.price * item.quantity,
                            is_complited=False,
                            end_datetime=timezone.now() + timezone.timedelta(days=item.service.subscription_days),
                            creation_date=timezone.now()
                        )

            if new_status == 'confirmed':
                user_notification_message = f"تم تأكيد طلبك رقم #{order.id} وسيتم معالجته قريباً."
            elif new_status == 'cancelled':
                user_notification_message = f"تم إلغاء طلبك رقم #{order.id}. يرجى التواصل مع خدمة العملاء للمزيد من المعلومات."
            elif new_status == 'completed':
                user_notification_message = f"تم اكتمال طلبك رقم #{order.id} بنجاح. شكراً لك!"

            return JsonResponse({'status': 'success', 'message': f'تم تحديث حالة الطلب إلى {dict(Order.STATUS_CHOICES)[new_status]}'})

        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def order_details_api(request, order_id):
    user = request.user
    print(f"طلب تفاصيل الطلب {order_id} بواسطة {user}")

    try:
        if not hasattr(user.userprofile, 'director_profile') or not user.userprofile.director_profile:
            print("غير مصرح به")
            return JsonResponse({'status': 'error', 'message': 'Unauthorized access'}, status=403)

        club = user.userprofile.director_profile.club

        order = Order.objects.get(id=order_id, club=club)
        order_items = OrderItem.objects.filter(order=order)

        context = {
            'order': order,
            'order_items': order_items,
        }

        html = render_to_string('club_dashboard/orders/order_details_modal.html', context)

        return JsonResponse({
            'status': 'success',
            'html': html
        })
    except Order.DoesNotExist:
        print(f"الطلب {order_id} غير موجود")
        return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)
    except Exception as e:
        print(f"خطأ غير متوقع: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def add_shipment(request):
    user = request.user
    club = user.userprofile.director_profile.club

    if request.method == 'POST':
        form = ProductShipmentForm(request.POST, club=club)
        if form.is_valid():
            shipment = form.save()

            product = shipment.product
            product.stock += shipment.quantity

            if shipment.manufacturing_date and not product.manufacturing_date:
                product.manufacturing_date = shipment.manufacturing_date

            if shipment.expiration_date:
                if not product.expiration_date or shipment.expiration_date > product.expiration_date:
                    product.expiration_date = shipment.expiration_date

            product.save()

            messages.success(request, 'تم إضافة الشحنة بنجاح!')
            return redirect('view_product_shipments', product_id=shipment.product.id)
    else:
        form = ProductShipmentForm(club=club)

    product_id = request.GET.get('product_id')
    if product_id:
        try:
            product = ProductsModel.objects.get(id=product_id, club=club)
            form.initial['product'] = product
        except ProductsModel.DoesNotExist:
            pass

    context = {
        'form': form,
    }
    return render(request, 'club_dashboard/products/ProductsStock/add_shipment.html', context)

def view_product_shipments(request, product_id):
    user = request.user
    club = user.userprofile.director_profile.club

    try:
        product = ProductsModel.objects.get(id=product_id, club=club)
    except ProductsModel.DoesNotExist:
        messages.error(request, 'المنتج غير موجود!')
        return redirect('viewProducts')

    shipments = ProductShipment.objects.filter(product=product).order_by('-created_at')

    expiring_soon_count = sum(1 for s in shipments if s.is_expiring_soon)
    expired_count = sum(1 for s in shipments if s.is_expired)
    valid_count = len(shipments) - expiring_soon_count - expired_count

    total_quantity = sum(s.quantity for s in shipments)
    expiring_soon_quantity = sum(s.quantity for s in shipments if s.is_expiring_soon)
    expired_quantity = sum(s.quantity for s in shipments if s.is_expired)
    valid_quantity = total_quantity - expiring_soon_quantity - expired_quantity

    context = {
        'product': product,
        'shipments': shipments,
        'stats': {
            'total_count': len(shipments),
            'expiring_soon_count': expiring_soon_count,
            'expired_count': expired_count,
            'valid_count': valid_count,
            'total_quantity': total_quantity,
            'expiring_soon_quantity': expiring_soon_quantity,
            'expired_quantity': expired_quantity,
            'valid_quantity': valid_quantity,
        }
    }
    return render(request, 'club_dashboard/products/ProductsStock/view_product_shipments.html', context)

def product_details(request, product_id):
    user = request.user
    club = user.userprofile.director_profile.club

    try:
        product = ProductsModel.objects.get(id=product_id, club=club)
    except ProductsModel.DoesNotExist:
        messages.error(request, 'المنتج غير موجود!')
        return redirect('viewProducts')

    product_images = product.product_images.all()

    shipments = ProductShipment.objects.filter(product=product).order_by('-created_at')

    expiring_soon_count = sum(1 for s in shipments if s.is_expiring_soon)
    expired_count = sum(1 for s in shipments if s.is_expired)
    valid_count = len(shipments) - expiring_soon_count - expired_count

    total_quantity = sum(s.quantity for s in shipments)
    expiring_soon_quantity = sum(s.quantity for s in shipments if s.is_expiring_soon)
    expired_quantity = sum(s.quantity for s in shipments if s.is_expired)
    valid_quantity = total_quantity - expiring_soon_quantity - expired_quantity

    context = {
        'product': product,
        'product_images': product_images,
        'shipments': shipments,
        'stats': {
            'total_count': len(shipments),
            'expiring_soon_count': expiring_soon_count,
            'expired_count': expired_count,
            'valid_count': valid_count,
            'total_quantity': total_quantity,
            'expiring_soon_quantity': expiring_soon_quantity,
            'expired_quantity': expired_quantity,
            'valid_quantity': valid_quantity,
        }
    }

    return render(request, 'club_dashboard/products/ProductsStock/product_details.html', context)


@login_required
def club_financial_dashboard(request):
    user = request.user

    if not hasattr(user.userprofile, 'director_profile') or not user.userprofile.director_profile:
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    club = user.userprofile.director_profile.club

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date:
        start_date = (timezone.now() - timezone.timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')

    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
    except ValueError:
        start_date_obj = timezone.now() - timezone.timedelta(days=30)
        end_date_obj = timezone.now()

    orders = Order.objects.filter(
        club=club,
        created_at__gte=start_date_obj,
        created_at__lte=end_date_obj
    ).order_by('-created_at')

    credit_card_orders = orders.filter(payment_method='credit_card')
    cash_orders = orders.filter(payment_method='cash_on_delivery')

    total_revenue = orders.filter(status__in=['confirmed', 'completed']).aggregate(Sum('total_price'))['total_price__sum'] or 0
    pending_revenue = orders.filter(status='pending').aggregate(Sum('total_price'))['total_price__sum'] or 0

    credit_card_revenue = credit_card_orders.filter(status__in=['confirmed', 'completed']).aggregate(Sum('total_price'))['total_price__sum'] or 0
    cash_revenue = cash_orders.filter(status__in=['confirmed', 'completed']).aggregate(Sum('total_price'))['total_price__sum'] or 0

    total_confirmed_revenue = total_revenue
    credit_card_percentage = 0
    cash_percentage = 0
    if total_confirmed_revenue > 0:
        credit_card_percentage = round((credit_card_revenue / total_confirmed_revenue) * 100)
        cash_percentage = round((cash_revenue / total_confirmed_revenue) * 100)

    months_data = []
    for i in range(6):
        month_date = timezone.now() - timezone.timedelta(days=30 * i)
        month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month_date.month == 12:
            month_end = month_date.replace(year=month_date.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0) - timezone.timedelta(seconds=1)
        else:
            month_end = month_date.replace(month=month_date.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0) - timezone.timedelta(seconds=1)

        month_orders = Order.objects.filter(
            club=club,
            created_at__gte=month_start,
            created_at__lte=month_end,
            status__in=['confirmed', 'completed']
        )

        month_credit = month_orders.filter(payment_method='credit_card').aggregate(Sum('total_price'))['total_price__sum'] or 0
        month_cash = month_orders.filter(payment_method='cash_on_delivery').aggregate(Sum('total_price'))['total_price__sum'] or 0

        months_data.append({
            'month': month_start.strftime('%B %Y'),
            'credit_card': float(month_credit),
            'cash': float(month_cash),
            'total': float(month_credit + month_cash)
        })

    months_data.reverse()

    order_items = OrderItem.objects.filter(order__club=club, order__status__in=['confirmed', 'completed'])

    product_sales = {}
    service_sales = {}

    for item in order_items:
        if item.product:
            product_id = item.product.id
            product_name = item.product.title
            if product_id in product_sales:
                product_sales[product_id]['quantity'] += item.quantity
                product_sales[product_id]['revenue'] += float(item.price * item.quantity)
            else:
                product_sales[product_id] = {
                    'name': product_name,
                    'quantity': item.quantity,
                    'revenue': float(item.price * item.quantity)
                }

        if item.service:
            service_id = item.service.id
            service_name = item.service.title
            if service_id in service_sales:
                service_sales[service_id]['quantity'] += item.quantity
                service_sales[service_id]['revenue'] += float(item.price * item.quantity)
            else:
                service_sales[service_id] = {
                    'name': service_name,
                    'quantity': item.quantity,
                    'revenue': float(item.price * item.quantity)
                }

    top_products = sorted([v for k, v in product_sales.items()], key=lambda x: x['revenue'], reverse=True)[:5]
    top_services = sorted([v for k, v in service_sales.items()], key=lambda x: x['revenue'], reverse=True)[:5]

    context = {
        'all_orders': orders,
        'orders': orders,
        'credit_card_orders': credit_card_orders,
        'cash_orders': cash_orders,
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'credit_card_revenue': credit_card_revenue,
        'cash_revenue': cash_revenue,
        'credit_card_percentage': credit_card_percentage,
        'cash_percentage': cash_percentage,
        'start_date': start_date,
        'end_date': end_date,
        'months_data': json.dumps(months_data),
        'top_products': top_products,
        'top_services': top_services,
    }

    return render(request, 'club_dashboard/financial/dashboard.html', context)


