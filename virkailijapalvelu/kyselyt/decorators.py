
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie
from django_ratelimit.decorators import ratelimit


RATELIMIT_DECORATORS = [
    ratelimit(key="ip", rate=f"{settings.TOKEN_RATELIMIT_PER_MINUTE}/m", block=True),
    ratelimit(key="ip", rate=f"{settings.TOKEN_RATELIMIT_PER_HOUR}/h", block=True)]

CSRF_DECORATORS = [ensure_csrf_cookie] if settings.CSRF_FORCE_ENABLED else []
