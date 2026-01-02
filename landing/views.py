from django.shortcuts import render, redirect
from shopcloud.language_utils import get_user_language

def home(request):
    """Home page with language detection"""
    language = get_user_language(request)
    
    if language == 'en':
        return render(request, 'landing/home_en.html')
    else:
        return render(request, 'landing/home_ur.html')

def features(request):
    """Features page with language detection"""
    language = get_user_language(request)
    
    if language == 'en':
        return render(request, 'landing/features_en.html')
    else:
        return render(request, 'landing/features.html')