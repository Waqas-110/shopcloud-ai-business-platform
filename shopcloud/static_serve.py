from django.http import FileResponse, Http404
from django.conf import settings
import os

def serve_static(request, path):
    static_path = os.path.join(settings.BASE_DIR, 'static', path)
    if os.path.exists(static_path):
        return FileResponse(open(static_path, 'rb'))
    raise Http404()