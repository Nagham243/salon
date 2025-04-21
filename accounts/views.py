import random
from django.utils.timezone import now
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages  # Import Django messages framework
from .forms import StudentProfileForm, DirectorSignupForm , ReceptionistSignupForm
from .models import UserProfile, DirectorProfile, ClubsModel,ReceptionistProfile
from .models import UserProfile, StudentProfile, OTP


def generate_otp():
    return str(random.randint(100000, 999999))

def signin(request):
    """Step 1: Verify email & password, then send OTP"""
    if request.method == 'POST':
        email = request.POST.get('email').strip().lower()
        password = request.POST.get('password')
        user = User.objects.filter(email=email).first()

        if user:
            user = authenticate(username=user.username, password=password)
            if user:
                # Generate and save OTP
                otp_code = generate_otp()
                OTP.objects.update_or_create(user=user, defaults={"otp_code": otp_code, "created_at": now()})

                # Send OTP via email
                try:
                    send_mail(
                        "Your OTP Code",
                        f"Your OTP code is {otp_code}. It expires in 5 minutes.",
                        "noreply@yourdomain.com",  # Replace with your actual sender email
                        [user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    return render(request, 'accounts/sign/signin.html', {"error": f"Error sending email: {str(e)}"})

                request.session['otp_user_id'] = user.id  # Store user ID for OTP verification
                return redirect('verify_otp')  # Redirect to OTP verification page

        return render(request, 'accounts/sign/signin.html', {"error": "Invalid email or password."})

    return render(request, 'accounts/sign/signin.html')


def verify_otp(request):
    """Step 2: Verify the OTP and complete the login process"""
    if request.method == "POST":
        otp_code = request.POST.get("otp", "").strip()
        user_id = request.session.get('otp_user_id')

        if not user_id:
            return redirect('signin')

        user = User.objects.filter(id=user_id).first()
        try:
            account_type = user.userprofile.account_type
        except UserProfile.DoesNotExist:
            # Create a default UserProfile if it doesn't exist
            UserProfile.objects.create(user=user, account_type='3')  # Default to student
            account_type = '3'

        otp_record = OTP.objects.filter(user=user, otp_code=otp_code).first()

        if otp_record:
            # Check if the OTP is expired (5 minutes validity)
            if (now() - otp_record.created_at).seconds > 300:
                otp_record.delete()
                return render(request, 'accounts/sign/otp_verify.html', {
                    "error": "OTP has expired. Please request a new one."
                })

            # OTP is valid; complete the login
            login(request, user)
            otp_record.delete()  # Delete OTP after successful login
            request.session.pop('otp_user_id', None)  # SAFE deletion

            # Redirect based on user profile account type
            account_type = user.userprofile.account_type
            if account_type == '1':
                return redirect('adminIndex')
            elif account_type == '2':
                return redirect('club_dashboard_index')
            elif account_type == '3':
                return redirect('studentIndex')
            elif account_type == '4':
                return redirect('coachIndex')
            elif account_type == '5':
                return redirect('receptionistIndex')
            else:
                return redirect('landingIndex')

        return render(request, 'accounts/sign/otp_verify.html', {"error": "Invalid OTP. Please try again."})

    return render(request, 'accounts/sign/otp_verify.html')


def signup(request):
    account_type = request.POST.get('account_type', '3')  # Default to Student

    student_form = StudentProfileForm()
    director_form = DirectorSignupForm()
    receptionist_form = ReceptionistSignupForm()

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        print(f"DEBUG: Account type: {account_type}, Username: {username}, Email: {email}")

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "اسم المستخدم مأخوذ بالفعل.")
            return redirect('signup')

        elif User.objects.filter(email=email).exists():
            messages.error(request, "البريد الإلكتروني مسجل مسبقًا.")
            return redirect('signup')

        else:
            if account_type == '3':  # Student Sign-Up
                student_form = StudentProfileForm(request.POST)
                if student_form.is_valid():
                    user = User.objects.create_user(username=username, email=email, password=password)
                    student_profile = student_form.save()
                    UserProfile.objects.create(user=user, account_type='3', student_profile=student_profile)

                    messages.success(request, "تم إنشاء حساب العميل بنجاح! يمكنك الآن تسجيل الدخول.")
                    return redirect('signin')
                else:
                    messages.error(request, "حدث خطأ في بيانات التسجيل، يرجى التحقق منها.")

            elif account_type == '2':  # Director Sign-Up
                director_form = DirectorSignupForm(request.POST, request.FILES)
                if director_form.is_valid():
                    try:
                        # **Step 1: Create the User first**
                        user = User.objects.create_user(username=username, email=email, password=password)

                        # **Step 2: Validate City Selection**
                        city = director_form.cleaned_data['city']
                        from .fields import citys
                        valid_city_values = [c[0] for c in citys]
                        if city not in valid_city_values:
                            messages.error(request, "اختيار المدينة غير صالح.")
                            return redirect('signup')

                        # **Step 3: Check for Existing Club**
                        club_name = director_form.cleaned_data['club_name']
                        existing_club = ClubsModel.objects.filter(name=club_name).first()
                        if existing_club:
                            messages.error(request, "اسم الصالون مستخدم بالفعل.")
                            return redirect('signup')

                        # **Step 4: Create the Club instance**
                        club = ClubsModel.objects.create(
                            name=club_name,
                            city=city,
                            street=director_form.cleaned_data['street'],
                            district=director_form.cleaned_data.get('district'),
                            about=director_form.cleaned_data.get('about'),
                            desc=director_form.cleaned_data.get('desc'),
                            club_profile_image_base64=director_form.cleaned_data.get('club_profile_image_base64', None)
                        )

                        # **Step 5: Create Director Profile linked to the Club**
                        director_profile = DirectorProfile.objects.create(
                            full_name=director_form.cleaned_data['username'],
                            phone=director_form.cleaned_data['phone'],
                            club=club,
                            about=director_form.cleaned_data.get('about')
                        )

                        # **Step 6: Create UserProfile linked to the DirectorProfile**
                        UserProfile.objects.create(user=user, account_type='2', director_profile=director_profile)

                        messages.success(request, f"تم إنشاء الصالون {club_name} بنجاح! يمكنك الآن تسجيل الدخول.")
                        return redirect('signin')

                    except Exception as e:
                        messages.error(request, f"حدث خطأ غير متوقع: {e}")
                        return redirect('signup')

                else:
                    messages.error(request, "حدث خطأ في التسجيل، يرجى مراجعة البيانات.")

            elif account_type == '5':  # Receptionist Sign-Up
                receptionist_form = ReceptionistSignupForm(request.POST)
                if receptionist_form.is_valid():
                    try:
                        # Create User
                        user = User.objects.create_user(
                            username=receptionist_form.cleaned_data['username'],
                            email=receptionist_form.cleaned_data['email'],
                            password=receptionist_form.cleaned_data['password']
                        )

                        # Create Receptionist Profile
                        receptionist_profile = ReceptionistProfile.objects.create(
                            full_name=receptionist_form.cleaned_data['full_name'],
                            phone=receptionist_form.cleaned_data['phone'],
                            email=receptionist_form.cleaned_data['email'],
                            club=receptionist_form.cleaned_data['club'],
                            about=receptionist_form.cleaned_data.get('about')
                        )

                        # Create UserProfile
                        UserProfile.objects.create(
                            user=user,
                            account_type='5',
                            receptionist_profile=receptionist_profile
                        )

                        messages.success(request, "تم إنشاء حساب الموظف بنجاح! يمكنك الآن تسجيل الدخول.")
                        return redirect('signin')

                    except Exception as e:
                        messages.error(request, f"حدث خطأ غير متوقع: {e}")
                        return redirect('signup')


    return render(request, 'accounts/sign/signup.html', {
        'student_form': student_form,
        'director_form': director_form,
        'receptionist_form': receptionist_form,
        'account_type': account_type
    })


def signout(request):
    logout(request)
    messages.success(request, "تم تسجيل الخروج بنجاح.")
    return redirect('landingIndex')
