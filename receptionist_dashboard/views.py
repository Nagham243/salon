from django.shortcuts import render, redirect, get_object_or_404
from club_dashboard.models import SalonAppointment
from django.contrib.auth.decorators import login_required
from .forms import SalonBookingForm ,ServiceSelectionForm
from .models import SalonBooking ,BookingService
from django.contrib import messages
from django.http import JsonResponse
from accounts.models import UserProfile ,StudentProfile
from django.contrib.auth.models import User
from club_dashboard.utils import send_notification
from accounts.forms import StudentProfileForm
from datetime import datetime, timedelta
from django.db import models , transaction
from students.models import ServicesModel
from django.forms import formset_factory

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
def index(request):
    club = get_user_club(request.user)
    if not club:
        messages.error(request, "No club assigned to your profile. Please contact an administrator.")
        return redirect('signin')

    students = UserProfile.objects.filter(
        account_type='3',
        student_profile__club=club
    ).select_related('user', 'student_profile')

    valid_students = [student for student in students if student.student_profile]

    user = request.user
    receptionist = user.userprofile.receptionist_profile
    if request.user.userprofile.account_type != '5':
        return redirect('signin')

    receptionist_profile = request.user.userprofile.receptionist_profile

    context = {
        'receptionist': receptionist_profile,
        'club': receptionist_profile.club if receptionist_profile else None,
        'students': valid_students
    }

    return render(request, 'receptionist_dashboard/index.html', context)

@login_required
def salon_appointments(request):
    days = ['السبت', 'الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة']

    time_slots = []
    for hour in range(1, 13):
        for minute in [0, 30]:
            current_time = datetime.strptime(f'{hour:02d}:{minute:02d}:00 AM', '%I:%M:%S %p').time()
            time_slots.append(current_time)
    for hour in range(1, 13):
        for minute in [0, 30]:
            current_time = datetime.strptime(f'{hour:02d}:{minute:02d}:00 PM', '%I:%M:%S %p').time()
            time_slots.append(current_time)

    schedule = {}

    club = get_user_club(request.user)
    if not club:
        messages.error(request, "No club assigned to your profile. Please contact an administrator.")
        return render(request, 'receptionist_dashboard/salon_appointments.html', {
            'schedule': {},
            'days': days,
            'time_slots': [slot.strftime('%I:%M %p') for slot in time_slots]
        })

    for day in days:
        schedule[day] = []
        appointments = SalonAppointment.objects.filter(
            day=day,
            club=club
        ).order_by('start_time')

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

    return render(request, 'receptionist_dashboard/salon_appointments.html', {
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
        return redirect('book_appointment_details', day=selected_day)

    return render(request, 'receptionist_dashboard/select_appointment_day.html', {
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

    for appointment in day_appointments:
        try:
            booking = appointment.booking
            services = BookingService.objects.filter(booking=booking)
            service_names = ", ".join([s.service.title for s in services])

            start_datetime = datetime.combine(datetime.today(), appointment.start_time)
            end_datetime = datetime.combine(datetime.today(), appointment.end_time)
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

        if booking_form.is_valid() and service_formset.is_valid():
            total_duration = 0
            for form in service_formset:
                if form.cleaned_data and form.cleaned_data.get('service'):
                    total_duration += form.cleaned_data['service'].duration

            booking_data = booking_form.cleaned_data.copy()

            student = booking_data.get('student')
            employee = booking_data.get('employee')

            booking_data['student_id'] = student.id if student else None
            booking_data['employee_id'] = employee.id if employee else None
            booking_data['employee_name'] = booking_data.get('employee_name')

            booking_data.pop('student', None)
            booking_data.pop('employee', None)

            request.session['booking_form_data'] = booking_data

            services_data = []
            for form in service_formset:
                if form.cleaned_data and form.cleaned_data.get('service'):
                    services_data.append(form.cleaned_data['service'].id)

            request.session['service_ids'] = services_data
            request.session['total_duration'] = total_duration

            return redirect('select_appointment_time', day=day)
        else:
            messages.error(request, "هناك خطأ في البيانات المدخلة. الرجاء التحقق والمحاولة مرة أخرى.")
    else:
        booking_form = SalonBookingForm()
        service_formset = ServiceFormSet(prefix='services')

    return render(request, 'receptionist_dashboard/book_appointment_details.html', {
        'booking_form': booking_form,
        'service_formset': service_formset,
        'day': day,
        'appointments': appointments
    })

@login_required
def select_appointment_time(request, day):
    club = get_user_club(request.user)
    if not club:
        messages.error(request, "No club assigned to your profile. Please contact an administrator.")
        return redirect('index')

    time_slots = []
    for hour in range(1, 13):
        for minute in [0, 30]:
            time = datetime.strptime(f'{hour:02d}:{minute:02d}:00 AM', '%I:%M:%S %p').time()
            time_slots.append(time)
    for hour in range(1, 13):
        for minute in [0, 30]:
            time = datetime.strptime(f'{hour:02d}:{minute:02d}:00 PM', '%I:%M:%S %p').time()
            time_slots.append(time)

    total_duration = request.session.get('total_duration', 0)

    available_slots = []
    for time in time_slots:
        is_available = True

        start_datetime = datetime.combine(datetime.today(), time)
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

    return render(request, 'receptionist_dashboard/select_appointment_time.html', {
        'day': day,
        'time_slots': available_slots,
        'total_duration': total_duration
    })

@login_required
def verify_and_book_appointment(request, day):
    club = get_user_club(request.user)

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم.")
        return redirect('select_club')

    if request.method != 'POST':
        return redirect('select_appointment_time', day=day)

    time_input = request.POST.get('time_input')
    period = request.POST.get('period')

    if not time_input or not period:
        messages.error(request, "يرجى إدخال الوقت والفترة")
        return redirect('select_appointment_time', day=day)

    try:
        if ':' in time_input:
            hours, minutes = time_input.split(':')
            hours = int(hours)
            minutes = int(minutes)

            if hours < 1 or hours > 12:
                messages.error(request, "صيغة الوقت غير صحيحة. يجب أن تكون الساعة من 1 إلى 12")
                return redirect('select_appointment_time', day=day)

            if period == 'PM' and hours < 12:
                hours += 12
            elif period == 'AM' and hours == 12:
                hours = 0

            time_obj = datetime.strptime(f'{hours:02d}:{minutes:02d}:00', '%H:%M:%S').time()
    except ValueError:
        messages.error(request, "صيغة الوقت غير صحيحة. الرجاء استخدام الصيغة HH:MM")
        return redirect('select_appointment_time', day=day)


    booking_form_data = request.session.get('booking_form_data', {})
    service_ids = request.session.get('service_ids', [])
    total_duration = request.session.get('total_duration', 0)

    if not booking_form_data or not service_ids:
        messages.error(request, "بيانات الحجز غير مكتملة. الرجى المحاولة مرة أخرى.")
        return redirect('select_appointment_day')

    start_datetime = datetime.combine(datetime.today(), time_obj)
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
        messages.error(request, "هذا الوقت غير متاح. يرجى اختيار وقت آخر.")
        return redirect('select_appointment_time', day=day)

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

            if not student_id:
                messages.error(request, "بيانات العميل غير متوفرة. الرجاء المحاولة مرة أخرى.")
                return redirect('select_appointment_day')

            try:
                student = StudentProfile.objects.get(id=student_id)
            except StudentProfile.DoesNotExist:
                messages.error(request, "لم يتم العثور على العميل. الرجاء المحاولة مرة أخرى.")
                return redirect('select_appointment_day')

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
                created_at=datetime.now()
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

            return redirect('receptionist_salon_appointments')

    except Exception as e:
        messages.error(request, f"حدث خطأ أثناء الحجز: {str(e)}")
        return redirect('select_appointment_time', day=day)


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
        return redirect('select_appointment_day')

    booking_form_data = request.session.get('booking_form_data', {})
    service_ids = request.session.get('service_ids', [])
    total_duration = request.session.get('total_duration', 0)

    if not booking_form_data or not service_ids:
        messages.error(request, "بيانات الحجز غير مكتملة. الرجاء المحاولة مرة أخرى.")
        return redirect('select_appointment_day')

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

    start_datetime = datetime.combine(datetime.today(), time_obj)
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
        messages.error(request, "هناك تعارض في المواعيد. الرجاء اختيار وقت آخر")
        return redirect('select_appointment_time', day=day)

    try:
        with transaction.atomic():
            appointment = SalonAppointment.objects.create(
                day=day,
                start_time=time_obj,
                end_time=end_time,
                available=False,
                club=club
            )

            student_id = booking_form_data.get('student_id')  # FIXED: Use student_id instead of student
            employee_id = booking_form_data.get('employee_id')  # FIXED: Use employee_id instead of employee

            if not student_id:
                messages.error(request, "بيانات العميل غير متوفرة. الرجاء المحاولة مرة أخرى.")
                return redirect('select_appointment_day')

            try:
                student = StudentProfile.objects.get(id=student_id)
            except StudentProfile.DoesNotExist:
                messages.error(request, "لم يتم العثور على العميل. الرجاء المحاولة مرة أخرى.")
                return redirect('select_appointment_day')

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
                created_at=datetime.now()
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

            return redirect('receptionist_salon_appointments')
    except Exception as e:
        messages.error(request, f"حدث خطأ أثناء الحجز: {str(e)}")
        return redirect('select_appointment_day')

@login_required
def appointment_details(request, appointment_id):
    club = get_user_club(request.user)

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم.")
        return redirect('index')

    appointment = get_object_or_404(SalonAppointment, id=appointment_id)
    if appointment.club != club:
        messages.error(request, "ليس لديك صلاحية لعرض هذا الموعد.")
        return redirect('receptionist_salon_appointments')

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
            'booking_services': booking_services,  # Change the variable name to be more explicit
            'total_price': sum(bs.service.price for bs in booking_services),
            'total_duration': sum(bs.service.duration for bs in booking_services)
        }
    except Exception as e:
        messages.error(request, f"لم يتم العثور على معلومات الحجز: {str(e)}")
        return redirect('receptionist_salon_appointments')

    return render(request, 'receptionist_dashboard/appointment_details.html', context)

@login_required
def cancel_appointment(request, appointment_id):
    club = get_user_club(request.user)

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم.")
        return redirect('index')

    appointment = get_object_or_404(SalonAppointment, id=appointment_id)
    if appointment.club != club:
        messages.error(request, "ليس لديك صلاحية لإلغاء هذا الموعد.")
        return redirect('receptionist_salon_appointments')

    try:
        booking = appointment.booking
        BookingService.objects.filter(booking=booking).delete()
        booking.delete()
        appointment.delete()

        messages.success(request, "تم إلغاء الحجز بنجاح")
    except:
        messages.error(request, "لم يتم العثور على حجز لهذا الموعد")

    return redirect('receptionist_salon_appointments')


def viewStudentss(request):
    """Displays all students in the club."""
    club = get_user_club(request.user)

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم.")
        return redirect('index')

    students = UserProfile.objects.filter(
        account_type='3',
        student_profile__club=club
    ).select_related('user', 'student_profile')

    valid_students = [student for student in students if student.student_profile]

    return render(request, 'receptionist_dashboard/students/viewStudents.html', {'students': valid_students})


def addStudent(request):
    """Adds a new student to the club."""
    club = get_user_club(request.user)

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم.")
        return redirect('index')

    form = StudentProfileForm()

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('addStudentFromReceptionist')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already in use.")
            return redirect('addStudentFromReceptionist')

        form = StudentProfileForm(request.POST)
        if form.is_valid():
            student = User.objects.create(username=username, email=email)
            if password:
                student.set_password(password)
            student.save()

            student_profile = form.save(commit=False)
            student_profile.user = student
            student_profile.club = club
            student_profile.save()

            UserProfile.objects.create(user=student, account_type='3', student_profile=student_profile)

            # send_notification(f"📢 New student {username} has been added to club {club}.")

            messages.success(request, "client added successfully.")
            return redirect('viewStudentss')
        else:
            print(f"Form errors: {form.errors}")
            messages.error(request, f"Form validation failed: {form.errors}")

    return render(request, 'receptionist_dashboard/students/addStudent.html', {'form': form})


@login_required
def editStudentt(request, id):
    """Edits an existing student's details."""
    club = get_user_club(request.user)

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم.")
        return redirect('index')

    student_profile = get_object_or_404(StudentProfile, id=id)
    if student_profile.club != club:
        messages.error(request, "ليس لديك صلاحية لتعديل هذا الطالب.")
        return redirect('viewStudentss')

    student = get_object_or_404(User, userprofile__student_profile=student_profile)

    form = StudentProfileForm(instance=student_profile)

    if request.method == 'POST':
        new_username = request.POST.get('username')
        new_email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=new_username).exclude(id=student.id).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'receptionist_dashboard/students/editStudent.html', {
                'form': form,
                'student': student
            })

        if User.objects.filter(email=new_email).exclude(id=student.id).exists():
            messages.error(request, "Email is already in use.")
            return render(request, 'receptionist_dashboard/students/editStudent.html', {
                'form': form,
                'student': student
            })

        form = StudentProfileForm(request.POST, instance=student_profile)
        if form.is_valid():
            student.username = new_username
            student.email = new_email
            if password:
                student.set_password(password)
            student.save()

            student_profile = form.save(commit=False)
            student_profile.user = student
            student_profile.club = club
            student_profile.save()

            messages.success(request, "Student profile updated successfully.")
            return redirect('viewStudentss')
        else:
            print(f"Form errors: {form.errors}")
            messages.error(request, f"Form validation failed: {form.errors}")

    return render(request, 'receptionist_dashboard/students/editStudent.html', {
        'form': form,
        'student': student
    })



@login_required
def deleteStudentt(request, id):
    """Deletes a student from the club."""
    club = get_user_club(request.user)

    if not club:
        messages.error(request, "لم يتم تحديد نادٍ لهذا المستخدم.")
        return redirect('index')

    student_profile = get_object_or_404(StudentProfile, id=id)
    if student_profile.club != club:
        messages.error(request, "ليس لديك صلاحية لحذف هذا الطالب.")
        return redirect('viewStudentss')

    student = get_object_or_404(User, userprofile__student_profile=student_profile)

    student_name = student.username

    student_profile.delete()
    student.delete()

    # ✅ Send notification
    # send_notification( f"🗑️ Student {student_name} has been removed.")

    messages.success(request, "Client has been deleted successfully.")
    return redirect('viewStudentss')

# Helper function to generate available slots
def get_available_time_slots(request,day, duration_minutes):
    """Get available time slots for a given day and duration"""
    club = get_user_club(request.user)

    if not club:
        return []

    time_slots = []
    for hour in range(24):
        for minute in [0, 30]:
            time = datetime.strptime(f'{hour:02d}:{minute:02d}:00', '%H:%M:%S').time()
            time_slots.append(time)

    available_slots = []
    for time in time_slots:
        # Calculate end time based on duration
        start_datetime = datetime.combine(datetime.today(), time)
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        end_time = end_datetime.time()

        # Check for conflicts
        conflicts = SalonAppointment.objects.filter(
            day=day,
            available=False,
            club=club,
        ).filter(
            models.Q(start_time__lt=end_time, end_time__gt=time)
        )

        if not conflicts.exists():
            available_slots.append({
                'time': time.strftime('%H:%M'),
                'available': True
            })

    return available_slots