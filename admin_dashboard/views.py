from django.shortcuts import render, redirect
from accounts.models import ClubsModel, DirectorProfile, UserProfile
from django.contrib.auth.models import User
from accounts.fields import citys
from .forms import ClubsForm, DirectorForm
from datetime import datetime
from django.contrib.admin.models import LogEntry


# Create your views here.

def index(request):
    user = request.user
    if user.is_authenticated:
        if user.userprofile.account_type == '1':
                    
            userprofile = UserProfile.objects.filter(account_type='2')
            clubs = ClubsModel.objects.all()
            directors = DirectorProfile.objects.all()

            return render(request, 'admin_dashboard/index.html', {'userprofile':userprofile, 'clubs':clubs, 'directors':directors})
    return redirect('landingIndex')


def addClub(request):
    form = ClubsForm
    if request.method == 'POST':
        form = ClubsForm(request.POST)
        if form.is_valid():
            form.save()
    
    return render(request, 'admin_dashboard/Club/addClub.html', {'form':form})

def editClub(request, id):
    club = ClubsModel.objects.get(id=id)
    form = ClubsForm(instance=club)
    if request.method == 'POST':
        form = ClubsForm(request.POST, instance=club)
        if form.is_valid():
            form.save()

    return render(request, 'admin_dashboard/Club/editClub.html', {'form':form})

def viewClub(request):
    clubs = ClubsModel.objects.all()
    return render(request, 'admin_dashboard/Club/viewClub.html', {'clubs':clubs})


def deleteClub(request, id):
    club = ClubsModel.objects.get(id=id)
    club.delete()
    return redirect('viewClub')

def addDirector(request):
    clubs = ClubsModel.objects.all()
    if request.method == 'POST':
        username = request.POST.get('username')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        club = request.POST.get('club')


        director = DirectorProfile.objects.create(full_name=full_name, phone=phone, club=ClubsModel.objects.get(id=club))
        director.save()

        user = User.objects.create(username=username, email=email)
        user.set_password(password)
        user.save()

        userprofile = UserProfile.objects.create(user=user, account_type='2', director_profile=director)
        userprofile.save()
    return render(request, 'admin_dashboard/Director/addDirector.html', {'clubs':clubs})


def editDirector(request, id):
    clubs = ClubsModel.objects.all()

    if request.method == 'POST':
        userprofile = UserProfile.objects.get(id=id)

        username = request.POST.get('username')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        club = request.POST.get('club')

        director = DirectorProfile.objects.get(id=userprofile.director_profile.id)
        director.full_name = full_name
        director.phone=phone
        director.club = ClubsModel.objects.get(id=club)

        user = User.objects.get(id=userprofile.user.id)
        user.username = username
        user.email = email

        if password:
            user.set_password(password)

        
        director.save()
        user.save()


    userprofile = UserProfile.objects.get(id=id)
    username = userprofile.user.username
    full_name = userprofile.director_profile.full_name
    email = userprofile.user.email
    phone = userprofile.director_profile.phone
    club = userprofile.director_profile.club

    obj = {'username':username, 'full_name':full_name, 'email':email, 'phone':phone, 'club':club, 'clubs':clubs}

    return render(request, 'admin_dashboard/Director/editDirector.html', obj)

def viewDirector(request):
    date_time_now = datetime.now()
    directors = UserProfile.objects.filter(account_type='2')
    this_month_directors = directors.filter(creation_date__year=date_time_now.year, creation_date__month=date_time_now.month)
    Clubs = ClubsModel.objects.all()
    Directors = DirectorProfile.objects.all()

    clubs_have_Director = 0
    for i in Clubs:
        if Directors.filter(club=i).exists():clubs_have_Director+=1
        break

    return render(request, 'admin_dashboard/Director/viewDirector.html', {'directors':directors, 'this_month_directors':this_month_directors, 'clubs_have_Director':clubs_have_Director})

def deleteDirector(request, id):
    userprofile = UserProfile.objects.get(id=id)
    user = User.objects.get(id=userprofile.user.id)
    director = DirectorProfile.objects.get(id=userprofile.director_profile.id)

    director.delete()
    user.delete()

    return redirect('viewDirector')