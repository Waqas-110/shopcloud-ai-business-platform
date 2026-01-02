def get_user_language(request):
    """Get user's preferred language from session or default to Urdu"""
    return request.session.get('language', 'ur')

def set_user_language(request, language):
    """Set user's preferred language in session"""
    request.session['language'] = language

def get_template_name(base_template, language):
    """Get template name based on language"""
    if language == 'ur':
        return base_template.replace('.html', '_ur.html')
    # For English or default, use the base template without suffix
    return base_template