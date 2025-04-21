from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Avg, Sum, F, ExpressionWrapper, DecimalField
from django.contrib import messages
from club_dashboard.models import SalonAppointment,Notification
from django.core.paginator import Paginator
from receptionist_dashboard.models import SalonBooking,BookingService
from django.db import models , transaction
from datetime import datetime, timedelta
from django.forms import formset_factory
from django.contrib.auth.decorators import login_required
from receptionist_dashboard.forms import SalonBookingForm ,ServiceSelectionForm
from django.http import JsonResponse
from .models import ProductsModel , CartItem,ServiceCartItem,OrderItem,Order
from accounts.models import UserProfile,StudentProfile
from django import forms
import base64
from decimal import Decimal



# Import necessary models
from .models import (
    Blog, ServicesModel, ServicesClassificationModel,
    ProductsModel, ProductsClassificationModel, ServiceOrderModel, UserProfile
)
from club_dashboard.models import Review  # ✅ Import Review from club_dashboard
from accounts.models import ClubsModel, CoachProfile, StudentProfile
from coach_dashboard.models import StudentAppointmentPresenceModel, CoachAppointmentsModel

# Import necessary forms
from .forms import ReviewForm


# from django.contrib import messages

import datetime
# Create your views here.

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


def index(request):
    user = request.user
    print(f"User authenticated: {user.is_authenticated}")

    try:
        userprofile = UserProfile.objects.get(user=user)
        student = userprofile.student_profile
        print(f"User: {user}, Profile: {getattr(user, 'userprofile', None)}")
        print(f"Student Profile: {getattr(userprofile, 'student_profile', None) if 'userprofile' in locals() else None}")
        print(f"Club: {getattr(student, 'club', None) if 'student' in locals() else None}")

        if not student:
            messages.error(request, "No student profile found for this user.")
            return redirect('signin')  # or an appropriate error page

        club = student.club

        if not club:
            messages.error(request, "No club associated with this student.")
            return redirect('signin')  # or an appropriate error page

        coaches = CoachProfile.objects.filter(club=club)
        students = StudentProfile.objects.filter(club=club)

        # Check subscription status
        subscription_status = student.get_subscription_status()

        # Activate a 30-day subscription when a student signs up (if they don’t have one)
        if not student.subscription_start_date:
            student.subscription_start_date = timezone.now()
            student.subscription_end_date = timezone.now() + datetime.timedelta(days=30)
            student.has_subscription = True
            student.save()

        # Fetch all services and products related to the club
        services = ServicesModel.objects.filter(club=club)
        products = ProductsModel.objects.filter(club=club)

        # Show appointments only if the student has an active subscription
        if subscription_status == "active" or subscription_status == "expiring_soon":
            appointments = CoachAppointmentsModel.objects.filter(coach__club=club)
        else:
            appointments = []  # Empty list if subscription is expired

        return render(request, 'student/index.html', {
            'coaches': coaches,
            'students': students,
            'club': club,
            'services': services,
            'products': products,
            'appointments': appointments,
            'subscription_status': subscription_status,
            'subscription_end_date': student.subscription_end_date,
        })

    except UserProfile.DoesNotExist:
        print(f"UserProfile.DoesNotExist: {str(e)}")
        messages.error(request, "User profile not found.")
        return redirect('signin')  # or an appropriate error page
    except Exception as e:
        print(f"Unexpected exception: {str(e)}")
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('signin')  # or an appropriate error page




def viewProducts(request):
    products = ProductsModel.objects.all()
    # classifications = ClassificationModel.objects.all()  # Get all available classifications

    total_products = products.count()
    total_value = 0
    low_stock_count = 0
    out_of_stock_count = 0
    low_stock_threshold = 10

    for product in products:
        if hasattr(product, 'stock'):
            product_value = product.price * product.stock
            total_value += product_value

            if 0 < product.stock <= low_stock_threshold:
                low_stock_count += 1

            if product.stock == 0:
                out_of_stock_count += 1

    paginator = Paginator(products, 6)
    page_number = request.GET.get('page', 1)
    paginated_products = paginator.get_page(page_number)

    context = {
        'products': paginated_products,
        # 'classifications': classifications,
        'total_products': total_products,
        'total_value': total_value,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
    }

    return render(request, 'student/products/viewProducts.html', context)

def extract_features(description):
    """Helper function to extract product features from description"""
    if description:
        return [
            "مصنوعة من مواد فائقة الجودة",
            "تصميم عصري وأنيق",
            "سهولة الاستخدام",
            "ضمان لمدة سنة"
        ]
    return []

def viewProductsSpecific(request, id):
    user = request.user
    club = user.userprofile.student_profile.club

    product = ProductsModel.objects.get(id=id)

    product.features = extract_features(product.desc)

    from datetime import timedelta
    from django.utils import timezone
    product.is_new = product.created_at >= timezone.now() - timedelta(days=7) if hasattr(product, 'created_at') else False

    related_products = ProductsModel.objects.filter(club=club).exclude(id=id)[:3]

    context = {
        'product': product,
        'products': related_products,
    }

    return render(request, 'student/products/viewSpecific.html', context)



def viewServices(request):
    user = request.user
    club = user.userprofile.student_profile.club
    services = ServicesModel.objects.filter(club=club)
    classifications = ProductsClassificationModel.objects.filter(club=club)

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
        'classifications': classifications,
        'avg_price': avg_price,
        'avg_duration_hours': avg_duration_hours,
        'avg_duration_minutes': avg_duration_minutes,
    }

    return render(request, 'student/services/viewServices.html', context)

def viewServicesSpecific(request, id):
    user = request.user
    club = user.userprofile.student_profile.club
    service = ServicesModel.objects.get(id=id)
    services = ServicesModel.objects.filter(club=club)
    order = ServiceOrderModel.objects.filter(service=service, student=user).order_by('-id').first()
    return render(request, 'student/services/viewSpecific.html', {'service':service, 'services':services, 'order':order})


def viewArticles(request):
    user = request.user
    club = user.userprofile.student_profile.club
    arts = Blog.objects.filter(club=club)
    featured_article = arts.order_by('-creation_date').first()

    context = {
        'arts': arts,
        'featured_article': featured_article
    }

    return render(request, 'student/blog/viewArticless.html', context)

def viewArticle(request,id):
    user = request.user
    club = user.userprofile.student_profile.club

    try:
        article = Blog.objects.get(id=id, club=club)

        related_articles = Blog.objects.filter(club=club).exclude(id=id)[:3]

        context = {
            'article': article,
            'related_articles': related_articles
        }

        return render(request, 'student/blog/viewArticle.html', context)

    except Blog.DoesNotExist:
        return redirect('viewArticles')


def OrderService(request, service_id):
    student = request.user
    service = ServicesModel.objects.get(id=service_id)
    orders = ServiceOrderModel.objects.filter(service=service, student=student).order_by('-id')
    if orders.exists():
        if orders.first().has_subscription():
            return redirect('viewServicesSpecific', service_id)
    end_datetime = datetime.timedelta(days=30) + timezone.now()
    order = ServiceOrderModel.objects.create(service=service, student=student, price=service.price, is_complited=True, end_datetime=end_datetime, creation_date=timezone.now())
    order.save()
    return redirect('studentIndex')

def add_review(request):
    """Allows a student to review any coach in their club."""
    user = request.user

    # ✅ Ensure user has a valid StudentProfile
    student_profile = getattr(user.userprofile, 'student_profile', None)
    if not student_profile:
        messages.error(request, "❌ لم يتم العثور على ملف الطالب الخاص بك.")
        return redirect('studentIndex')

    club = student_profile.club
    if not club:
        messages.error(request, "❌ أنت غير مسجل في أي نادٍ.")
        return redirect('studentIndex')

    # ✅ Get all coaches in the club
    coaches = CoachProfile.objects.filter(club=club)

    if request.method == 'POST':
        selected_coach_id = request.POST.get('coach_id')

        if not selected_coach_id:
            messages.error(request, "❌ يرجى اختيار مدرب لإضافة تقييم.")
            return redirect('add_review')

        # ✅ Check if the coach exists
        coach_profile = get_object_or_404(CoachProfile, id=selected_coach_id)

        # ✅ Check if the student already reviewed this coach
        existing_review = Review.objects.filter(student=student_profile, coach=coach_profile).first()

        # ✅ Use form with instance for updating existing review
        form = ReviewForm(request.POST, instance=existing_review)

        if form.is_valid():
            review = form.save(commit=False)
            review.student = student_profile
            review.coach = coach_profile
            review.save()

            messages.success(request, "✅ تم إرسال التقييم بنجاح!")
            return redirect('view_reviews')
        else:
            messages.error(request, f"❌ حدث خطأ أثناء إرسال التقييم: {form.errors}")
    else:
        form = ReviewForm()

    return render(request, 'student/reviews/add_review.html', {
        'form': form,
        'coaches': coaches  # ✅ Correctly passing only relevant coaches
    })
    
def view_reviews(request):
    """Displays the reviews written by the logged-in student."""
    user = request.user

    # ✅ Ensure user has a valid UserProfile and StudentProfile
    try:
        student_profile = user.userprofile.student_profile
    except AttributeError:
        messages.error(request, "لم يتم العثور على ملف الطالب الخاص بك.")
        return redirect('studentIndex')

    # ✅ Fetch only the reviews this student wrote
    student_reviews = Review.objects.filter(student=student_profile).select_related('coach').order_by('-created_at')

    return render(request, 'student/reviews/view_reviews.html', {
        'student_reviews': student_reviews,
    })
      
def edit_review(request, review_id):
    """Allows a student to edit their existing review."""
    user = request.user
    review = get_object_or_404(Review, id=review_id, student=user.userprofile.student_profile)

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تعديل التقييم بنجاح!")
            return redirect('view_reviews')
    else:
        form = ReviewForm(instance=review)

    return render(request, 'student/reviews/edit_review.html', {'form': form, 'review': review})


def salon_appointments(request):
    days = ['السبت', 'الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة']

    time_slots = []
    for hour in range(1, 13):
        for minute in [0, 30]:
            current_time = datetime.datetime.strptime(f'{hour:02d}:{minute:02d}:00 AM', '%I:%M:%S %p').time()
            time_slots.append(current_time)
    for hour in range(1, 13):
        for minute in [0, 30]:
            current_time = datetime.datetime.strptime(f'{hour:02d}:{minute:02d}:00 PM', '%I:%M:%S %p').time()
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
                                start_datetime = datetime.datetime.combine(datetime.datetime.today(), appointment.start_time)
                                end_datetime = datetime.datetime.combine(datetime.datetime.today(), appointment.end_time)
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

    return render(request, 'student/blog/viewArticles.html', {
        'schedule': schedule,
        'days': days,
        'time_slots': [slot.strftime('%I:%M %p') for slot in time_slots]
    })

@login_required
def select_appointment_day(request):
    club = get_user_club(request.user)
    if not club:
        messages.error(request, "No club assigned to your profile. Please contact an administrator.")
        return redirect('index')

    days = ['السبت', 'الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة']

    if request.method == 'POST':
        selected_day = request.POST.get('day')
        return redirect('client_book_appointment_details', day=selected_day)

    return render(request, 'student/blog/select_appointment_day.html', {
        'days': days
    })

@login_required
def book_appointment_details(request, day):
    club = get_user_club(request.user)
    if not club:
        messages.error(request, "No club assigned to your profile. Please contact an administrator.")
        return redirect('index')
    ServiceFormSet = formset_factory(ServiceSelectionForm, extra=1)

    appointments = []
    day_appointments = SalonAppointment.objects.filter(
        day=day,
        available=False,
        club=club,
    ).order_by('start_time')

    try:
        student_profile = request.user.userprofile.student_profile
    except AttributeError:
        messages.error(request, "لم يتم العثور على ملف الطالب الخاص بك.")
        return redirect('studentIndex')

    for appointment in day_appointments:
        try:
            booking = appointment.booking
            services = BookingService.objects.filter(booking=booking)
            service_names = ", ".join([s.service.title for s in services])

            start_datetime = datetime.datetime.combine(datetime.datetime.today(), appointment.start_time)
            end_datetime = datetime.datetime.combine(datetime.datetime.today(), appointment.end_time)
            total_duration = (end_datetime - start_datetime).seconds / 60

            appointments.append({
                'start_time': appointment.start_time,
                'end_time': appointment.end_time,
                'client_name': booking.student.full_name,
                'employee_name': booking.employee,
                'total_duration': total_duration,
                'services': service_names
            })
        except:
            # Skip appointments without valid booking information
            continue

    if request.method == 'POST':
        booking_form = SalonBookingForm(request.POST)
        service_formset = ServiceFormSet(request.POST, prefix='services')

        booking_form.data = booking_form.data.copy()
        booking_form.data['student'] = student_profile.id

        if booking_form.is_valid() and service_formset.is_valid():
            total_duration = 0
            for form in service_formset:
                if form.cleaned_data and form.cleaned_data.get('service'):
                    total_duration += form.cleaned_data['service'].duration

            booking_data = {
                'student_id': student_profile.id,
                'employee_id': booking_form.cleaned_data['employee'].id if booking_form.cleaned_data.get('employee') else None,
                'employee_name': booking_form.cleaned_data.get('employee_name', '')
            }

            request.session['booking_form_data'] = booking_data

            services_data = []
            for form in service_formset:
                if form.cleaned_data and form.cleaned_data.get('service'):
                    services_data.append(form.cleaned_data['service'].id)

            request.session['service_ids'] = services_data
            request.session['total_duration'] = total_duration

            return redirect('client_select_appointment_time', day=day)
        else:
            messages.error(request, "هناك خطأ في البيانات المدخلة. الرجاء التحقق والمحاولة مرة أخرى.")
            print(f"Form errors: {booking_form.errors}")
            print(f"Formset errors: {service_formset.errors}")
    else:
        booking_form = SalonBookingForm(initial={'student': student_profile.id})
        service_formset = ServiceFormSet(prefix='services')

    return render(request, 'student/blog/book_appointment_details.html', {
        'booking_form': booking_form,
        'service_formset': service_formset,
        'day': day,
        'appointments': appointments,
        'current_user': request.user
    })


@login_required
def select_appointment_time(request, day):
    club = get_user_club(request.user)
    if not club:
        messages.error(request, "No club assigned to your profile. Please contact an administrator.")
        return redirect('index')

    # arabic_day_mapping = {
    #     'السبت': 5,
    #     'الأحد': 6,
    #     'الاثنين': 0,
    #     'الثلاثاء': 1,
    #     'الأربعاء': 2,
    #     'الخميس': 3,
    #     'الجمعة': 4,
    # }
    #
    # today = datetime.datetime.now().date()
    #
    # if day in arabic_day_mapping:
    #     days_ahead = arabic_day_mapping[day] - today.weekday()
    #     if days_ahead <= 0:
    #         days_ahead += 7
    #     day_date = today + datetime.timedelta(days=days_ahead)
    # else:
    #     try:
    #         day_date = datetime.datetime.strptime(day, '%Y-%m-%d').date()
    #     except ValueError:
    #         messages.error(request, f"Invalid day format: {day}")
    #         return redirect('index')

    time_slots = []
    for hour in range(1, 13):
        for minute in [0, 30]:
            time = datetime.datetime.strptime(f'{hour:02d}:{minute:02d}:00 AM', '%I:%M:%S %p').time()
            time_slots.append(time)
    for hour in range(1, 13):
        for minute in [0, 30]:
            time = datetime.datetime.strptime(f'{hour:02d}:{minute:02d}:00 PM', '%I:%M:%S %p').time()
            time_slots.append(time)

    total_duration = request.session.get('total_duration', 0)

    available_slots = []
    for time in time_slots:
        is_available = True

        start_datetime = datetime.datetime.combine(datetime.datetime.today(), time)
        end_datetime = start_datetime + timedelta(minutes=total_duration)
        end_time = end_datetime.time()

        appointments = SalonAppointment.objects.filter(
            day=day,
            available=False,
            club=club,
        ).filter(
            models.Q(start_time__lt=end_time, end_time__gt=time)
        )

        if appointments.exists():
            is_available = False

        if is_available:
            hour = time.hour
            minute = time.minute
            period = 'AM' if time.hour < 12 else 'PM'
            display_hour = hour if hour <= 12 else hour - 12
            if display_hour == 0:
                display_hour = 12

            end_hour = end_time.hour
            end_minute = end_time.minute
            end_period = 'AM' if end_time.hour < 12 else 'PM'
            end_display_hour = end_hour if end_hour <= 12 else end_hour - 12
            if end_display_hour == 0:
                end_display_hour = 12

            available_slots.append({
                'time': f'{display_hour:02d}:{minute:02d} {period}',
                'available': True,
                'end_time': f'{end_display_hour:02d}:{end_minute:02d} {end_period}'
            })

    return render(request, 'student/blog/select_appointment_time.html', {
        'day': day,
        'time_slots': available_slots,
        'total_duration': total_duration
    })

@login_required
def verify_and_book_appointment(request, day):
    club = get_user_club(request.user)

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم.")
        return redirect('index')

    if request.method != 'POST':
        return redirect('client_select_appointment_time', day=day)

    time_input = request.POST.get('time_input')
    period = request.POST.get('period')

    if not time_input or not period:
        messages.error(request, "يرجى إدخال الوقت والفترة")
        return redirect('client_select_appointment_time', day=day)

    try:
        if ':' in time_input:
            hours, minutes = time_input.split(':')
            hours = int(hours)
            minutes = int(minutes)
        if hours < 1 or hours > 12:
            messages.error(request, "صيغة الوقت غير صحيحة. يجب أن تكون الساعة من 1 إلى 12")
            return redirect('client_select_appointment_time', day=day)

        if period == 'PM' and hours < 12:
            hours += 12
        elif period == 'AM' and hours == 12:
            hours = 0

        time_obj = datetime.datetime.strptime(f'{hours:02d}:{minutes:02d}:00', '%H:%M:%S').time()
    except ValueError:
        messages.error(request, "صيغة الوقت غير صحيحة. الرجاء استخدام الصيغة HH:MM")
        return redirect('client_select_appointment_time', day=day)

    booking_form_data = request.session.get('booking_form_data', {})
    service_ids = request.session.get('service_ids', [])
    total_duration = request.session.get('total_duration', 0)

    if not booking_form_data or not service_ids:
        messages.error(request, "بيانات الحجز غير مكتملة. الرجاء المحاولة مرة أخرى.")
        return redirect('client_select_appointment_day')

    # Handle Arabic day names
    # arabic_day_mapping = {
    #     'السبت': 5,  # Saturday
    #     'الأحد': 6,  # Sunday
    #     'الاثنين': 0,  # Monday
    #     'الثلاثاء': 1,  # Tuesday
    #     'الأربعاء': 2,  # Wednesday
    #     'الخميس': 3,  # Thursday
    #     'الجمعة': 4,  # Friday
    # }
    #
    # # Convert day name to date object if needed
    # if day in arabic_day_mapping:
    #     today = datetime.datetime.now().date()
    #     days_ahead = arabic_day_mapping[day] - today.weekday()
    #     if days_ahead <= 0:  # Target day already happened this week
    #         days_ahead += 7
    #     day_date = today + datetime.timedelta(days=days_ahead)
    # else:
    #     # Try to parse as date if not a day name
    #     try:
    #         day_date = datetime.datetime.strptime(day, '%Y-%m-%d').date()
    #     except ValueError:
    #         messages.error(request, f"صيغة اليوم غير صحيحة: {day}")
    #         return redirect('client_select_appointment_day')

    start_datetime = datetime.datetime.combine(datetime.datetime.today(), time_obj)
    end_datetime = start_datetime + timedelta(minutes=total_duration)
    end_time = end_datetime.time()

    conflicts = SalonAppointment.objects.filter(
        day=day,
        available=False,
        club=club,
    ).filter(
        models.Q(start_time__lt=end_time, end_time__gt=time_obj)
    )

    if conflicts.exists():
        messages.error(request, "هذا الوقت غير متاح. يرجى اختيار وقت آخر.")
        return redirect('client_select_appointment_time', day=day)

    try:
        with transaction.atomic():
            appointment = SalonAppointment.objects.create(
                day=day,
                start_time=time_obj,
                end_time=end_time,
                available=False,
                club=club,
            )

            student_id = booking_form_data.get('student_id')

            if not student_id:
                messages.error(request, "بيانات العميل غير متوفرة. الرجاء المحاولة مرة أخرى.")
                return redirect('client_select_appointment_day')

            try:
                student = StudentProfile.objects.get(id=student_id)
            except StudentProfile.DoesNotExist:
                messages.error(request, "لم يتم العثور على العميل. الرجاء المحاولة مرة أخرى.")
                return redirect('client_select_appointment_day')

            employee_id = booking_form_data.get('employee_id')
            employee = booking_form_data.get('employee_name', '')

            if not employee:
                from accounts.models import CoachProfile
                try:
                    coach = CoachProfile.objects.get(id=employee_id)
                    employee = coach.full_name
                except:
                    employee = "غير محدد"

            booking = SalonBooking.objects.create(
                appointment=appointment,
                student=student,
                employee=employee,
                created_at=datetime.datetime.now()
            )

            for service_id in service_ids:
                service = ServicesModel.objects.get(id=service_id)
                BookingService.objects.create(
                    booking=booking,
                    service=service
                )
                cart_item, created = ServiceCartItem.objects.get_or_create(
                    user=request.user,
                    service=service,
                    defaults={'quantity': 1}
                )
                if not created:
                    cart_item.quantity += 1
                    cart_item.save()

            messages.success(request, "تم حجز الموعد بنجاح وإضافة الخدمة إلى سلة التسوق")

            if 'booking_form_data' in request.session:
                del request.session['booking_form_data']
            if 'service_ids' in request.session:
                del request.session['service_ids']
            if 'total_duration' in request.session:
                del request.session['total_duration']

            return redirect('studentViewArticles')

    except Exception as e:
        messages.error(request, f"حدث خطأ أثناء الحجز: {str(e)}")
        return redirect('client_select_appointment_time', day=day)

@login_required
def get_service_duration(request, service_id):
    try:
        service = ServicesModel.objects.get(id=service_id)
        return JsonResponse({'duration': service.duration})
    except ServicesModel.DoesNotExist:
        return JsonResponse({'duration': 0})



@login_required
def book_appointment(request, day, time_slot):
    club = get_user_club(request.user)

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم.")
        return redirect('client_select_appointment_day')

    booking_form_data = request.session.get('booking_form_data', {})
    service_ids = request.session.get('service_ids', [])
    total_duration = request.session.get('total_duration', 0)

    if not booking_form_data or not service_ids:
        messages.error(request, "بيانات الحجز غير مكتملة. الرجاء المحاولة مرة أخرى.")
        return redirect('client_select_appointment_day')

    try:
        time_parts = time_slot.split()
        time_str = time_parts[0]
        period = time_parts[1]

        hours, minutes = time_str.split(':')
        hours = int(hours)
        minutes = int(minutes)

        if period == 'PM' and hours < 12:
            hours += 12
        elif period == 'AM' and hours == 12:
            hours = 0

        time_obj = datetime.strptime(f'{hours:02d}:{minutes:02d}:00', '%H:%M:%S').time()
    except (ValueError, IndexError):
        messages.error(request, "صيغة الوقت غير صحيحة")
        return redirect('select_appointment_time', day=day)

    start_datetime = datetime.datetime.combine(datetime.datetime.today(), time_obj)
    end_datetime = start_datetime + timedelta(minutes=total_duration)
    end_time = end_datetime.time()

    conflicts = SalonAppointment.objects.filter(
        day=day,
        available=False,
        club=club
    ).filter(
        models.Q(start_time__lt=end_time, end_time__gt=time_obj)
    )

    if conflicts.exists():
        messages.error(request, "هناك تعارض في المواعيد. الرجاء اختيار وقت آخر")
        return redirect('client_select_appointment_time', day=day)

    try:
        with transaction.atomic():
            appointment = SalonAppointment.objects.create(
                day=day,
                start_time=time_obj,
                end_time=end_time,
                available=False,
                club=club
            )

            student_id = booking_form_data.get('student_id')
            employee_id = booking_form_data.get('employee_id')

            if not student_id:
                messages.error(request, "بيانات العميل غير متوفرة. الرجاء المحاولة مرة أخرى.")
                return redirect('client_select_appointment_day')

            try:
                student = StudentProfile.objects.get(id=student_id)
            except StudentProfile.DoesNotExist:
                messages.error(request, "لم يتم العثور على العميل. الرجاء المحاولة مرة أخرى.")
                return redirect('client_select_appointment_day')

            employee = booking_form_data.get('employee_name', '')

            if not employee:
                from accounts.models import CoachProfile
                try:
                    coach = CoachProfile.objects.get(id=employee_id)
                    employee = coach.full_name
                except:
                    employee = "غير محدد"

            booking = SalonBooking.objects.create(
                appointment=appointment,
                student=student,
                employee=employee,
                created_at=datetime.datetime.now()
            )

            for service_id in service_ids:
                service = ServicesModel.objects.get(id=service_id)
                BookingService.objects.create(
                    booking=booking,
                    service=service
                )

            messages.success(request, "تم حجز الموعد بنجاح")

            if 'booking_form_data' in request.session:
                del request.session['booking_form_data']
            if 'service_ids' in request.session:
                del request.session['service_ids']
            if 'total_duration' in request.session:
                del request.session['total_duration']

            return redirect('studentViewArticles')
    except Exception as e:
        messages.error(request, f"حدث خطأ أثناء الحجز: {str(e)}")
        return redirect('client_select_appointment_day')

@login_required
def appointment_details(request, appointment_id):
    club = get_user_club(request.user)

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم.")
        return redirect('index')

    appointment = get_object_or_404(SalonAppointment, id=appointment_id)
    if appointment.club != club:
        messages.error(request, "ليس لديك صلاحية لعرض هذا الموعد.")
        return redirect('studentViewArticles')

    try:
        booking = appointment.booking
        # Explicitly fetch booking services
        booking_services = BookingService.objects.filter(booking=booking).select_related('service')

        if not booking_services.exists():
            messages.warning(request, "لا توجد خدمات مرتبطة بهذا الحجز")

        # For debugging
        print(f"Found {booking_services.count()} services for booking {booking.id}")

        context = {
            'appointment': appointment,
            'booking': booking,
            'student': booking.student,
            'employee': booking.employee,
            'booking_services': booking_services,
            'total_price': sum(bs.service.price for bs in booking_services),
            'total_duration': sum(bs.service.duration for bs in booking_services),
            'start_time': appointment.start_time.strftime('%I:%M %p'),
            'end_time': appointment.end_time.strftime('%I:%M %p')
        }
    except Exception as e:
        messages.error(request, f"لم يتم العثور على معلومات الحجز: {str(e)}")
        return redirect('studentViewArticles')

    return render(request, 'student/blog/appointment_details.html', context)


@login_required
def cancel_appointment(request, appointment_id):
    club = get_user_club(request.user)

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم.")
        return redirect('index')

    appointment = get_object_or_404(SalonAppointment, id=appointment_id)
    if appointment.club != club:
        messages.error(request, "ليس لديك صلاحية لإلغاء هذا الموعد.")
        return redirect('studentViewArticles')

    try:
        booking = appointment.booking
        BookingService.objects.filter(booking=booking).delete()
        booking.delete()
        appointment.delete()

        messages.success(request, "تم إلغاء الحجز بنجاح")
    except:
        messages.error(request, "لم يتم العثور على حجز لهذا الموعد")

    return redirect('studentViewArticles')


@login_required
def add_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))

        # Get the product
        product = get_object_or_404(ProductsModel, id=product_id)

        # Check if stock is available
        if product.stock < quantity:
            return JsonResponse({
                'success': False,
                'message': 'لا يوجد مخزون كافي'
            })

        # Check if item already in cart
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )

        # If item already exists, update quantity
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        # Get cart count for navbar badge
        cart_count = CartItem.objects.filter(user=request.user).aggregate(
            total=Sum('quantity'))['total'] or 0

        return JsonResponse({
            'success': True,
            'message': 'تمت إضافة المنتج إلى السلة',
            'cart_count': cart_count
        })

    return JsonResponse({'success': False, 'message': 'Invalid request'})

# Cart Page View
@login_required
def cart(request):
    product_items = CartItem.objects.filter(user=request.user)
    service_items = ServiceCartItem.objects.filter(user=request.user)

    # Calculate total price
    product_total = sum(item.total_price for item in product_items)
    service_total = sum(item.total_price for item in service_items)
    total_price = product_total + service_total

    context = {
        'product_items': product_items,
        'service_items': service_items,
        'product_total': product_total,
        'service_total': service_total,
        'total_price': total_price
    }

    return render(request, 'student/cart/cart.html', context)

# Update Cart Quantity
@login_required
def update_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')

        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)

        if action == 'increase':
            # Check stock availability
            if cart_item.quantity >= cart_item.product.stock:
                return JsonResponse({
                    'success': False,
                    'message': 'لا يوجد مخزون كافي'
                })

            cart_item.quantity += 1
            cart_item.save()

        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()

        elif action == 'remove':
            cart_item.delete()

        # Recalculate totals
        remaining_items = CartItem.objects.filter(user=request.user)
        total_price = sum(item.total_price for item in remaining_items)
        cart_count = remaining_items.aggregate(total=Sum('quantity'))['total'] or 0

        return JsonResponse({
            'success': True,
            'total_price': float(total_price),
            'cart_count': cart_count,
            'item_total': float(cart_item.total_price) if action != 'remove' else 0
        })

    return JsonResponse({'success': False})

def get_cart_count(request):
    if request.user.is_authenticated:
        product_count = CartItem.objects.filter(user=request.user).aggregate(
            total=Sum('quantity'))['total'] or 0
        service_count = ServiceCartItem.objects.filter(user=request.user).aggregate(
            total=Sum('quantity'))['total'] or 0
        total_count = product_count + service_count
        return JsonResponse({'cart_count': total_count})
    return JsonResponse({'cart_count': 0})


@login_required
def checkout(request):
    product_items = CartItem.objects.filter(user=request.user)
    service_items = ServiceCartItem.objects.filter(user=request.user)

    if not product_items.exists() and not service_items.exists():
        messages.warning(request, 'سلة التسوق فارغة')
        return redirect('cart')

    out_of_stock_items = []
    for item in product_items:
        if item.quantity > item.product.stock:
            out_of_stock_items.append(item.product.title)

    if out_of_stock_items:
        messages.error(request, f'المنتجات التالية غير متوفرة بالكمية المطلوبة: {", ".join(out_of_stock_items)}')
        return redirect('cart')

    product_total = sum(item.total_price for item in product_items)
    service_total = sum(item.total_price for item in service_items)
    total_price = product_total + service_total

    context = {
        'product_items': product_items,
        'service_items': service_items,
        'product_total': product_total,
        'service_total': service_total,
        'total_price': total_price
    }

    return render(request, 'student/cart/checkout.html', context)

# Process Order
@login_required
def place_order(request):
    if request.method == 'POST':
        product_items = CartItem.objects.filter(user=request.user)
        service_items = ServiceCartItem.objects.filter(user=request.user)

        if not product_items.exists() and not service_items.exists():
            messages.warning(request, 'سلة التسوق فارغة')
            return redirect('cart')

        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        region = request.POST.get('region')
        postal_code = request.POST.get('postal_code')
        notes = request.POST.get('notes', '')
        payment_method = request.POST.get('payment_method', 'credit_card')

        for item in product_items:
            if item.quantity > item.product.stock:
                messages.error(request, f'المنتج {item.product.title} غير متوفر بالكمية المطلوبة')
                return redirect('cart')

        product_total = sum(item.total_price for item in product_items)
        service_total = sum(item.total_price for item in service_items)
        total_price = product_total + service_total

        total_with_tax = total_price * Decimal(str(1.15))

        club = None
        if product_items.exists():
            club = product_items.first().product.club
        elif service_items.exists():
            club = service_items.first().service.club

        order = Order.objects.create(
            user=request.user,
            club=club,
            total_price=total_with_tax,
            status='pending' if payment_method == 'cash_on_delivery' else 'confirmed',
            payment_method=payment_method,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            region=region,
            postal_code=postal_code,
            notes=notes
        )

        for item in product_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

            if payment_method == 'credit_card':
                product = item.product
                product.stock -= item.quantity
                product.save()

        for item in service_items:
            OrderItem.objects.create(
                order=order,
                service=item.service,
                quantity=item.quantity,
                price=item.service.price
            )

            if payment_method == 'credit_card':
                ServiceOrderModel.objects.create(
                    service=item.service,
                    student=request.user,
                    price=item.service.price * item.quantity,
                    is_complited=False,
                    end_datetime=timezone.now() + timezone.timedelta(days=item.service.subscription_days),
                    creation_date=timezone.now()
                )

        if payment_method == 'cash_on_delivery' and club:
            customer_name = f"{first_name} {last_name}"
            notification_message = f"طلب جديد رقم #{order.id} بقيمة {total_with_tax} ر.س من العميل {customer_name} - طريقة الدفع: الدفع عند الاستلام"

            Notification.objects.create(
                club=club,
                message=notification_message,
                is_read=False,
                created_at=timezone.now()
            )

        product_items.delete()
        service_items.delete()

        if payment_method == 'cash_on_delivery':
            messages.success(request, 'تم إرسال طلبك بنجاح وهو الآن قيد المراجعة. سيتم تأكيده من قبل المدير قريباً.')
        else:
            messages.success(request, 'تم إتمام عملية الشراء بنجاح')

        return redirect('order_details', order_id=order.id)

    return redirect('checkout')


@login_required
def add_service_to_cart(request):
    if request.method == 'POST':
        service_id = request.POST.get('service_id')
        quantity = int(request.POST.get('quantity', 1))

        service = get_object_or_404(ServicesModel, id=service_id)

        booked_services = BookingService.objects.filter(
            booking__student=request.user.userprofile.student_profile,
            service=service
        )

        if not booked_services.exists():
            return JsonResponse({
                'success': False,
                'message': 'لا يمكنك إضافة هذه الخدمة إلى السلة لأنها لم تُحجز.'
            })

        cart_item, created = ServiceCartItem.objects.get_or_create(
            user=request.user,
            service=service,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        product_count = CartItem.objects.filter(user=request.user).aggregate(
            total=Sum('quantity'))['total'] or 0
        service_count = ServiceCartItem.objects.filter(user=request.user).aggregate(
            total=Sum('quantity'))['total'] or 0
        cart_count = product_count + service_count

        return JsonResponse({
            'success': True,
            'message': 'تمت إضافة الخدمة إلى السلة',
            'cart_count': cart_count,
            'booked_services':booked_services,
        })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def update_service_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')

        cart_item = get_object_or_404(ServiceCartItem, id=item_id, user=request.user)

        if action == 'increase':
            cart_item.quantity += 1
            cart_item.save()

        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()

        elif action == 'remove':
            cart_item.delete()

        remaining_service_items = ServiceCartItem.objects.filter(user=request.user)
        remaining_product_items = CartItem.objects.filter(user=request.user)

        service_total = sum(item.total_price for item in remaining_service_items)
        product_total = sum(item.total_price for item in remaining_product_items)
        total_price = service_total + product_total

        service_count = remaining_service_items.aggregate(total=Sum('quantity'))['total'] or 0
        product_count = remaining_product_items.aggregate(total=Sum('quantity'))['total'] or 0
        cart_count = service_count + product_count

        return JsonResponse({
            'success': True,
            'total_price': float(total_price),
            'cart_count': cart_count,
            'item_total': float(cart_item.total_price) if action != 'remove' else 0
        })

    return JsonResponse({'success': False})

@login_required
def view_student_profile(request):
    try:
        user_profile = request.user.userprofile
        student = user_profile.student_profile

        if not student:
            return render(request, 'error_page.html', {'message': 'No student profile found for this user.'})

        context = {
            'student': student,
            'userprofile': user_profile,
        }

        return render(request, 'accounts/profiles/Student/ViewStudentProfile.html', context)

    except UserProfile.DoesNotExist:
        return render(request, 'error_page.html', {'message': 'User profile not found.'})

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['full_name', 'phone', 'birthday', 'about']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'phone': forms.TextInput(attrs={'class': 'mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'birthday': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'about': forms.Textarea(attrs={'rows': 4, 'class': 'mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'})
        }

@login_required
def edit_student_profile(request):
    try:
        user_profile = request.user.userprofile
        student = user_profile.student_profile

        if not student:
            return render(request, 'error_page.html', {'message': 'No student profile found for this user.'})

        if request.method == 'POST':
            form = StudentProfileForm(request.POST, instance=student)

            if form.is_valid():
                form.save()

                if 'profile_image_base64' in request.FILES:
                    image_file = request.FILES['profile_image_base64']
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    user_profile.profile_image_base64 = f"data:image/{image_file.content_type.split('/')[-1]};base64,{encoded_string}"
                    user_profile.save()

                return redirect('student_profile')
        else:
            form = StudentProfileForm(instance=student)

        context = {
            'form': form,
            'student': student,
        }

        return render(request, 'accounts/settings/Student/EditStudentProfile.html', context)

    except UserProfile.DoesNotExist:
        return render(request, 'error_page.html', {'message': 'User profile not found.'})


@login_required
def order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)

    context = {
        'order': order,
        'order_items': order_items,
    }

    return render(request, 'student/orders/order_details.html', context)

@login_required
def student_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'orders': orders
    }

    return render(request, 'student/orders/student_orders.html', context)