from django.shortcuts import render, redirect,get_object_or_404
from .forms import CoachAppointmentsForm, StudentAppointmentPresenceForm
from .models import CoachAppointmentsModel, StudentAppointmentPresenceModel
import datetime, json
from students.models import ServiceOrderModel, ServicesModel
from django.contrib.auth.models import User
from django.http import JsonResponse
from accounts.models import UserProfile
from django.utils import timezone
import datetime  # ✅ Import datetime module
from club_dashboard.models import Notification
from .utils import send_notification
from django.contrib.auth.decorators import login_required  # ✅ Fix missing import
from django.contrib import messages
from club_dashboard.models import SalonAppointment
from datetime import datetime
from receptionist_dashboard.models import BookingService
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
    coach = user.userprofile.Coach_profile

    CoachAppointments = CoachAppointmentsModel.objects.filter(coach=coach)
    StudentAppointmentPresences = StudentAppointmentPresenceModel.objects.filter(appointment__coach=coach)

    club = coach.club if coach and coach.club else None

    return render(request, 'coach_dashboard/index.html', {
        'CoachAppointments': CoachAppointments,
        'StudentAppointmentPresences': StudentAppointmentPresences,
        'club': club,
        'coachName': coach.full_name
    })


def viewCoachAppointments(request):
    user = request.user

    if not hasattr(user.userprofile, 'Coach_profile') or not user.userprofile.Coach_profile:
        messages.error(request, "ليس لديك صلاحية للوصول إلى هذه الصفحة.")
        return redirect('coachIndex')

    coach = user.userprofile.Coach_profile
    coach_appointments = CoachAppointmentsModel.objects.filter(coach=coach)

    return render(request, 'coach_dashboard/CoachAppointments/viewCoachAppointments.html', {
        'CoachAppointments': coach_appointments
    })


def addCoachAppointments(request):
    user = request.user

    if not hasattr(user.userprofile, 'Coach_profile') or not user.userprofile.Coach_profile:
        messages.error(request, "ليس لديك صلاحية للوصول إلى هذه الصفحة.")
        return redirect('coachIndex')

    coach = user.userprofile.Coach_profile
    club = coach.club

    club_services = ServicesModel.objects.filter(club=club)
    form = CoachAppointmentsForm(coach=coach)

    if request.method == 'POST':
        form = CoachAppointmentsForm(request.POST, coach=coach)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.coach = coach
            appointment.end_datetime = appointment.start_datetime + datetime.timedelta(days=1)
            appointment.save()

            send_notification(user, club, f"📅 تمت إضافة موعد جديد بواسطة المدرب {coach.full_name} في {appointment.start_datetime.strftime('%Y-%m-%d %H:%M')}.")
            messages.success(request, "تمت إضافة الموعد بنجاح.")
            return redirect('viewCoachAppointments')

    return render(request, 'coach_dashboard/CoachAppointments/addCoachAppointments.html', {
        'form': form,
        'club_services': club_services
    })


def editCoachAppointments(request, id):
    user = request.user

    if not hasattr(user.userprofile, 'Coach_profile') or not user.userprofile.Coach_profile:
        messages.error(request, "ليس لديك صلاحية للوصول إلى هذه الصفحة.")
        return redirect('coachIndex')

    coach = user.userprofile.Coach_profile
    club = coach.club

    coach_appointment = get_object_or_404(CoachAppointmentsModel, id=id, coach=coach)

    form = CoachAppointmentsForm(instance=coach_appointment, coach=coach)

    if request.method == 'POST':
        form = CoachAppointmentsForm(request.POST, instance=coach_appointment, coach=coach)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.end_datetime = appointment.start_datetime + datetime.timedelta(days=1)
            appointment.save()

            send_notification(user, club, f"📝 تم تعديل موعد بواسطة المدرب {coach.full_name}. الموعد الجديد: {appointment.start_datetime.strftime('%Y-%m-%d %H:%M')}.")
            messages.success(request, "تم تعديل الموعد بنجاح.")
            return redirect('viewCoachAppointments')

    return render(request, 'coach_dashboard/CoachAppointments/editCoachAppointments.html', {'form': form})


def deleteCoachAppointments(request, id):
    user = request.user

    if not hasattr(user.userprofile, 'Coach_profile') or not user.userprofile.Coach_profile:
        messages.error(request, "ليس لديك صلاحية للوصول إلى هذه الصفحة.")
        return redirect('coachIndex')

    coach = user.userprofile.Coach_profile
    club = coach.club

    coach_appointment = get_object_or_404(CoachAppointmentsModel, id=id, coach=coach)
    appointment_time = coach_appointment.start_datetime.strftime('%Y-%m-%d %H:%M')

    coach_appointment.delete()

    send_notification(user, club, f"🗑️ تم حذف الموعد بتاريخ {appointment_time} بواسطة المدرب {coach.full_name}.")
    messages.success(request, "تم حذف الموعد بنجاح.")
    return redirect('viewCoachAppointments')




#StudentAppointmentPresences
# def viewStudentAppointmentPresences(request):
#     coach = request.user
#     coach_profile = coach.userprofile.Coach_profile
#     club = coach_profile.club
#     services = ServicesModel.objects.filter(club=club)
#     StudentAppointmentPresences = StudentAppointmentPresenceModel.objects.filter(appointment__coach=coach_profile)
#
#     coach = request.user.userprofile.Coach_profile
#     form = StudentAppointmentPresenceForm(coach=coach)
#
#     return render(request, 'coach_dashboard/StudentAppointmentPresences/viewStudentAppointmentPresences.html', {'StudentAppointmentPresences':StudentAppointmentPresences, 'services':services, 'form':form})
#
# def addStudentAppointmentPresence(request):
#     coach = request.user.userprofile.Coach_profile
#     form = StudentAppointmentPresenceForm(coach=coach)
#
#     if request.method == 'POST':
#         form = StudentAppointmentPresenceForm(request.POST, coach=coach)
#         student_id = request.POST.get('student_id')
#         student_profile = UserProfile.objects.get(user__id=student_id).student_profile
#         if form.is_valid():
#             presence = form.save(commit=False)
#             presence.student = student_profile
#             presence.creation_date = timezone.now()
#             presence.save()
#             return redirect('viewStudentAppointmentPresences')
#     return render(request, 'coach_dashboard/StudentAppointmentPresences/addStudentAppointmentPresence.html', {'form':form})
#
#
# def editStudentAppointmentPresence(request, id):
#     coach = request.user.userprofile.Coach_profile
#     CoachAppointment = StudentAppointmentPresenceModel.objects.get(id=id)
#     form = StudentAppointmentPresenceForm(instance=CoachAppointment, coach=coach)
#     if request.method == 'POST':
#         form = StudentAppointmentPresenceForm(request.POST, instance=CoachAppointment, coach=coach)
#         if form.is_valid():
#             form.save()
#     return render(request, 'coach_dashboard/StudentAppointmentPresences/editStudentAppointmentPresence.html', {'form':form})
#
# def deleteStudentAppointmentPresence(request, id):
#     StudentAppointmentPresence = StudentAppointmentPresenceModel.objects.get(id=id)
#     StudentAppointmentPresence.delete()
#     return redirect('viewStudentAppointmentPresences')



def getServiceStudents(request, service_id):
    coach = request.user
    coach_profile = coach.userprofile.Coach_profile
    club = coach_profile.club
    students = User.objects.filter(userprofile__account_type='3', userprofile__student_profile__club=club)
    students_list = []
    service = ServicesModel.objects.get(id=service_id)
    for student in students:
        services_order = ServiceOrderModel.objects.filter(service=service, student=student)
        if services_order.exists():
            students_list.append({'full_name':student.userprofile.student_profile.full_name, 'user_id':student.id})
    
    return JsonResponse(students_list, safe=False)


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
        return render(request, 'coach_dashboard/salon_appointments.html', {
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
                                    'start': appointment.start_time.strftime('%H:%M'),
                                    'end': appointment.end_time.strftime('%H:%M')
                                }
                            except:
                                slot_info['booking'] = None

                        break

            schedule[day].append(slot_info)

    return render(request, 'coach_dashboard/salon_appointments.html', {
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
        return redirect('coach_dashboard/appointment_details.html')

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
        return redirect('coach_salon_appointments')

    return render(request, 'coach_dashboard/appointment_details.html', context)