from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import IntegrityError, transaction
from .models import Profile

# Create your views here.
def Welcome(request):
    return render(request, 'Welcome.html')

def _signup_form_context(request):
    return {
        'form_username': request.POST.get('username', '').strip(),
        'form_email': request.POST.get('email', '').strip(),
        'form_state': request.POST.get('state', ''),
        'form_district': request.POST.get('district', ''),
        'form_role': request.POST.get('role', 'FARMER'),
    }

def Signup(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        role = request.POST.get('role', Profile.Roles.FARMER)
        state = request.POST.get('state', '').strip()
        district = request.POST.get('district', '').strip()
        context = _signup_form_context(request)

        if not username or not email or not password:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'Signup.html', context)

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'Signup.html', context)

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, "Username already taken. Try logging in instead.")
            return render(request, 'Signup.html', context)

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Email already registered. Try logging in instead.")
            return render(request, 'Signup.html', context)

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username, email=email, password=password
                )
                Profile.objects.create(
                    user=user, role=role, state=state, district=district
                )
        except IntegrityError:
            messages.error(request, "Username already taken. Try logging in instead.")
            return render(request, 'Signup.html', context)

        messages.success(request, "Account Created Successfully. Please log in.")
        return redirect('Login')

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