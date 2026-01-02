from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .models import Shop
from shopcloud.language_utils import get_user_language

def signup_view(request):
    # Get user language
    language = get_user_language(request)
    template_name = 'auth/signup_ur.html' if language == 'ur' else 'auth/signup.html'
    
    if request.method == 'POST':
        # Get and validate input data
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        # Validation checks
        errors = []
        
        if not username:
            errors.append('Username is required!' if language == 'en' else 'صارف نام درکار ہے!')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters long!' if language == 'en' else 'صارف نام کم از کم 3 حروف کا ہونا چاہیے!')
        
        if not email:
            errors.append('Email is required!' if language == 'en' else 'ای میل درکار ہے!')
        elif '@' not in email:
            errors.append('Please enter a valid email address!' if language == 'en' else 'براہ کرم درست ای میل پتہ درج کریں!')
        
        if not password:
            errors.append('Password is required!' if language == 'en' else 'پاس ورڈ درکار ہے!')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters long!' if language == 'en' else 'پاس ورڈ کم از کم 6 حروف کا ہونا چاہیے!')
        
        # Password confirmation check
        if password != confirm_password:
            errors.append('Passwords do not match!' if language == 'en' else 'پاس ورڈز میل نہیں کھاتے!')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, template_name)
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!' if language == 'en' else 'صارف نام پہلے سے موجود ہے!')
            return render(request, template_name)
            
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists!' if language == 'en' else 'ای میل پہلے سے موجود ہے!')
            return render(request, template_name)
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            messages.success(request, 'Account created successfully!' if language == 'en' else 'اکاؤنٹ کامیابی سے بنایا گیا!')
            return redirect('users:login')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}' if language == 'en' else f'اکاؤنٹ بنانے میں خرابی: {str(e)}')
            return render(request, template_name)
    
    return render(request, template_name)

def login_view(request):
    # Get user language
    language = get_user_language(request)
    template_name = 'auth/login_ur.html' if language == 'ur' else 'auth/login.html'
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        # Validation
        if not email or not password:
            messages.error(request, 'Please enter both email and password!' if language == 'en' else 'براہ کرم ای میل اور پاس ورڈ دونوں درج کریں!')
            return render(request, template_name)
        
        # Find user by email
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password!' if language == 'en' else 'غلط ای میل یا پاس ورڈ!')
            return render(request, template_name)
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Check if user is superuser/admin - redirect to admin panel
            if user.is_superuser:
                return redirect('users:admin_accounts')
            # Check if user has shop setup
            elif hasattr(user, 'shop'):
                return redirect('dashboard:main')
            else:
                return redirect('users:shop_setup')
        else:
            messages.error(request, 'Invalid email or password!' if language == 'en' else 'غلط ای میل یا پاس ورڈ!')
    
    return render(request, template_name)

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('landing:home')

@login_required
def shop_setup_view(request):
    if hasattr(request.user, 'shop'):
        return redirect('dashboard:main')
    
    # Get user language
    language = get_user_language(request)
    template_name = 'auth/shop_setup_ur.html' if language == 'ur' else 'auth/shop_setup.html'
    
    if request.method == 'POST':
        shop_name = request.POST.get('shop_name', '').strip()
        address = request.POST.get('address', '').strip()
        whatsapp = request.POST.get('whatsapp', '').strip()
        email = request.POST.get('email', '').strip()
        logo = request.FILES.get('logo')
        
        # Validation
        errors = []
        if not shop_name:
            errors.append('Shop name is required!' if language == 'en' else 'شاپ کا نام درکار ہے!')
        if not address:
            errors.append('Address is required!' if language == 'en' else 'پتہ درکار ہے!')
        if not whatsapp:
            errors.append('WhatsApp number is required!' if language == 'en' else 'واٹس ایپ نمبر درکار ہے!')
        elif len(whatsapp) < 10:
            errors.append('Please enter a valid WhatsApp number!' if language == 'en' else 'براہ کرم درست واٹس ایپ نمبر درج کریں!')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, template_name)
        
        try:
            Shop.objects.create(
                name=shop_name,
                address=address,
                whatsapp=whatsapp,
                email=email,
                logo=logo,
                owner=request.user
            )
            messages.success(request, 'Shop setup completed!' if language == 'en' else 'شاپ سیٹ اپ مکمل ہو گیا!')
            return redirect('dashboard:main')
        except Exception as e:
            messages.error(request, f'Error setting up shop: {str(e)}' if language == 'en' else f'شاپ سیٹ اپ میں خرابی: {str(e)}')
            return render(request, template_name)
    
    return render(request, template_name)

@login_required
def profile_view(request):
    try:
        shop = request.user.shop
    except Shop.DoesNotExist:
        messages.error(request, 'Shop not found. Please set up your shop first.')
        return redirect('users:shop_setup')
    
    if request.method == 'POST':
        # Get and validate input
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        shop_name = request.POST.get('shop_name', '').strip()
        address = request.POST.get('address', '').strip()
        whatsapp = request.POST.get('whatsapp', '').strip()
        shop_email = request.POST.get('shop_email', '').strip()
        
        # Validation
        errors = []
        if not email or '@' not in email:
            errors.append('Please enter a valid email address!')
        if not shop_name:
            errors.append('Shop name is required!')
        if not address:
            errors.append('Address is required!')
        if not whatsapp:
            errors.append('WhatsApp number is required!')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # Update user info
                request.user.first_name = first_name
                request.user.last_name = last_name
                request.user.email = email
                request.user.save()
                
                # Update shop info
                shop.name = shop_name
                shop.address = address
                shop.whatsapp = whatsapp
                shop.email = shop_email
                shop.save()
                
                messages.success(request, 'Profile updated successfully!')
            except Exception as e:
                messages.error(request, f'Error updating profile: {str(e)}')
        
        return redirect('users:profile')
    
    context = {
        'user': request.user,
        'shop': shop
    }
    return render(request, 'auth/profile.html', context)

def forgot_password_view(request):
    language = get_user_language(request)
    template_name = 'auth/forgot_password_ur.html' if language == 'ur' else 'auth/forgot_password.html'
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email or '@' not in email:
            messages.error(request, 'Please enter a valid email address!' if language == 'en' else 'براہ کرم درست ای میل پتہ درج کریں!')
            return render(request, template_name)
        
        try:
            user = User.objects.get(email=email)
            # TODO: Implement actual password reset email sending
            # For now, just show success message
            messages.success(request, 'Password reset instructions sent to your email!' if language == 'en' else 'پاس ورڈ ری سیٹ کی ہدایات آپ کے ای میل پر بھیج دی گئی ہیں!')
            return redirect('users:login')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address!' if language == 'en' else 'اس ای میل پتے سے کوئی اکاؤنٹ نہیں ملا!')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}' if language == 'en' else f'ایک خرابی پیش آئی: {str(e)}')
    
    return render(request, template_name)

@login_required
def admin_accounts_management(request):
    """Admin page to manage all user accounts"""
    # Check if user is superuser/admin
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard:main')
    
    # Get all users
    users = User.objects.all().order_by('-date_joined')
    
    # Calculate stats
    total_users = User.objects.count()
    active_shops = Shop.objects.count()
    from datetime import timedelta
    from django.utils import timezone
    recent_users = User.objects.filter(date_joined__gte=timezone.now() - timedelta(days=7)).count()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'change_password':
            user_id = request.POST.get('user_id')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_new_password')
            
            try:
                user = User.objects.get(id=user_id)
                
                if not new_password:
                    messages.error(request, 'Password cannot be empty!')
                elif len(new_password) < 6:
                    messages.error(request, 'Password must be at least 6 characters!')
                elif new_password != confirm_password:
                    messages.error(request, 'Passwords do not match!')
                else:
                    user.set_password(new_password)
                    user.save()
                    messages.success(request, f'Password changed successfully for {user.username}!')
            except User.DoesNotExist:
                messages.error(request, 'User not found!')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        
        elif action == 'delete_user':
            user_id = request.POST.get('user_id')
            try:
                user = User.objects.get(id=user_id)
                if user.is_superuser:
                    messages.error(request, 'Cannot delete superuser account!')
                else:
                    username = user.username
                    user.delete()
                    messages.success(request, f'User {username} deleted successfully!')
            except User.DoesNotExist:
                messages.error(request, 'User not found!')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        
        return redirect('users:admin_accounts')
    
    context = {
        'users': users,
        'total_users': total_users,
        'active_shops': active_shops,
        'recent_users': recent_users,
    }
    return render(request, 'admin/accounts_management.html', context)