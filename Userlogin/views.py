from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Profile

# Create your views here.
def Welcome(request):
    return render(request, 'Welcome.html')

def Signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        role = request.POST['role']  # Get the selected role

        if password != password2: 
            messages.error(request, "Passwords do not match.")
            return render(request, 'Signup.html')

        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'Signup.html')

        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'Signup.html')
        
        else:
            # 1. Create the User
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()

            # 2. Create the Profile with the selected role
            Profile.objects.create(user=user, role=role)

            messages.success(request, "Account Created Successfully. Please log in.")
            return redirect('Login')
    else:
        return render(request, 'Signup.html')

def Login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            user_role = user.profile.role
            
            if user_role == 'FARMER':
                return redirect('Farmer')
            elif user_role == 'RESEARCHER':
                return redirect('Dashboard')
            elif user_role == 'STAKEHOLDER':
                return redirect('Stakeholder')
            else:
                # Fallback for users with roles that don't match
                return redirect('Welcome')

        else:
            messages.error(request, "Invalid Credentials")
            return render(request, 'Login.html')
    else:
        return render(request, 'Login.html')
    
def Logout(request):
    logout(request)
    return redirect('Welcome')