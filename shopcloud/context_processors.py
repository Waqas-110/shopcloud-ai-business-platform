from .language_utils import get_user_language

def language_context(request):
    """Add language context to all templates"""
    language = get_user_language(request)
    return {
        'current_language': language,
        'is_urdu': language == 'ur',
        'is_english': language == 'en'
    }