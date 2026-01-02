from django import template
from django.utils.translation import get_language

register = template.Library()

@register.simple_tag(takes_context=True)
def get_base_template(context):
    """Returns the appropriate base template based on current language"""
    lang = get_language()
    if lang == 'ur':
        return 'base_ur.html'
    elif lang == 'en':
        return 'base_en.html'
    return 'base.html'

@register.simple_tag
def lang_template(template_name, lang=None):
    """Returns language-specific template name"""
    if not lang:
        lang = get_language()
    
    if lang == 'ur':
        return template_name.replace('.html', '_ur.html')
    elif lang == 'en':
        return template_name.replace('.html', '_en.html')
    return template_name

@register.simple_tag(takes_context=True)
def select_template(context, base_name, **conditions):
    """Selects template based on multiple conditions"""
    template_name = base_name
    
    # Language-based selection
    if 'lang' in conditions or get_language() in ['ur', 'en']:
        lang = conditions.get('lang', get_language())
        if lang == 'ur':
            template_name = template_name.replace('.html', '_ur.html')
        elif lang == 'en':
            template_name = template_name.replace('.html', '_en.html')
    
    # Device-based selection
    if 'device' in conditions:
        device = conditions['device']
        template_name = template_name.replace('.html', f'_{device}.html')
    
    # User role-based selection
    if 'role' in conditions and hasattr(context.get('user'), 'role'):
        role = conditions['role']
        template_name = template_name.replace('.html', f'_{role}.html')
    
    return template_name