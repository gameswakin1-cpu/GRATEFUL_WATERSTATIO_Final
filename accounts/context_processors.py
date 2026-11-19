from django.conf import settings


def map_api_keys(request):
    return {
        'mapbox_api_key': getattr(settings, 'MAPBOX_API_KEY', ''),
        'carto_api_key': getattr(settings, 'CARTO_API_KEY', ''),
    }
