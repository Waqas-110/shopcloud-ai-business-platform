from django.shortcuts import redirect
from django.http import JsonResponse
from .language_utils import set_user_language, get_user_language

def switch_language(request):
    """Switch user language"""
    language = request.GET.get('lang', 'ur')
    if language in ['en', 'ur']:
        set_user_language(request, language)
    
    # Redirect back to the same page where language was changed
    # First check if 'next' parameter is provided
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    
    # Otherwise use HTTP_REFERER
    referer = request.META.get('HTTP_REFERER')
    if referer:
        # Remove language parameter from referer if present
        if 'switch-language' in referer:
            # If coming from language switcher, go to home
            return redirect('landing:home')
        return redirect(referer)
    else:
        # Fallback to home if no referer
        return redirect('landing:home')