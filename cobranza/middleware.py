from django.core.cache import cache
from django.utils import timezone

class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if hasattr(request, 'user') and request.user.is_authenticated:
            cache.set(f'seen_{request.user.username}', timezone.now(), 600)
        return response
