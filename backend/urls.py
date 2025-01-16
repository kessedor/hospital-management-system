from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Custom error handlers
handler403 = 'core.views.handler403'
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),
    
    # Home app
    path('', include('home.urls')),
    
    # App URLs
    path('core/', include('core.urls')),
    path('authentication/', include('authentication.urls', namespace='authentication')),  # Added namespace
    path('patient/', include('patient_management.urls', namespace='patient_management')),
    
    # Media files in development
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Debug toolbar (only in development)
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include('debug_toolbar.urls')),
        ]
    except ImportError:
        pass